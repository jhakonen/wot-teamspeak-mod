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
from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.lib.pluginmanager import Plugin
from gui.mods.tessumod.models import g_player_model, FilterModel

logger = logutils.logger.getChild("speakindicator")

class SpeakIndicatorPlugin(Plugin, plugintypes.SettingsProvider):
	"""
	This plugin renders speech indicator notifications in game when a user
	matched a player speaks. The indicator is shown as a green ripple effect
	under player's name. There is also a speaker icon shown over tanks in battle.
	"""

	def __init__(self):
		super(SpeakIndicatorPlugin, self).__init__()
		self.__filter_model = None
		self.__enabled = None
		self.__self_enabled = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.__filter_model = FilterModel(g_player_model)
		self.__filter_model.allow_namespaces(["battle", "prebattle"])
		self.__filter_model.add_filter(lambda player: self.__enabled)
		self.__filter_model.add_filter(lambda player: player.has_attribute("speaking"))
		self.__filter_model.add_filter(lambda player: self.__self_enabled or not player.is_me)

		self.__filter_model.on("added", self.__on_filter_model_added)
		self.__filter_model.on("modified", self.__on_filter_model_modified)
		self.__filter_model.on("removed", self.__on_filter_model_removed)

	@logutils.trace_call(logger)
	def deinitialize(self):
		self.__filter_model = None

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "VoiceChatNotifications":
			if name == "enabled":
				self.__enabled = value
				self.__filter_model.invalidate()
			if name == "self_enabled":
				self.__self_enabled = value
				self.__filter_model.invalidate()

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"VoiceChatNotifications": {
				"help": "",
				"variables": [
					{
						"name": "enabled",
						"default": True,
						"help": "Enable or disable speak notifications in player panels and showing of speaker icons above tanks"
					},
					{
						"name": "self_enabled",
						"default": True,
						"help": "Enable or disable notifications when you're speaking"
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def __on_filter_model_added(self, new_player):
		gameapi.set_player_speaking(new_player.id, new_player.speaking)

	@logutils.trace_call(logger)
	def __on_filter_model_modified(self, old_player, new_player):
		if new_player.speaking != old_player.speaking:
			gameapi.set_player_speaking(new_player.id, new_player.speaking)

	@logutils.trace_call(logger)
	def __on_filter_model_removed(self, old_player):
		gameapi.set_player_speaking(old_player.id, False)
