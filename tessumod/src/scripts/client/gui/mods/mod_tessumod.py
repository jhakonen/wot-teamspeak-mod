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

from tessumod.infrastructure import gameapi, log
from tessumod import boundaries, adapters

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''

	try:
		log.install_logger_impl(gameapi.Logger)

		settings      = adapters.settings.SettingsAdapter(gameapi.EventLoop, boundaries)
		minimap       = adapters.wotgame.MinimapAdapter()
		chatindicator = adapters.wotgame.ChatIndicatorAdapter()
		notifications = adapters.wotgame.NotificationsAdapter(boundaries)
		battle        = adapters.wotgame.BattleAdapter(boundaries)
		players       = adapters.wotgame.PlayerAdapter()
		usercache     = adapters.usercache.UserCacheAdapter(gameapi.EventLoop, boundaries)
		chatclient    = adapters.teamspeak.TeamSpeakChatClientAdapter(gameapi.EventLoop, boundaries)
		datastorage   = adapters.datastorage.DataStorageAdapter()

		boundaries.provide_dependency("settings",      settings)
		boundaries.provide_dependency("minimap",       minimap)
		boundaries.provide_dependency("chatindicator", chatindicator)
		boundaries.provide_dependency("usercache",     usercache)
		boundaries.provide_dependency("chatclient",    chatclient)
		boundaries.provide_dependency("datastorage",   datastorage)
		boundaries.provide_dependency("notifications", notifications)
		boundaries.provide_dependency("battle",        battle)
		boundaries.provide_dependency("players",       players)

		[adapter.init() for adapter in (settings, notifications, usercache, chatclient)]

		try:
			from tessumod import build_info
			print "TessuMod version {0} ({1})".format(build_info.MOD_VERSION, build_info.SUPPORT_URL)
		except ImportError:
			print "TessuMod development version"

	except:
		log.LOG_CURRENT_EXCEPTION()
