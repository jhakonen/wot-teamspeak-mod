# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

AVAILABLE_PLUGIN_VERSION = 1

try:
	import game
	from tessumod.utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	from tessumod.ts3 import TS3Client
	from tessumod import utils, mytsplugin, notifications
	from tessumod.settings import settings
	from tessumod.user_cache import UserCache
	from tessumod.keyvaluestorage import KeyValueStorage
	import tessumod.positional_audio as positional_audio
	import BigWorld
	from VOIP.VOIPManager import VOIPManager
	import BattleReplay
	from messenger.proto.events import g_messengerEvents
	from PlayerEvents import g_playerEvents
	import os
	import subprocess
	import threading
	from functools import partial
except:
	import traceback
	print traceback.format_exc()

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''
	try:
		global g_ts, g_talk_states, g_minimap_ctrl, g_user_cache, g_positional_audio, g_keyvaluestorage
		global g_authentication_error

		g_authentication_error = False

		# make sure that ini-folder exists
		try:
			os.makedirs(utils.get_ini_dir_path())
		except os.error:
			pass
		settings_ini_path     = os.path.join(utils.get_ini_dir_path(), "tessu_mod.ini")
		old_settings_ini_path = os.path.join(utils.get_old_ini_dir_path(), "tessu_mod.ini")
		cache_ini_path        = os.path.join(utils.get_ini_dir_path(), "tessu_mod_cache.ini")
		# when updating from mod version 0.3.x to 0.4 (or newer) the ini-file needs
		# to be copied to the new location
		if os.path.isfile(old_settings_ini_path) and not os.path.isfile(settings_ini_path):
			os.rename(old_settings_ini_path, settings_ini_path)

		# do all intializations here
		settings(settings_ini_path).on_reloaded += load_settings
		g_user_cache = UserCache(cache_ini_path)
		g_user_cache.on_read_error += on_user_cache_read_error
		g_user_cache.init()

		g_talk_states = {}
		g_minimap_ctrl = utils.MinimapMarkersController()
		g_ts = TS3Client()

		g_positional_audio = positional_audio.PositionalAudio(
			ts_users      = g_ts.users_in_my_channel,
			user_cache    = g_user_cache
		)

		load_settings()

		g_ts.set_apikey(settings().get_client_query_apikey())
		g_ts.connect()
		g_ts.on_connected += on_connected_to_ts3
		g_ts.on_disconnected += on_disconnected_from_ts3
		g_ts.on_connected_to_server += on_connected_to_ts3_server
		g_ts.on_disconnected_from_server += on_disconnected_from_ts3_server
		g_ts.on_authenticate_error += on_ts3_authenticate_error
		g_ts.users_in_my_channel.on_added += on_ts3_user_in_my_channel_added
		g_ts.users_in_my_channel.on_modified += on_ts3_user_in_my_channel_modified
		utils.call_in_loop(settings().get_client_query_interval(), g_ts.check_events)

		g_playerEvents.onAvatarReady           += g_positional_audio.enable
		g_playerEvents.onAvatarBecomeNonPlayer += g_positional_audio.disable

		# don't show system center notifications in battle
		g_playerEvents.onAvatarBecomePlayer    += partial(notifications.set_notifications_enabled, False)
		g_playerEvents.onAvatarBecomeNonPlayer += partial(notifications.set_notifications_enabled, True)

		g_playerEvents.onAvatarBecomePlayer    += update_wot_nickname_to_ts
		g_playerEvents.onAccountBecomePlayer   += update_wot_nickname_to_ts

		# if nothing broke so far then it should be safe to patch the needed
		# functions (modified functions have dependencies to g_* global variables)
		VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIPManager.isParticipantTalking)
		BattleReplay.BattleReplay.play = BattleReplay_play(BattleReplay.BattleReplay.play)

		g_messengerEvents.users.onUsersListReceived += on_users_list_received

		notifications.add_event_handler(notifications.TSPLUGIN_INSTALL, on_tsplugin_install)
		notifications.add_event_handler(notifications.TSPLUGIN_IGNORED, on_tsplugin_ignore_toggled)
		notifications.add_event_handler(notifications.TSPLUGIN_MOREINFO, on_tsplugin_moreinfo_clicked)
		notifications.add_event_handler(notifications.SETTINGS_PATH, on_settings_path_clicked)

		g_keyvaluestorage = KeyValueStorage(utils.get_states_dir_path())

		utils.call_in_loop(settings().get_ini_check_interval, sync_configs)
		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())

	except:
		LOG_CURRENT_EXCEPTION()

def on_speak_status_changed(user):
	'''Called when TeamSpeak user's speak status changes.'''
	g_user_cache.add_ts_user(user.nick, user.unique_id)

	player = utils.ts_user_to_player(user,
		use_metadata = settings().get_wot_nick_from_ts_metadata(),
		use_ts_nick_search = settings().is_ts_nick_search_enabled(),
		extract_patterns = settings().get_nick_extract_patterns(),
		mappings = settings().get_name_mappings(),
		players = utils.get_players(in_battle=True, in_prebattle=True)
	)

	if player:
		g_user_cache.add_player(player.name, player.id)
		g_user_cache.pair(player_id=player.id, ts_user_id=user.unique_id)

	for player_id in g_user_cache.get_paired_player_ids(user.unique_id):
		talk_status(player_id, user.speaking)
		if user.speaking:
			# set speaking state immediately
			update_player_speak_status(player_id)
		else:
			# keep speaking state for a little longer
			BigWorld.callback(settings().get_speak_stop_delay(), utils.with_args(update_player_speak_status, player_id))

def talk_status(player_id, talking=None):
	if talking is not None:
		g_talk_states[player_id] = talking
	try:
		return g_talk_states[player_id]
	except:
		return False

def update_player_speak_status(player_id):
	'''Updates given 'player_id's talking status to VOIP system and minimap.'''
	try:
		talking = is_voice_chat_speak_allowed(player_id) and talk_status(player_id)
		g_messengerEvents.voip.onPlayerSpeaking(player_id, talking)
	except:
		LOG_CURRENT_EXCEPTION()

	try:
		info = utils.get_player_info_by_dbid(player_id)
		talking = (
			talk_status(player_id) and
			is_minimap_speak_allowed(player_id) and
			utils.get_vehicle(info["vehicle_id"])["isAlive"]
		)
		if talking:
			g_minimap_ctrl.start(info["vehicle_id"], settings().get_minimap_action(), settings().get_minimap_action_interval())
		else:
			g_minimap_ctrl.stop(info["vehicle_id"])
	except KeyError:
		# not an error, occurs in garage where there are no vehicles and
		# such no "vehicle_id"
		pass
	except:
		LOG_CURRENT_EXCEPTION()

def is_voice_chat_speak_allowed(player_id):
	if not settings().is_voice_chat_notifications_enabled():
		return False
	if not settings().is_self_voice_chat_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def is_minimap_speak_allowed(player_id):
	if not settings().is_minimap_notifications_enabled():
		return False
	if not settings().is_self_minimap_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def clear_speak_statuses():
	'''Clears speak status of all players.'''
	players_speaking = [id for id in g_talk_states if g_talk_states[id]]
	g_talk_states.clear()
	g_minimap_ctrl.stop_all()

	for id in players_speaking:
		try:
			g_messengerEvents.voip.onPlayerSpeaking(id, False)
		except:
			pass

def on_connected_to_ts3():
	'''Called when TessuMod manages to connect TeamSpeak client. However, this
	doesn't mean that the client is connected to any TeamSpeak server.
	'''
	LOG_NOTE("Connected to TeamSpeak client")

	global g_authentication_error
	if g_authentication_error:
		notifications.push_warning_message("Permission granted, connected to TeamSpeak client")
	g_authentication_error = False

	installer_path = utils.get_plugin_installer_path()

	# plugin doesn't work in WinXP so check that we are running on
	# sufficiently recent Windows OS
	if not is_vista_or_newer():
		return
	if not os.path.isfile(installer_path):
		return
	if is_newest_plugin_version(get_installed_plugin_version()):
		return
	if is_newest_plugin_version(get_ignored_plugin_version()):
		return

	notifications.push_ts_plugin_install_message(
		moreinfo_url   = "https://github.com/jhakonen/wot-teamspeak-mod/wiki/TeamSpeak-Plugins#tessumod-plugin",
		ignore_state   = "off"
	)

def is_vista_or_newer():
	'''Returns True if the game is running on Windows Vista or newer OS.'''
	try:
		import sys
		return sys.getwindowsversion()[0] >= 6
	except:
		LOG_ERROR("Failed to get current Windows OS version")
		return True

def get_installed_plugin_version():
	with mytsplugin.InfoAPI() as api:
		return api.get_api_version()

def is_newest_plugin_version(plugin_version):
	return plugin_version >= AVAILABLE_PLUGIN_VERSION

def get_ignored_plugin_version():
	if "ignored_plugin_version" in g_keyvaluestorage:
		return int(g_keyvaluestorage["ignored_plugin_version"])
	return 0

def set_plugin_install_ignored(ignored):
	g_keyvaluestorage["ignored_plugin_version"] = AVAILABLE_PLUGIN_VERSION if ignored else 0

def on_disconnected_from_ts3():
	'''Called when TessuMod loses connection to TeamSpeak client.'''
	LOG_NOTE("Disconnected from TeamSpeak client")
	clear_speak_statuses()
	notifications.push_warning_message("Disconnected from TeamSpeak client")

def on_connected_to_ts3_server(server_name):
	LOG_NOTE("Connected to TeamSpeak server '{0}'".format(server_name))
	notifications.push_info_message("Connected to TeamSpeak server '{0}'".format(server_name))
	update_wot_nickname_to_ts()

def on_disconnected_from_ts3_server():
	LOG_NOTE("Disconnected from TeamSpeak server")
	clear_speak_statuses()

def on_ts3_authenticate_error():
	'''Called when ClientQuery protocol tries to authenticate but the required
	API key is either not set or is wrong.
	'''
	global g_authentication_error
	if g_authentication_error:
		return
	g_authentication_error = True
	LOG_NOTE("Failed to authenticate to TeamSpeak client")
	settings_link = "<a href=\"event:{0}\">{1}</a>".format(notifications.SETTINGS_PATH, os.path.abspath(settings().get_filepath()))
	notifications.push_warning_message("TessuMod needs permission to access your TeamSpeak client.\n\n"
		+ "Plese enter ClientQuery API key (see TeamSpeak -> Tools -> Options -> Addons -> Plugins -> ClientQuery -> Settings) "
		+ "to option <b>api_key</b> within section <b>[TSClientQueryService]</b> in TessuMod's settings file ({0}).\n\n".format(settings_link)
		+ "<b>NOTE:</b> If your current settings file doesn't have this option, you can add it there yourself. "
		+ "Alternatively you can delete the file and restart World of Tanks. "
		+ "TessuMod will generate a new file on game start which will include the option.")

def on_ts3_user_in_my_channel_added(client_id):
	on_speak_status_changed(g_ts.users[client_id])

def on_ts3_user_in_my_channel_modified(client_id):
	on_speak_status_changed(g_ts.users[client_id])

def on_user_cache_read_error(message):
	'''This function is called if user cache's reading fails.'''
	notifications.push_error_message("Failed to read file '{0}':\n   {1}"
		.format(g_user_cache.ini_path, message))

def load_settings():
	LOG_NOTE("Settings loaded from ini file")
	utils.CURRENT_LOG_LEVEL = settings().get_log_level()
	g_ts.HOST = settings().get_client_query_host()
	g_ts.PORT = settings().get_client_query_port()
	g_ts.set_apikey(settings().get_client_query_apikey())

def sync_configs():
	g_user_cache.sync()
	settings().sync()

def update_wot_nickname_to_ts():
	g_ts.set_wot_nickname(utils.get_my_name())

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		'''Called by other game modules (but not by minimap) to determine
		current speaking status.
		'''
		try:
			return is_voice_chat_speak_allowed(dbid) and talk_status(dbid)
		except:
			LOG_CURRENT_EXCEPTION()
		return orig_method(self, dbid)
	return wrapper

def BattleReplay_play(orig_method):
	def wrapper(*args, **kwargs):
		'''Called when replay is starting.
		Prevents user cache from getting polluted by incorrect pairings; If user
		plays someone else's replay and user's TS ID would get matched with the
		replay's player name.
		'''
		g_user_cache.is_write_enabled = settings().should_update_cache_in_replays()
		return orig_method(*args, **kwargs)
	return wrapper

def on_users_list_received(tags):
	'''This function populates user cache with friends and clan members from
	user storage when user list is received at start when player logs in to
	the game.
	Users storage should be available and populated by now.
	'''
	for player in utils.get_players(clanmembers=True, friends=True):
		g_user_cache.add_player(player.name, player.id)

def on_tsplugin_install(type_id, msg_id, data):
	threading.Thread(
		target = partial(
			subprocess.call,
			args  = [os.path.normpath(utils.get_plugin_installer_path())],
			shell = True
		)
	).start()

def on_tsplugin_ignore_toggled(type_id, msg_id, data):
	data["ignore_state"] = "on" if data["ignore_state"] == "off" else "off"
	set_plugin_install_ignored(True if data["ignore_state"] == "on" else False)
	notifications.update_message(type_id, msg_id, data)

def on_tsplugin_moreinfo_clicked(type_id, msg_id, data):
	subprocess.call(["start", data["moreinfo_url"]], shell=True)

def on_settings_path_clicked(type_id, msg_id, data):
	subprocess.call(["start", os.path.abspath(settings().get_filepath())], shell=True)
