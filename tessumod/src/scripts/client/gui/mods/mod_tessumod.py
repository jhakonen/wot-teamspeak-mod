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
	from tessumod import boundaries, adapters
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

		usercache_impl = UserCache(cache_ini_path)
		storage_impl   = KeyValueStorage(utils.get_states_dir_path())
		settings_impl  = Settings(settings_ini_path)

		settings      = adapters.settings.SettingsAdapter(gameapi.EventLoop, settings_impl, boundaries)
		minimap       = adapters.wotgame.MinimapAdapter()
		chatindicator = adapters.wotgame.ChatIndicatorAdapter()
		notifications = adapters.wotgame.NotificationsAdapter(boundaries)
		battle        = adapters.wotgame.BattleAdapter(boundaries)
		players       = adapters.wotgame.PlayerAdapter()
		usercache     = adapters.usercache.UserCacheAdapter(usercache_impl, gameapi.EventLoop, boundaries)
		chatclient    = adapters.teamspeak.TeamSpeakChatClientAdapter(gameapi.EventLoop, boundaries)
		datastorage   = adapters.datastorage.DataStorageAdapter(storage_impl)

		boundaries.provide_dependency("settings",      settings)
		boundaries.provide_dependency("minimap",       minimap)
		boundaries.provide_dependency("chatindicator", chatindicator)
		boundaries.provide_dependency("usercache",     usercache)
		boundaries.provide_dependency("chatclient",    chatclient)
		boundaries.provide_dependency("datastorage",   datastorage)
		boundaries.provide_dependency("notifications", notifications)
		boundaries.provide_dependency("battle",        battle)
		boundaries.provide_dependency("players",       players)

		settings_impl.sync()
		gameapi.Notifications.init()
		usercache_impl.init()
		chatclient.init()

		print "TessuMod version {0} ({1})".format(utils.get_mod_version(), utils.get_support_url())

	except:
		log.LOG_CURRENT_EXCEPTION()
