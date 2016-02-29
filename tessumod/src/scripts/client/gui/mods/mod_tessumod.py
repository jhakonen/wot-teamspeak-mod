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

from tessumod.infrastructure import gameapi, log, timer
from tessumod.adapters.settings import SettingsAdapter
from tessumod.adapters.wotgame import MinimapAdapter, ChatIndicatorAdapter, NotificationsAdapter, BattleAdapter, PlayerAdapter, EnvironmentAdapter
from tessumod.adapters.usercache import UserCacheAdapter
from tessumod.adapters.teamspeak import TeamSpeakChatClientAdapter
from tessumod.adapters.datastorage import DataStorageAdapter
from tessumod import application as app

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''

	try:
		log.install_logger_impl(gameapi.Logger)
		timer.set_eventloop(gameapi.EventLoop)

		app.inject("settings",      SettingsAdapter(app))
		app.inject("minimap",       MinimapAdapter())
		app.inject("chatindicator", ChatIndicatorAdapter())
		app.inject("usercache",     UserCacheAdapter(app))
		app.inject("chatclient",    TeamSpeakChatClientAdapter(app))
		app.inject("datastorage",   DataStorageAdapter())
		app.inject("notifications", NotificationsAdapter(app))
		app.inject("battle",        BattleAdapter(app))
		app.inject("players",       PlayerAdapter())
		app.inject("environment",   EnvironmentAdapter())

		try:
			from tessumod import build_info
			print "TessuMod version {0} ({1})".format(build_info.MOD_VERSION, build_info.SUPPORT_URL)
		except ImportError:
			print "TessuMod development version"

		app.execute_initialize()

	except:
		log.LOG_CURRENT_EXCEPTION()
