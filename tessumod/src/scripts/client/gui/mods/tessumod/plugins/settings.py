# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2016  Janne Hakonen
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

from gui.mods.tessumod import plugintypes, logutils
import gui.mods.tessumod.adapters.settings as adapter_settings
from gui.mods.tessumod.constants import SettingConstants
from gui.mods.tessumod.infrastructure.inifile import INIFile
from gui.mods.tessumod.infrastructure.gameapi import Environment
import os
import copy
import BigWorld

logger = logutils.logger.getChild("settings")

class SettingsPlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin, plugintypes.SettingsUIProvider):
	"""
	This plugin loads settings from tessu_mod.ini file and writes a default
	file when the config file is missing.

	Calls following methods from "Settings" category:
	 * get_settings_content: To get information from other plugins what the
	                         config file should contain
	 * on_settings_changed:  For every setting variable at mod start and later
	                         when any variable have been changed (due of config
	                         file modified on fly)
	"""

	def __init__(self):
		super(SettingsPlugin, self).__init__()
		self.__inifile = INIFile(adapter_settings.DEFAULT_INI)
		self.__inifile.on("file-loaded", self.__on_file_loaded)
		self.__inifile.set_filepath(os.path.join(Environment.find_res_mods_version_path(),
			"..", "configs", "tessu_mod", "tessu_mod.ini"))
		self.__previous_values = {}
		self.__type_to_getter = {
			bool: self.__inifile.get_boolean,
			int: self.__inifile.get_int,
			float: self.__inifile.get_float,
			str: self.__inifile.get_string,
			unicode: self.__inifile.get_string,
			list: self.__inifile.get_list
		}

	@logutils.trace_call(logger)
	def initialize(self):
		BigWorld.callback(0, self.__inifile.init)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "General":
			if name == "ini_check_interval":
				self.__inifile.set_file_check_interval(value)

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsMixin.
		"""
		return {
			"General": {
				"help": "",
				"variables": [
					{
						"name": "ini_check_interval",
						"default": 5,
						"help": "Interval (as seconds) that this ini-file is checked for modifications, and reloaded if modified"
					}
				]
			}
		}

	def get_settingsui_content(self):
		"""
		Implemented from SettingsUIProvider.
		"""
		return {
			"General Settings": [
				{
					"label": "Config poll interval",
					"help": """Interval (as seconds) that this ini-file is checked
						for modifications, and reloaded if modified.""",
					"type": "combobox",
					"variable": ("General", "ini_check_interval")
				}
			]
		}

	def __on_file_loaded(self):
		new_values = {}
		for plugin_info in self.plugin_manager.getPluginsOfCategory("Settings"):
			content = plugin_info.plugin_object.get_settings_content()
			for section in content:
				variables = content[section]["variables"]
				if variables == "any":
					new_values[(section, section)] = self.__inifile.get_dict(section, self.__type_to_getter[content[section]["variable_type"]], default={})
				else:
					for variable in variables:
						name = variable["name"]
						default = variable["default"]
						new_values[(section, name)] = self.__type_to_getter[type(default)](section, name, default=default)

		for plugin_info in self.plugin_manager.getPluginsOfCategory("Settings"):
			for key, value in new_values.iteritems():
				if value != self.__previous_values.get(key, None):
					section, name = key
					plugin_info.plugin_object.on_settings_changed(section, name, value)

		self.__previous_values = new_values
