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
	from tessumod.infrastructure import utils, mytsplugin, gameapi, log
	from tessumod.infrastructure.settings import Settings
	from tessumod.infrastructure.user_cache import UserCache
	from tessumod.infrastructure.keyvaluestorage import KeyValueStorage
	from tessumod import usecases, adapters, repositories
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
		log.install_logger_impl(gameapi.Logger)

		# make sure that ini-folder exists
		try:
			os.makedirs(utils.get_ini_dir_path())
		except os.error:
			pass
		settings_ini_path = os.path.join(utils.get_ini_dir_path(), "tessu_mod.ini")
		cache_ini_path    = os.path.join(utils.get_ini_dir_path(), "tessu_mod_cache.ini")

		# do all intializations here
		usercache    = UserCache(cache_ini_path)
		storage      = KeyValueStorage(utils.get_states_dir_path())
		settings     = Settings(settings_ini_path)

		settings_adapter       = adapters.settings.SettingsAdapter(gameapi.EventLoop, settings, usecases)
		minimap_adapter        = adapters.wotgame.MinimapAdapter()
		chat_indicator_adapter = adapters.wotgame.ChatIndicatorAdapter()
		notifications_adapter  = adapters.wotgame.NotificationsAdapter(usecases)
		battle_adapter         = adapters.wotgame.BattleAdapter(usecases)
		player_adapter         = adapters.wotgame.PlayerAdapter()
		user_cache_adapter     = adapters.usercache.UserCacheAdapter(usercache, gameapi.EventLoop, usecases)
		chat_client_adapter    = adapters.teamspeak.TeamSpeakChatClientAdapter(gameapi.EventLoop, usecases)

		settings_repository  = repositories.KeyValueRepository({})
		chat_user_repository = repositories.ChatUserRepository()
		vehicle_repository   = repositories.VehicleRepository(gameapi.Battle)
		key_value_repository = repositories.KeyValueRepository(storage)

		usecases.provide_dependency("settings_api",           settings_adapter)
		usecases.provide_dependency("minimap_api",            minimap_adapter)
		usecases.provide_dependency("chat_indicator_api",     chat_indicator_adapter)
		usecases.provide_dependency("user_cache_api",         user_cache_adapter)
		usecases.provide_dependency("chat_client_api",        chat_client_adapter)
		usecases.provide_dependency("notifications_api",      notifications_adapter)
		usecases.provide_dependency("battle_api",             battle_adapter)
		usecases.provide_dependency("player_api",             player_adapter)
		usecases.provide_dependency("settings_repository",    settings_repository)
		usecases.provide_dependency("chat_user_repository",   chat_user_repository)
		usecases.provide_dependency("vehicle_repository",     vehicle_repository)
		usecases.provide_dependency("key_value_repository",   key_value_repository)

		settings.sync()
		gameapi.Notifications.init()
		usercache.init()
		chat_client_adapter.init()

		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())

	except:
		log.LOG_CURRENT_EXCEPTION()
