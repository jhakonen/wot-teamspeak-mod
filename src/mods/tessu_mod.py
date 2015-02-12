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
		VOIP.getVOIPManager().onPlayerSpeaking(player_id, talking)
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
			VOIP.getVOIPManager().onPlayerSpeaking(id, False)
		except:
			pass

def on_connected_to_ts3():
	'''Called when TessuMod manages to connect TeamSpeak client. However, this
	doesn't mean that the client is connected to any TeamSpeak server.
	'''
	LOG_NOTE("Connected to TeamSpeak client")
	utils.push_system_message("Connected to TeamSpeak client", SystemMessages.SM_TYPE.Information)

def on_disconnected_from_ts3():
	'''Called when TessuMod loses connection to TeamSpeak client.'''
	LOG_NOTE("Disconnected from TeamSpeak client")
	clear_speak_statuses()
	utils.push_system_message("Disconnected from TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_connected_to_ts3_server(server_name):
	LOG_NOTE("Connected to TeamSpeak server '{0}'".format(server_name))
	utils.push_system_message("Connected to TeamSpeak server '{0}'".format(server_name), SystemMessages.SM_TYPE.Information)
	g_ts.set_wot_nickname(utils.get_my_name())

def on_disconnected_from_ts3_server():
	LOG_NOTE("Disconnected from TeamSpeak server")
	clear_speak_statuses()

def on_ts3_user_in_my_channel_added(client_id):
	'''This function populates user cache with TeamSpeak users whenever they
	enter our TeamSpeak channel.
	'''
	user = g_ts.users[client_id]
	g_user_cache.add_ts_user(user.nick, user.unique_id)

def on_user_cache_read_error(message):
	'''This function is called if user cache's reading fails.'''
	utils.push_system_message("Failed to read file '{0}':\n   {1}"
		.format(g_user_cache.ini_path, message), SystemMessages.SM_TYPE.Error)

def load_settings():
	LOG_NOTE("Settings loaded from ini file")
	utils.CURRENT_LOG_LEVEL = settings().get_log_level()
	g_ts.HOST = settings().get_client_query_host()
	g_ts.PORT = settings().get_client_query_port()

def sync_configs():
	g_user_cache.sync()
	settings().sync()

def Player_onBecomePlayer(orig_method):
	def wrapper(self):
		'''Called when BigWorld.player() is available.'''
		orig_method(self)
		g_ts.set_wot_nickname(utils.get_my_name())
	return wrapper

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

def in_test_suite():
	import sys
	return "behave" in sys.argv[0]

def load_mod():
	global g_ts, g_talk_states, g_minimap_ctrl, g_user_cache

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

	load_settings()

	g_ts.connect()
	g_ts.on_connected += on_connected_to_ts3
	g_ts.on_disconnected += on_disconnected_from_ts3
	g_ts.on_connected_to_server += on_connected_to_ts3_server
	g_ts.on_disconnected_from_server += on_disconnected_from_ts3_server
	g_ts.on_speak_status_changed += on_speak_status_changed
	g_ts.users_in_my_channel.on_added += on_ts3_user_in_my_channel_added
	utils.call_in_loop(settings().get_client_query_interval(), g_ts.check_events)

	# if nothing broke so far then it should be safe to patch the needed
	# functions (modified functions have dependencies to g_* global variables)
	Avatar.Avatar.onBecomePlayer = Player_onBecomePlayer(Avatar.Avatar.onBecomePlayer)
	Account.PlayerAccount.onBecomePlayer = Player_onBecomePlayer(Account.PlayerAccount.onBecomePlayer)
	VOIP.VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIP.VOIPManager.isParticipantTalking)
	BattleReplay.BattleReplay.play = BattleReplay_play(BattleReplay.BattleReplay.play)

	g_messengerEvents.users.onUsersListReceived += on_users_list_received

	utils.call_in_loop(settings().get_ini_check_interval, sync_configs)

try:
	import game
	from tessu_utils.utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	from tessu_utils.ts3 import TS3Client
	from tessu_utils import utils
	from tessu_utils.settings import settings
	from tessu_utils.user_cache import UserCache
	import BigWorld
	import Avatar
	import Account
	import VOIP
	import BattleReplay
	from gui import SystemMessages
	from messenger.proto.events import g_messengerEvents
	import os

	if not in_test_suite():
		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())
		load_mod()
except:
	LOG_CURRENT_EXCEPTION()
