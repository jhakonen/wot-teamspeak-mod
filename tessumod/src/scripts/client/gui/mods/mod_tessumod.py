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

import sys
import inspect
import json
import os

from tessumod import database, migrate, plugintypes, constants
from tessumod.lib import gameapi, logutils, messagepump, timer
from tessumod.lib.pluginmanager import PluginManager

plugin_manager = None

log_config_path = "./mods/configs/tessumod/logging.ini"

logutils.init(log_config_path, gameapi.create_log_redirection_handler())
logger = logutils.logger

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''
	global plugin_manager
	try:
		gameapi.init()
		timer.set_eventloop(gameapi.create_event_loop())

		try:
			from tessumod import build_info
			print "TessuMod version {0} ({1})".format(build_info.MOD_VERSION, build_info.SUPPORT_URL)
		except ImportError:
			print "TessuMod development version"

		migrate.migrate()

		config = json.loads(gameapi.resources_read_file(constants.RESOURCES_DATA_DIR + '/config.json'))

		plugin_categories = [member[1] for member in inspect.getmembers(plugintypes, inspect.isclass)]
		plugin_manager = PluginManager(config["plugins"], config["plugins_import_path"], plugin_categories)
		plugin_manager.collectPlugins()
		messages = messagepump.MessagePump()
		database.messages = messages
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.plugin_object.plugin_manager = plugin_manager
			plugin_info.plugin_object.messages = messages
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.initialize()

	except:
		logger.exception("TessuMod initialization failed")

def fini():
	'''Mod's destructor entry point. Called by WoT's built-in mod loader.'''
	global plugin_manager
	if plugin_manager is not None:
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.deinitialize()
	gameapi.deinit()
