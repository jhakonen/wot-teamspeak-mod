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
from gui.mods.tessumod.models import g_player_model, FilterModel
from gui.mods.tessumod.adapters.wotgame import MinimapAdapter

logger = logutils.logger.getChild("minimap")

class MinimapPlugin(plugintypes.ModPlugin, plugintypes.SettingsProvider, plugintypes.SettingsUIProvider):
	"""
	This plugin renders speech notifications to minimap in battle when a player
	who is in battle speaks in voice chat.
	"""

	def __init__(self):
		super(MinimapPlugin, self).__init__()
		self.__adapter = MinimapAdapter()
		self.__adapter.set_action_interval(2.0)
		self.__adapter.set_action("attackSender")
		self.__players = {}
		self.__enabled = False
		self.__self_enabled = False
		self.__filter_model = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.__filter_model = FilterModel(g_player_model)
		self.__filter_model.add_filter(lambda player: self.__enabled)
		self.__filter_model.add_filter(lambda player: player.is_alive)
		self.__filter_model.add_filter(lambda player: player.has_attribute("speaking"))
		self.__filter_model.add_filter(lambda player: player.has_attribute("vehicle_id"))
		self.__filter_model.add_filter(lambda player: self.__self_enabled or not player.is_me)

		self.__filter_model.on("added", self.__on_model_added)
		self.__filter_model.on("modified", self.__on_model_modified)
		self.__filter_model.on("removed", self.__on_model_removed)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "MinimapNotifications":
			if name == "enabled":
				self.__enabled = value
				self.__filter_model.invalidate()
			if name == "self_enabled":
				self.__self_enabled = value
				self.__filter_model.invalidate()
			if name == "action":
				self.__adapter.set_action(value)
			if name == "repeat_interval":
				self.__adapter.set_action_interval(value)

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"MinimapNotifications": {
				"help": "",
				"variables": [
					{
						"name": "enabled",
						"default": True,
						"help": "Enable or disable speak notifications in minimap"
					},
					{
						"name": "self_enabled",
						"default": True,
						"help": "Enable or disable notifications when you're speaking"
					},
					{
						"name": "action",
						"default": "attackSender",
						"help": """
							Define notification animation's appearance
							Can be one of the following:
							 - attack
							 - attackSPG
							 - attackSender
							 - attackSenderSPG
							 - enemySPG
							 - firstEnemy
							 - follow_me
							 - follow_meSPG
							 - help_me
							 - help_meSPG
							 - help_me_ex
							 - help_me_exSPG
							 - negative
							 - negativeSPG
							 - positive
							 - positiveSPG
							 - reloading_gun
							 - reloading_gunSPG
							 - stop
							 - stopSPG
							 - turn_back
							 - turn_backSPG
						"""
					},
					{
						"name": "repeat_interval",
						"default": 2.0,
						"help": """
							Define repeat interval (in seconds) of the notification animation.
							Adjust this until the animation animates continuously while someone is
							speaking.
						"""
					},

				]
			}
		}

	def get_settingsui_content(self):
		"""
		Implemented from SettingsUIProvider.
		"""
		return {
			"Minimap Settings": [
				{
					"label": "Enabled",
					"help": "Enable or disable speak notifications in minimap",
					"type": "checkbox",
					"variable": ("MinimapNotifications", "enabled")
				},
				{
					"label": "Enabled for self",
					"help": "Enable or disable notifications when you're speaking",
					"type": "checkbox",
					"variable": ("MinimapNotifications", "self_enabled")
				},
				{
					"label": "Notification animation",
					"help": """Select an animation type which is used in minimap
					to display the speak notification""",
					"type": "dropdown",
					"variable": ("MinimapNotifications", "action"),
					"choices": [
						"attack", "attackSPG", "attackSender", "attackSenderSPG",
						"enemySPG", "firstEnemy", "follow_me", "follow_meSPG", "help_me",
						"help_meSPG", "help_me_ex", "help_me_exSPG", "negative",
						"negativeSPG", "positive", "positiveSPG", "reloading_gun",
						"reloading_gunSPG", "stop", "stopSPG", "turn_back", "turn_backSPG"
					]
				},
				{
					"label": "Enabled for self",
					"help": """Defines repeat interval (in seconds) of the notification
						animation. Adjust this until the animation animates continuously
						while someone is speaking.""",
					"type": "combobox",
					"variable": ("MinimapNotifications", "repeat_interval")
				}
			]
		}

	def __on_model_added(self, new_player):
		logger.debug("__on_model_added: {}".format(new_player))
		self.__adapter.set_player_speaking(self.__player_to_old(new_player), new_player.speaking)

	def __on_model_modified(self, old_player, new_player):
		logger.debug("__on_model_modified: {}".format(new_player))
		self.__adapter.set_player_speaking(self.__player_to_old(new_player), new_player.speaking)

	def __on_model_removed(self, old_player):
		logger.debug("__on_model_removed: {}".format(old_player))
		self.__adapter.set_player_speaking(self.__player_to_old(old_player), False)

	def __player_to_old(self, player):
		return {
			"in_battle": True,
			"vehicle_id": player.vehicle_id
		}
