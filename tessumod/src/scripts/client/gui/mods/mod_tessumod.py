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
	from tessumod.infrastructure.utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	from tessumod.infrastructure.ts3 import TS3Client
	from tessumod.infrastructure import utils, mytsplugin, notifications, positional_audio
	from tessumod.infrastructure.settings import settings
	from tessumod.infrastructure.user_cache import UserCache
	from tessumod.infrastructure.keyvaluestorage import KeyValueStorage
	from tessumod import usecases, adapters, repositories
	import BigWorld
	import VOIP
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
		global settings_adapter

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

		g_talk_states = {}
		g_minimap_ctrl = utils.MinimapMarkersController()
		g_ts = TS3Client()

		g_positional_audio = positional_audio.PositionalAudio(
			ts_users      = g_ts.users_in_my_channel,
			user_cache    = g_user_cache
		)

		g_keyvaluestorage = KeyValueStorage(utils.get_states_dir_path())

		settings_adapter = adapters.SettingsAdapter(settings())
		minimap_adapter = adapters.MinimapAdapter(g_minimap_ctrl, settings_adapter)
		chat_indicator_adapter = adapters.ChatIndicatorAdapter(VOIP.getVOIPManager())
		user_cache_adapter = adapters.UserCacheAdapter(g_user_cache, usecases)
		chat_client_adapter = adapters.TeamSpeakChatClientAdapter(g_ts, usecases)
		notifications_adapter = adapters.NotificationsAdapter(notifications, usecases)
		game_adapter = adapters.GameAdapter(g_playerEvents, usecases)

		chat_user_repository = repositories.ChatUserRepository()
		player_repository = repositories.GamePlayerRepository()
		key_value_repository = repositories.KeyValueRepository(g_keyvaluestorage)

		usecases.provide_dependency("settings_api",           settings_adapter)
		usecases.provide_dependency("minimap_api",            minimap_adapter)
		usecases.provide_dependency("chat_indicator_api",     chat_indicator_adapter)
		usecases.provide_dependency("user_cache_api",         user_cache_adapter)
		usecases.provide_dependency("chat_client_api",        chat_client_adapter)
		usecases.provide_dependency("notifications_api",      notifications_adapter)
		usecases.provide_dependency("game_api",               game_adapter)
		usecases.provide_dependency("chat_user_repository",   chat_user_repository)
		usecases.provide_dependency("player_repository",      player_repository)
		usecases.provide_dependency("key_value_repository",   key_value_repository)
		usecases.provide_dependency("speak_state_repository", g_talk_states)

		g_user_cache.init()
		load_settings()

		g_ts.connect()
		utils.call_in_loop(settings_adapter.get_client_query_interval(), g_ts.check_events)

		g_playerEvents.onAvatarReady           += g_positional_audio.enable
		g_playerEvents.onAvatarBecomeNonPlayer += g_positional_audio.disable

		# don't show system center notifications in battle
		g_playerEvents.onAvatarBecomePlayer    += partial(notifications.set_notifications_enabled, False)
		g_playerEvents.onAvatarBecomeNonPlayer += partial(notifications.set_notifications_enabled, True)

		# if nothing broke so far then it should be safe to patch the needed
		# functions (modified functions have dependencies to g_* global variables)
		VOIP.VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIP.VOIPManager.isParticipantTalking)
		BattleReplay.BattleReplay.play = BattleReplay_play(BattleReplay.BattleReplay.play)

		g_messengerEvents.users.onUsersListReceived += on_users_list_received

		utils.call_in_loop(settings_adapter.get_ini_check_interval, sync_configs)

		usecases.speak_states = g_talk_states

		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())

	except:
		LOG_CURRENT_EXCEPTION()

def load_settings():
	LOG_NOTE("Settings loaded from ini file")
	utils.CURRENT_LOG_LEVEL = settings_adapter.get_log_level()
	g_ts.HOST = settings_adapter.get_client_query_host()
	g_ts.PORT = settings_adapter.get_client_query_port()

def sync_configs():
	g_user_cache.sync()
	settings().sync()

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		'''Called by other game modules (but not by minimap) to determine
		current speaking status.
		'''
		if dbid in g_talk_states:
			return g_talk_states[dbid] and usecases.is_voice_chat_speak_allowed(dbid)
		return orig_method(self, dbid)
	return wrapper

def BattleReplay_play(orig_method):
	def wrapper(*args, **kwargs):
		'''Called when replay is starting.
		Prevents user cache from getting polluted by incorrect pairings; If user
		plays someone else's replay and user's TS ID would get matched with the
		replay's player name.
		'''
		g_user_cache.is_write_enabled = settings_adapter.should_update_cache_in_replays()
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
