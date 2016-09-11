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

from gui.mods.tessumod import plugintypes, logutils, models, pluginutils
from gui.mods.tessumod.adapters.wotgame import MinimapAdapter

logger = logutils.logger.getChild("minimap")

class MinimapPlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin):
	"""
	This plugin renders speech notifications to minimap in battle when a player
	who is in battle speaks in voice chat.
	"""

	def __init__(self):
		super(MinimapPlugin, self).__init__()
		self.__adapter = MinimapAdapter()
		self.__players = {}
		self.__enabled = False
		self.__self_enabled = False
		self.__filter_model = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.__filter_model = models.FilterModel(models.CompositeModel(
			pluginutils.get_player_models(self.plugin_manager, ["battle", "voice"])))
		self.__filter_model.add_filter(lambda item: self.__enabled)
		self.__filter_model.add_filter(lambda item: item.get("speaking", False))
		self.__filter_model.add_filter(lambda item: item.get("is_alive", False))
		self.__filter_model.add_filter(lambda item: "vehicle_id" in item)
		self.__filter_model.add_filter(lambda item: self.__self_enabled or not item["is_me"])

		self.__filter_model.on("added", self.__on_model_added)
		self.__filter_model.on("removed", self.__on_model_removed)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
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
		Implemented from SettingsMixin.
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
						"default": 2,
						"help": """
							Define repeat interval (in seconds) of the notification animation.
							Adjust this until the animation animates continuously while someone is
							speaking.
						"""
					},

				]
			}
		}

	def __on_model_added(self, new_player):
		self.__adapter.set_player_speaking(dict(new_player, in_battle=True), True)

	def __on_model_removed(self, old_player):
		self.__adapter.set_player_speaking(dict(old_player, in_battle=True), False)
