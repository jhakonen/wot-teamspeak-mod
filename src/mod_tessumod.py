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

PLUGIN_INFO_URL = "http://jhakonen.github.io/wot-teamspeak-mod/plugin_info.json"

try:
	import game
	from tessumod.utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	from tessumod.asyncore_utils import EventLoopAdapter
	from tessumod.http import HTTPClient
	from tessumod.ts3 import TS3Client
	from tessumod import utils, mytsplugin, notifications
	from tessumod.settings import Settings
	from tessumod.user_cache import UserCache
	from tessumod.keyvaluestorage import KeyValueStorage
	import tessumod.positional_audio as positional_audio
	import BigWorld
	import Event
	from VOIP.VOIPManager import VOIPManager
	import BattleReplay
	from messenger.proto.events import g_messengerEvents
	from PlayerEvents import g_playerEvents
	import json
	import os
	import re
	import subprocess
	import threading
	import time
	from functools import partial
	on_player_speaking = Event.Event()
except:
	import traceback
	print traceback.format_exc()

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''
	try:
		global g_ts, g_talk_states, g_minimap_ctrl, g_user_cache, g_positional_audio, g_keyvaluestorage
		global g_authentication_error, g_settings, g_settings_timer, g_ts_timer, g_http_client

		g_authentication_error = False
		utils.init()
		notifications.init()

		# make sure that ini-folder exists
		try:
			os.makedirs(utils.get_ini_dir_path())
			os.makedirs(os.path.join(utils.get_ini_dir_path(), "states"))
		except os.error:
			pass
		settings_ini_path     = os.path.join(utils.get_ini_dir_path(), "tessu_mod.ini")
		cache_ini_path        = os.path.join(utils.get_ini_dir_path(), "tessu_mod_cache.ini")

		# do all intializations here
		g_settings = Settings(settings_ini_path)
		g_settings.on_reloaded += load_settings
		g_user_cache = UserCache(cache_ini_path)
		g_user_cache.on_read_error += on_user_cache_read_error
		g_user_cache.init()

		event_loop = EventLoopAdapter()

		g_http_client = HTTPClient(event_loop)

		g_talk_states = {}
		g_minimap_ctrl = utils.MinimapMarkersController()
		g_ts = TS3Client(event_loop)

		g_positional_audio = positional_audio.PositionalAudio(
			ts_users      = g_ts.users_in_my_channel,
			user_cache    = g_user_cache
		)

		load_settings()

		event_loop.set_polling_interval(g_settings.get_client_query_interval())

		g_ts.set_apikey(g_settings.get_client_query_apikey())
		g_ts.connect()
		g_ts.on_connected += on_connected_to_ts3
		g_ts.on_disconnected += on_disconnected_from_ts3
		g_ts.on_connected_to_server += on_connected_to_ts3_server
		g_ts.on_disconnected_from_server += on_disconnected_from_ts3_server
		g_ts.on_authenticate_error += on_ts3_authenticate_error
		g_ts.users_in_my_channel.on_added += on_ts3_user_in_my_channel_added
		g_ts.users_in_my_channel.on_modified += on_ts3_user_in_my_channel_modified
		g_ts_timer = utils.call_in_loop(g_settings.get_client_query_interval(), g_ts.check_events)

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

		add_onPlayerSpeaking_filter(g_messengerEvents.voip.onPlayerSpeaking)

		notifications.add_event_handler(notifications.TSPLUGIN_INSTALL, on_tsplugin_install)
		notifications.add_event_handler(notifications.TSPLUGIN_IGNORED, on_tsplugin_ignore_toggled)
		notifications.add_event_handler(notifications.TSPLUGIN_MOREINFO, on_tsplugin_moreinfo_clicked)
		notifications.add_event_handler(notifications.SETTINGS_PATH, on_settings_path_clicked)

		g_keyvaluestorage = KeyValueStorage(utils.get_states_dir_path())

		g_settings_timer = utils.call_in_loop(g_settings.get_ini_check_interval(), sync_configs)
		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())

	except:
		LOG_CURRENT_EXCEPTION()

def fini():
	'''Mod's entry point. Called by WoT's built-in mod loader when the game
	is exiting. Main reason why this is done though is for fute test suite,
	allowing cleanup of the mod after each test.'''
	global g_ts, g_talk_states, g_minimap_ctrl, g_user_cache, g_positional_audio, g_keyvaluestorage
	global g_authentication_error, g_settings, g_settings_timer, g_ts_timer

	g_playerEvents.onAvatarReady           -= g_positional_audio.enable
	g_playerEvents.onAvatarBecomeNonPlayer -= g_positional_audio.disable

	remove_onPlayerSpeaking_filter(g_messengerEvents.voip.onPlayerSpeaking)

	g_authentication_error = None
	g_keyvaluestorage = None
	g_minimap_ctrl.fini()
	g_minimap_ctrl = None
	g_positional_audio.fini()
	g_positional_audio = None
	g_settings = None
	g_settings_timer.fini()
	g_settings_timer = None
	g_talk_states = None
	g_ts_timer.stop()
	g_ts_timer = None
	g_ts.fini()
	g_ts = None
	g_user_cache = None

	utils.fini()

def on_speak_status_changed(user):
	'''Called when TeamSpeak user's speak status changes.'''
	g_user_cache.add_ts_user(user.nick, user.unique_id)

	player = utils.ts_user_to_player(user,
		use_metadata = g_settings.get_wot_nick_from_ts_metadata(),
		use_ts_nick_search = g_settings.is_ts_nick_search_enabled(),
		extract_patterns = g_settings.get_nick_extract_patterns(),
		mappings = g_settings.get_name_mappings(),
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
			BigWorld.callback(g_settings.get_speak_stop_delay(), utils.with_args(update_player_speak_status, player_id))

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
		talking = talk_status(player_id)
		on_player_speaking(player_id, talking)
		g_messengerEvents.voip.onPlayerSpeaking.unfiltered_call(player_id, talking and is_voice_chat_speak_allowed(player_id))
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
			g_minimap_ctrl.start(info["vehicle_id"], g_settings.get_minimap_action(), g_settings.get_minimap_action_interval())
		else:
			g_minimap_ctrl.stop(info["vehicle_id"])
	except KeyError:
		# not an error, occurs in garage where there are no vehicles and
		# such no "vehicle_id"
		pass
	except:
		LOG_CURRENT_EXCEPTION()

def is_voice_chat_speak_allowed(player_id):
	if not g_settings.is_voice_chat_notifications_enabled():
		return False
	if not g_settings.is_self_voice_chat_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def is_minimap_speak_allowed(player_id):
	if not g_settings.is_minimap_notifications_enabled():
		return False
	if not g_settings.is_self_minimap_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def clear_speak_statuses():
	'''Clears speak status of all players.'''
	players_speaking = [id for id in g_talk_states if g_talk_states[id]]
	g_talk_states.clear()
	g_minimap_ctrl.stop_all()

	for id in players_speaking:
		try:
			g_messengerEvents.voip.onPlayerSpeaking.unfiltered_call(id, False)
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
	has_cached_plugin_info = \
		"plugin_info" in g_keyvaluestorage and \
		"plugin_info_timestamp" in g_keyvaluestorage and \
		abs(time.time() - g_keyvaluestorage["plugin_info_timestamp"]) < 60 * 60 * 24 * 7
	if has_cached_plugin_info:
		handle_plugin_info(g_keyvaluestorage["plugin_info"])
	else:
		def on_plugin_info_received(error, result):
			if error:
				LOG_ERROR(error)
				return
			plugin_info = json.loads(result.body)
			g_keyvaluestorage["plugin_info"] = plugin_info
			g_keyvaluestorage["plugin_info_timestamp"] = time.time()
			handle_plugin_info(plugin_info)
		g_http_client.get(PLUGIN_INFO_URL, on_plugin_info_received)

def handle_plugin_info(plugin_info):
	info = get_plugin_advertisement_info(dict(
		plugin_info = plugin_info,
		mod_version = utils.get_mod_version(),
		installed_plugin_version = get_installed_plugin_version(),
		ignored_plugin_versions = get_ignored_plugin_versions()
	))
	if not info:
		return
	if info["offer_type"] == "install":
		notifications.push_ts_plugin_install_message(
			moreinfo_url = "https://github.com/jhakonen/wot-teamspeak-mod/wiki/TeamSpeak-Plugins#tessumod-plugin",
			ignore_state = "off",
			plugin_version = info["plugin_version"]
		)

def get_installed_plugin_version():
	with mytsplugin.InfoAPI() as api:
		return api.get_api_version()

def get_ignored_plugin_versions():
	if "ignored_plugin_versions" in g_keyvaluestorage:
		return g_keyvaluestorage["ignored_plugin_versions"]
	elif "ignored_plugin_version" in g_keyvaluestorage:
		# Deprecated state variable (from 0.6.x versions)
		return [int(g_keyvaluestorage["ignored_plugin_version"])]
	return []

def get_plugin_advertisement_info(input):
	mod_version = parse_version(input["mod_version"], parts_required=3)

	installed_plugin_version = input["installed_plugin_version"]
	assert type(installed_plugin_version) is int

	ignored_plugin_versions = input["ignored_plugin_versions"]
	assert type(ignored_plugin_versions) is list
	for version in ignored_plugin_versions:
		assert type(version) is int
		assert version != 0

	version_entries = input["plugin_info"]["versions"]
	assert type(version_entries) is list
	for entry in version_entries:
		assert type(entry["plugin_version"]) is int
		assert type(entry["supported_mod_versions"]) is list
		assert len(entry["supported_mod_versions"]) < 3
		if "download_url" in entry:
			assert type(entry["download_url"]) in (str, unicode)
			assert entry["download_url"]

	supported_entries = get_supported_version_entries(mod_version, version_entries)
	new_available_entries = get_new_version_entries(installed_plugin_version, supported_entries)
	new_available_entries = get_not_ignored_version_entries(ignored_plugin_versions, new_available_entries)
	new_available_entries = get_downloadable_version_entries(new_available_entries)

	if new_available_entries:
		entry = new_available_entries[-1]
		return {
			"offer_type": "install" if installed_plugin_version == 0 else "update",
			"download_url": entry["download_url"],
			"plugin_version": entry["plugin_version"]
		}
	else:
		if installed_plugin_version != 0:
			if not supported_entries:
				return { "offer_type": "unsupported_mod" }
			matching_entries = [e for e in version_entries if e["plugin_version"] == installed_plugin_version]
			if not get_supported_version_entries(mod_version, matching_entries):
				return { "offer_type": "unsupported_plugin" }
		return None

def parse_version(version_str, parts_required=0):
	PART_REGEXP = re.compile("([0-9]+)")
	results = []
	parts = version_str.split(".")
	for part in parts:
		match = PART_REGEXP.match(part)
		if match:
			results.append(int(match.group(1)))
		else:
			break
	assert len(results) >= parts_required
	return results

def get_supported_version_entries(mod_version, entries):
	results = []
	for entry in entries:
		supported = entry["supported_mod_versions"]
		min_version = parse_version(supported[0], parts_required=1)
		max_version = parse_version(supported[1] if len(supported) == 2 else "999", parts_required=1)
		if version_in_range(mod_version, min_version, max_version):
			results.append(entry)
	return results

def version_in_range(value, min_value, max_value):
	if len(value) > 0 and len(min_value) > 0 and value[0] < min_value[0]:
		return False
	if len(value) > 1 and len(min_value) > 1 and value[1] < min_value[1]:
		return False
	if len(value) > 2 and len(min_value) > 2 and value[2] < min_value[2]:
		return False
	if len(value) > 0 and len(max_value) > 0 and value[0] > max_value[0]:
		return False
	if len(value) > 1 and len(max_value) > 1 and value[1] > max_value[1]:
		return False
	if len(value) > 2 and len(max_value) > 2 and value[2] > max_value[2]:
		return False
	return True

def get_new_version_entries(current_plugin_version, entries):
	return [entry for entry in entries if entry["plugin_version"] > current_plugin_version]

def get_not_ignored_version_entries(ignored_plugin_versions, entries):
	return [entry for entry in entries if entry["plugin_version"] not in ignored_plugin_versions]

def get_downloadable_version_entries(entries):
	return [entry for entry in entries if "download_url" in entry]

def set_plugin_install_ignored(plugin_version, ignored):
	ignored_state = g_keyvaluestorage.get("ignored_plugin_versions", [])
	if plugin_version in ignored_state and not ignored:
		ignored_state.remove(plugin_version)
	elif plugin_version not in ignored_state and ignored:
		ignored_state.append(plugin_version)
	g_keyvaluestorage["ignored_plugin_versions"] = ignored_state

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
	settings_link = "<a href=\"event:{0}\">{1}</a>".format(notifications.SETTINGS_PATH, os.path.abspath(g_settings.get_filepath()))
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
	utils.CURRENT_LOG_LEVEL = g_settings.get_log_level()
	g_ts.HOST = g_settings.get_client_query_host()
	g_ts.PORT = g_settings.get_client_query_port()
	g_ts.set_apikey(g_settings.get_client_query_apikey())

def sync_configs():
	g_user_cache.sync()
	g_settings.sync()

def update_wot_nickname_to_ts():
	g_ts.set_wot_nickname(utils.get_my_name())

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		'''Called by other game modules (but not by minimap) to determine
		current speaking status.
		'''
		talking = orig_method(self, dbid)
		try:
			talking = talking or has_speak_feedback(dbid)
		except:
			LOG_CURRENT_EXCEPTION()
		return talking
	return wrapper

def has_speak_feedback(dbid):
	return is_voice_chat_speak_allowed(dbid) and talk_status(dbid)

def BattleReplay_play(orig_method):
	def wrapper(*args, **kwargs):
		'''Called when replay is starting.
		Prevents user cache from getting polluted by incorrect pairings; If user
		plays someone else's replay and user's TS ID would get matched with the
		replay's player name.
		'''
		g_user_cache.is_write_enabled = g_settings.should_update_cache_in_replays()
		return orig_method(*args, **kwargs)
	return wrapper

def add_onPlayerSpeaking_filter(obj):
	class FilterEvent(type(obj)):
		def __call__(self, dbid, talking):
			if talking:
				self.unfiltered_call(dbid, talking)
			elif has_speak_feedback(dbid):
				pass
			else:
				self.unfiltered_call(dbid, talking)

		def unfiltered_call(self, *args, **kwargs):
			self.original_class.__call__(self, *args, **kwargs)

	obj.original_class = obj.__class__
	obj.__class__ = FilterEvent

def remove_onPlayerSpeaking_filter(obj):
	obj.__class__ = obj.original_class
	del obj.original_class

def on_users_list_received(tags):
	'''This function populates user cache with friends and clan members from
	user storage when user list is received at start when player logs in to
	the game.
	Users storage should be available and populated by now.
	'''
	for player in utils.get_players(clanmembers=True, friends=True):
		g_user_cache.add_player(player.name, player.id)

def on_tsplugin_install(type_id, msg_id, data):
	# For this to work under the TeamSpeak client probably would need to be
	# installed within the same prefix as the game is. File association for
	# .ts3_plugin missing otherwise?
	threading.Thread(
		target = partial(
			subprocess.call,
			args  = [os.path.normpath(utils.get_plugin_installer_path())],
			shell = True
		)
	).start()

def on_tsplugin_ignore_toggled(type_id, msg_id, data):
	data["ignore_state"] = "on" if data["ignore_state"] == "off" else "off"
	set_plugin_install_ignored(data["plugin_version"], True if data["ignore_state"] == "on" else False)
	notifications.update_message(type_id, msg_id, data)

def on_tsplugin_moreinfo_clicked(type_id, msg_id, data):
	# Using Popen here as opening the URL to a web browser using call() seems
	# to not work under WINE, and just freezes the game client. Browser opens
	# once you force close the client.
	subprocess.Popen(["start", data["moreinfo_url"]], shell=True)

def on_settings_path_clicked(type_id, msg_id, data):
	# Using call() for this under WINE works just fine, perplexing...
	subprocess.call(["start", os.path.abspath(g_settings.get_filepath())], shell=True)
