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

from tessumod.infrastructure import gameapi, log, timer, di
from tessumod.adapters.settings import SettingsAdapter
from tessumod.adapters.wotgame import (MinimapAdapter, ChatIndicatorAdapter, NotificationsAdapter, BattleAdapter,
	PlayerAdapter, EnvironmentAdapter)
from tessumod.adapters.usercache import UserCacheAdapter
from tessumod.adapters.teamspeak import TeamSpeakChatClientAdapter
from tessumod.adapters.datastorage import DataStorageAdapter
from tessumod.interactors import (Initialize, LoadSettings, CacheChatUser, PairChatUserToPlayer,
	UpdateChatUserSpeakState, RemoveChatUser, ClearSpeakStatuses, NotifyChatClientDisconnected,
	ShowChatClientPluginInstallMessage, InstallChatClientPlugin, IgnoreChatClientPluginInstallMessage,
	ShowChatClientPluginInfoUrl, NotifyConnectedToChatServer, PublishGameNickToChatServer, ShowCacheErrorMessage,
	EnablePositionalDataToChatClient, ProvidePositionalDataToChatClient, BattleReplayStart,
	PopulateUserCacheWithPlayers)
from tessumod.pluginmanager import ModPluginManager
import logging
import logging.config
import os
from tessumod import logutils

plugin_manager = None

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''

	try:
		log.install_logger_impl(gameapi.Logger)
		logutils.init(os.path.join(gameapi.Environment.find_res_mods_version_path(),
			"..", "configs", "tessu_mod", "logging.ini"))

		timer.set_eventloop(gameapi.EventLoop)

		app = {
			"initialize": Initialize,
			"load-settings": LoadSettings,
			"cache-chatuser": CacheChatUser,
			"pair-chatuser-to-player": PairChatUserToPlayer,
			"update-chatuser-speakstate": UpdateChatUserSpeakState,
			"remove-chatuser": RemoveChatUser,
			"clear-speakstatuses": ClearSpeakStatuses,
			"notify-chatclient-disconnected": NotifyChatClientDisconnected,
			"show-chatclient-plugin-install-message": ShowChatClientPluginInstallMessage,
			"install-chatclient-plugin": InstallChatClientPlugin,
			"ignore-chatclient-plugin-install-message": IgnoreChatClientPluginInstallMessage,
			"show-chatclient-plugin-info-url": ShowChatClientPluginInfoUrl,
			"notify-connected-to-chatserver": NotifyConnectedToChatServer,
			"publish-gamenick-to-chatserver": PublishGameNickToChatServer,
			"show-usercache-error-message": ShowCacheErrorMessage,
			"enable-positional-data-to-chatclient": EnablePositionalDataToChatClient,
			"provide-positional-data-to-chatclient": ProvidePositionalDataToChatClient,
			"battle-replay-start": BattleReplayStart,
			"populate-usercache-with-players": PopulateUserCacheWithPlayers
		}

		[di.install_provider(interactor) for interactor in app.itervalues()]

		for name, cls in app.iteritems():
			#app[name] = create_executable(cls)
			app[name] = noop

		di.provide("settings",      SettingsAdapter(app))
		di.provide("minimap",       MinimapAdapter())
		di.provide("chatindicator", ChatIndicatorAdapter())
		di.provide("usercache",     UserCacheAdapter(app))
		di.provide("chatclient",    TeamSpeakChatClientAdapter(app))
		di.provide("datastorage",   DataStorageAdapter())
		di.provide("notifications", NotificationsAdapter(app))
		di.provide("battle",        BattleAdapter(app))
		di.provide("players",       PlayerAdapter())
		di.provide("environment",   EnvironmentAdapter())

		try:
			from tessumod import build_info
			print "TessuMod version {0} ({1})".format(build_info.MOD_VERSION, build_info.SUPPORT_URL)
		except ImportError:
			print "TessuMod development version"

		app["initialize"]()

		plugin_manager = ModPluginManager()
		plugin_manager.collectPlugins()
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_manager.activatePluginByName(plugin_info.name)
			plugin_info.plugin_object.plugin_manager = plugin_manager
			plugin_info.plugin_object.initialize()

	except:
		log.LOG_CURRENT_EXCEPTION()

def fini():
	'''Mod's destructor entry point. Called by WoT's built-in mod loader.'''
	if plugin_manager is not None:
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.plugin_object.deinitialize()

def create_executable(cls):
	def execute(*args, **kwargs):
		return cls().execute(*args, **kwargs)
	return execute

def noop(*args, **kwargs):
	pass