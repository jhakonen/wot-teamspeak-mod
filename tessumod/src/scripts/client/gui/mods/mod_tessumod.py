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

from tessumod.lib import logutils, gameapi, timer
from tessumod.pluginmanager import ModPluginManager
import os
from tessumod import migrate, plugintypes

plugin_manager = None

logutils.init(os.path.join(gameapi.Environment.find_res_mods_version_path(),
	"..", "configs", "tessu_mod", "logging.ini"), gameapi.LogRedirectionHandler())
logger = logutils.logger

def init():
	'''Mod's main entry point. Called by WoT's built-in mod loader.'''
	global plugin_manager
	try:
		timer.set_eventloop(gameapi.EventLoop)

		try:
			from tessumod import build_info
			print "TessuMod version {0} ({1})".format(build_info.MOD_VERSION, build_info.SUPPORT_URL)
		except ImportError:
			print "TessuMod development version"

		migrate.migrate()

		plugin_manager = ModPluginManager(plugintypes.ModPlugin)
		plugin_manager.collectPlugins()
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_manager.activatePluginByName(plugin_info.name)
			plugin_info.plugin_object.plugin_manager = plugin_manager
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.plugin_object.initialize()

	except:
		logger.exception("TessuMod initialization failed")

def fini():
	'''Mod's destructor entry point. Called by WoT's built-in mod loader.'''
	global plugin_manager
	if plugin_manager is not None:
		for plugin_info in plugin_manager.getAllPlugins():
			plugin_info.plugin_object.deinitialize()
