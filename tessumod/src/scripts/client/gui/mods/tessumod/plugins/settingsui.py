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
from gui.mods.tessumod.lib.pluginmanager import Plugin
from gui.mods.tessumod.lib.timer import TimerMixin

logger = logutils.logger.getChild("settingsui")

# =============================================================================
#                          IMPLEMENTATION MISSING
#  - Passing content description to flash
#  - Passing user cache data to flash
#  - Passing ignored message info to flash
#  - Showing the settings ui
#  - Showing button in ui for opening the settings ui
#  - Handling events from flash (ok, apply, cancel, changes in controls)
# =============================================================================

class SettingsUIPlugin(Plugin, TimerMixin, plugintypes.SettingsProvider):
	"""
	This plugin...
	"""

	def __init__(self):
		super(SettingsUIPlugin, self).__init__()
		self.__snapshots = []

	@logutils.trace_call(logger)
	def initialize(self):
		self.on_timeout(0, self.__load_descriptions)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		pass

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {}

	@logutils.trace_call(logger)
	def open_ui(self):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SnapshotProvider"):
			self.__snapshots.append(plugin_info.plugin_object.create_snapshot())

	@logutils.trace_call(logger)
	def on_accepted(self):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SnapshotProvider"):
			for snapshot in self.__snapshots:
				plugin_info.plugin_object.release_snaphot(snapshot)

	@logutils.trace_call(logger)
	def on_cancelled(self):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SnapshotProvider"):
			for snapshot in self.__snapshots:
				plugin_info.plugin_object.restore_snapshot(snapshot)
				plugin_info.plugin_object.release_snaphot(snapshot)

	def __load_descriptions(self):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SettingsUIProvider"):
			content = plugin_info.plugin_object.get_settingsui_content()
