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
import BigWorld

logger = logutils.logger.getChild("settingsui")

# =============================================================================
#                          IMPLEMENTATION MISSING
#  - Passing content description to flash
#  - Passing user cache data to flash
#  - Passing ignored message info to flash
#  - Showing the settings ui
#  - Showing button in ui for opening the settings ui
#  - Handling events from flash (ok, apply, cancel, changes in controls)
#  - Creating, restoring and deleting snapshots
# =============================================================================

class SettingsUIPlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin):
	"""
	This plugin...
	"""

	def __init__(self):
		super(SettingsUIPlugin, self).__init__()

	@logutils.trace_call(logger)
	def initialize(self):
		BigWorld.callback(0, self.__load_descriptions)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		pass

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsMixin.
		"""
		return {}

	def __load_descriptions(self):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("SettingsUIProvider"):
			content = plugin_info.plugin_object.get_settingsui_content()
