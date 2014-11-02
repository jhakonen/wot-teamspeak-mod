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
	if not settings().get_wot_nick_from_ts_metadata():
		user.wot_nick = ""
	player_name = user.wot_nick if user.wot_nick else map_nick_to_wot_nick(extract_nick(user.nick))
	talk_status(player_name, user.speaking)
	if user.speaking:
		# set speaking state immediately
		update_player_speak_status(player_name)
	else:
		# keep speaking state for a little longer
		BigWorld.callback(settings().get_speak_stop_delay(), utils.with_args(update_player_speak_status, player_name))

def extract_nick(ts_nickname):
	'''Extracts WOT nickname (or something that can be passed to mapping
	rules) from 'ts_nickname' using regexp patterns defined in ini-file's
	'nick_extract_patterns'-key.
	Returns 'ts_nickname' if none of the patterns matched.
	'''
	for pattern in settings().get_nick_extract_patterns():
		matches = pattern.match(ts_nickname)
		if matches is not None:
			LOG_DEBUG("TS nickname '{0}' matched to regexp pattern '{1}'".format(ts_nickname, pattern.pattern))
			return matches.group(1)
	return ts_nickname

def map_nick_to_wot_nick(ts_nickname):
	'''Returns 'ts_nickname's matching WOT nickname using values from
	ini-file's [NameMappings] section.
	Returns 'ts_nickname' if mapping didn't exist for it.
	'''
	mapping = settings().get_name_mappings()
	try:
		wot_nickname = mapping[ts_nickname.lower()]
		LOG_DEBUG("TS nickname '{0}' mapped to WOT nickname '{1}'".format(ts_nickname, wot_nickname))
		return wot_nickname
	except:
		return ts_nickname

def talk_status(player_name, talking=None):
	player_name = player_name.lower()
	if talking is not None:
		g_talk_states[player_name] = talking
	try:
		return g_talk_states[player_name]
	except:
		return False

def update_player_speak_status(player_name):
	'''Updates given 'player_name's talking status to VOIP system and minimap.''' 
	player_name = player_name.lower()
	info = utils.get_player_info_by_name(player_name)
	if not info:
		return
	try:
		talking = is_voice_chat_speak_allowed(player_name) and talk_status(player_name)
		VOIP.getVOIPManager().setPlayerTalking(info["dbid"], talking)
	except:
		LOG_CURRENT_EXCEPTION()
	try:
		talking = (
			talk_status(player_name) and
			is_minimap_speak_allowed(player_name) and
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

def is_voice_chat_speak_allowed(player_name):
	if not settings().is_voice_chat_notifications_enabled():
		return False
	if not settings().is_self_voice_chat_notifications_enabled() and utils.get_my_name().lower() == player_name.lower():
		return False
	return True

def is_minimap_speak_allowed(player_name):
	if not settings().is_minimap_notifications_enabled():
		return False
	if not settings().is_self_minimap_notifications_enabled() and utils.get_my_name().lower() == player_name.lower():
		return False
	return True

def clear_speak_statuses():
	'''Clears speak status of all players.'''
	players_speaking = [name for name in g_talk_states if g_talk_states[name]]
	g_talk_states.clear()
	g_minimap_ctrl.stop_all()

	for name in players_speaking:
		try:
			info = utils.get_player_info_by_name(name)
			VOIP.getVOIPManager().setPlayerTalking(info["dbid"], False)
		except:
			pass

def on_connected_to_ts3():
	'''Called when TessuMod manages to connect TeamSpeak client. However, this
	doesn't mean that the client is connected to any TeamSpeak server.
	'''
	LOG_NOTE("Connected to TeamSpeak client")
	utils.push_system_message("Connected to TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_disconnected_from_ts3():
	'''Called when TessuMod loses connection to TeamSpeak client.'''
	LOG_NOTE("Disconnected from TeamSpeak client")
	clear_speak_statuses()
	utils.push_system_message("Disconnected from TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_connected_to_ts3_server():
	LOG_NOTE("Connected to TeamSpeak server")
	g_ts.set_wot_nickname(utils.get_my_name())

def on_disconnected_from_ts3_server():
	LOG_NOTE("Disconnected from TeamSpeak server")
	clear_speak_statuses()

def on_ts3_user_in_my_channel_added(client_id):
	'''This function populates user cache with TeamSpeak users whenever they
	enter our TeamSpeak channel.
	'''
	g_user_cache.add_ts_user(g_ts.users[client_id])

def load_settings():
	LOG_NOTE("Settings loaded from ini file")
	utils.CURRENT_LOG_LEVEL = settings().get_log_level()
	g_ts.HOST = settings().get_client_query_host()
	g_ts.PORT = settings().get_client_query_port()
	g_user_cache.set_ini_check_interval(settings().get_ini_check_interval())

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
			player_name = utils.get_player_info_by_dbid(dbid)["player_name"]
			return is_voice_chat_speak_allowed(player_name) and talk_status(player_name)
		except:
			LOG_CURRENT_EXCEPTION()
		return orig_method(self, dbid)
	return wrapper

def on_users_rosters_received():
	'''This function populates user cache with friends and clan members from
	user storage when user rosters are received at start when player logs in to
	the game.
	Users storage should be available and populated by now.
	'''
	users_storage = storage_getter('users')()
	for friend in users_storage.getList(find_criteria.BWFriendFindCriteria()):
		g_user_cache.add_player(friend)
	for member in users_storage.getClanMembersIterator(False):
		g_user_cache.add_player(member)

def in_test_suite():
	import sys
	return "behave" in sys.argv[0]

def load_mod():
	global g_ts, g_talk_states, g_minimap_ctrl, g_user_cache

	# do all intializations here
	settings(os.path.join(utils.get_ini_dir_path(), "tessu_mod.ini")).on_reloaded += load_settings
	g_user_cache = UserCache(os.path.join(utils.get_ini_dir_path(), "tessu_mod_cache.ini"))

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

	g_messengerEvents.users.onUsersRosterReceived += on_users_rosters_received

try:
	import game
	from tessu_utils.ts3 import TS3Client
	from tessu_utils.utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	from tessu_utils import utils
	from tessu_utils.settings import settings
	from tessu_utils.user_cache import UserCache
	import BigWorld
	import Avatar
	import Account
	import VOIP
	from gui import SystemMessages
	from messenger.proto.events import g_messengerEvents
	from messenger.storage import storage_getter
	from messenger.proto.bw import find_criteria
	import os

	if not in_test_suite():
		load_mod()
except:
	raise
	LOG_CURRENT_EXCEPTION()
