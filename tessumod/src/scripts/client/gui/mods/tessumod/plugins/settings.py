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

from gui.mods.tessumod import plugintypes
from gui.mods.tessumod.lib import logutils
from gui.mods.tessumod.lib.gameapi import Environment
from gui.mods.tessumod.lib.pluginmanager import Plugin
import BigWorld

import os
import copy
import json
import uuid

logger = logutils.logger.getChild("settings")

# =============================================================================
#                          IMPLEMENTATION MISSING
#  - Add writing into file
# =============================================================================

class SettingsPlugin(Plugin, plugintypes.Settings,
	plugintypes.SnapshotProvider):
	"""
	This plugin loads settings from tessu_mod.ini file and writes a default
	file when the config file is missing.

	Calls following methods from "SettingsProvider" category:
	 * get_settings_content: To get information from other plugins what the
	                         config file should contain
	 * on_settings_changed:  For every setting variable at mod start and later
	                         when any variable have been changed (due of config
	                         file modified on fly)
	"""

	def __init__(self):
		super(SettingsPlugin, self).__init__()
		self.__snapshots = {}
		self.__previous_values = {}
		self.__filepath = os.path.join(Environment.find_res_mods_version_path(),
			"..", "configs", "tessumod", "settings.json")

	@logutils.trace_call(logger)
	def initialize(self):
		self.__load_settings_data()
		BigWorld.callback(0, self.__notify_changed_settings)

	@logutils.trace_call(logger)
	def deinitialize(self):
		self.__save_settings_data()

	def set_settings_value(self, section, name, value):
		"""
		Implemented from Settings.
		"""
		self.__settings_data[section][name] = value
		self.__save_settings_data()
		self.__notify_changed_settings()

	@logutils.trace_call(logger)
	def create_snapshot(self):
		"""
		Implemented from SnapshotProvider.
		"""
		snapshot_name = uuid.uuid4()
		self.__snapshots[snapshot_name] = copy.deepcopy(self.__settings_data)
		return snapshot_name

	@logutils.trace_call(logger)
	def release_snaphot(self, snapshot_name):
		"""
		Implemented from SnapshotProvider.
		"""
		if snapshot_name in self.__snapshots:
			del self.__snapshots[snapshot_name]

	@logutils.trace_call(logger)
	def restore_snapshot(self, snapshot_name):
		"""
		Implemented from SnapshotProvider.
		"""
		if snapshot_name in self.__snapshots:
			self.__settings_data = self.__snapshots[snapshot_name]

	def __load_settings_data(self):
		"""
		Loads settings data from disk.
		"""
		# load settings file if one exists
		if os.path.isfile(self.__filepath):
			with open(self.__filepath, "rb") as file:
				self.__settings_data = json.loads(file.read())
		# load default values (existing variables are not overwritten)
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SettingsProvider"):
			content = plugin_info.plugin_object.get_settings_content()
			for category_name in content:
				category_content = content[category_name]
				variables = category_content["variables"]
				self.__settings_data.setdefault(category_name, {})
				if variables == "any":
					continue
				for variable in variables:
					self.__settings_data[category_name].setdefault(
						variable["name"], variable["default"])

	def __save_settings_data(self):
		"""
		Saves settings data to disk.
		"""
		# create destination directory if it doesn't exist yet
		dest_dirpath = os.path.dirname(self.__filepath)
		if not os.path.isdir(dest_dirpath):
			os.makedirs(dest_dirpath)
		# write out the settings file
		with open(self.__filepath, "wb") as out_file:
			out_file.write(json.dumps(self.__settings_data, indent=4))

	def __notify_changed_settings(self):
		"""
		Calls on_settings_changed() of any plugin which implements
		"SettingsProvider" interface when a setting has changed since last
		notification.
		"""
		# find changed settings
		changed = []
		for section, variables in self.__settings_data.iteritems():
			if section == "version":
				continue
			for name, value in variables.iteritems():
				if value != self.__previous_values.get(section, {}).get(name, None):
					changed.append((section, name, value))
		# notify listeners
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SettingsProvider"):
			for section, name, value in changed:
				plugin_info.plugin_object.on_settings_changed(section, name, value)
		# Save changed values for next time
		self.__previous_values = copy.deepcopy(self.__settings_data)
