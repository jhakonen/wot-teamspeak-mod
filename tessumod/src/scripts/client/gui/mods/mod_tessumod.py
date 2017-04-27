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

from tessumod import migrate, plugintypes
from tessumod.lib import logutils, gameapi, timer
from tessumod.lib.pluginmanager import PluginManager

import inspect
import json
import os

plugin_manager = None

mods_path = gameapi.find_res_mods_version_path()
log_config_path = os.path.join(mods_path, "..", "configs", "tessu_mod", "logging.ini")
config_path     = os.path.join(mods_path, "scripts", "client", "gui", "mods", "tessumod", "config.json")
plugins_path    = os.path.join(mods_path, "scripts", "client", "gui", "mods", "tessumod", "plugins")

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

		with open(config_path, "rb") as config_file:
			config = json.loads(config_file.read())

		plugin_categories = [member[1] for member in inspect.getmembers(plugintypes, inspect.isclass)]
		plugin_manager = PluginManager(config["plugins"], plugins_path, plugin_categories)
		plugin_manager.collectPlugins()
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.plugin_object.plugin_manager = plugin_manager
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
