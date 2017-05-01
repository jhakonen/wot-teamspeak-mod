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

from gui.mods.tessumod.items import get_items, match_id, match_player_id
from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.lib import pydash as _
from gui.mods.tessumod.messages import VehicleMessage, PlayerSpeakingMessage, PlayerMeMessage
from gui.mods.tessumod.plugintypes import Plugin, SettingsProvider, SettingsUIProvider

logger = logutils.logger.getChild("minimap")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return MinimapPlugin()

class MinimapPlugin(Plugin, SettingsProvider, SettingsUIProvider):
	"""
	This plugin renders speech notifications to minimap in battle when a player
	who is in battle speaks in voice chat.
	"""

	def __init__(self):
		super(MinimapPlugin, self).__init__()
		self.__action = "attackSender"
		self.__interval = 2.0
		self.__running_animations = {}
		self.__enabled = False
		self.__self_enabled = False
		self.__my_player_id = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.messages.subscribe(VehicleMessage, self.__on_vehicle_event)
		self.messages.subscribe(PlayerSpeakingMessage, self.__on_player_speaking_event)
		self.messages.subscribe(PlayerMeMessage, self.__on_player_is_me_event)

	@logutils.trace_call(logger)
	def deinitialize(self):
		self.messages.unsubscribe(VehicleMessage, self.__on_vehicle_event)
		self.messages.unsubscribe(PlayerSpeakingMessage, self.__on_player_speaking_event)
		self.messages.unsubscribe(PlayerMeMessage, self.__on_player_is_me_event)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "MinimapNotifications":
			if name == "enabled":
				self.__enabled = value
				_.for_each(self.__get_vehicles(), lambda v: self.__set_vehicle_speaking(v))
			if name == "self_enabled":
				self.__self_enabled = value
				self.__set_vehicle_speaking(self.__get_my_vehicle())
			if name == "action":
				self.__action = value
			if name == "repeat_interval":
				self.__interval = value

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

	def __get_vehicles(self):
		return get_items(self.plugin_manager, ["vehicles"], ["id"])

	def __get_speaking_players(self):
		return map(lambda p: p["id"], get_items(self.plugin_manager, ["speaking-players"], ["id"]))

	def __get_my_vehicle(self):
		return _.find(self.__get_vehicles(), lambda v: v["player-id"] == self.__my_player_id)

	@logutils.trace_call(logger)
	def __on_vehicle_event(self, action, data):
		self.__set_vehicle_speaking(data)

	@logutils.trace_call(logger)
	def __on_player_speaking_event(self, action, data):
		self.__set_vehicle_speaking(_.find(self.__get_vehicles(), match_player_id(data["id"])))

	@logutils.trace_call(logger)
	def __on_player_is_me_event(self, action, data):
		self.__my_player_id = data["id"]
		self.__set_vehicle_speaking(self.__get_my_vehicle())

	def __set_vehicle_speaking(self, vehicle):
		if not vehicle:
			return
		vehicle_id = vehicle["id"]
		speaking = \
			self.__enabled and \
			(self.__self_enabled or vehicle["player-id"] != self.__my_player_id) and \
			vehicle["is-alive"] and \
			vehicle["player-id"] in self.__get_speaking_players()
		if speaking:
			if vehicle_id not in self.__running_animations:
				anim = gameapi.create_minimap_animation(vehicle_id, self.__interval, self.__action, self.__on_animation_done)
				self.__running_animations[vehicle_id] = anim
			self.__running_animations[vehicle_id].start()
		else:
			if vehicle_id in self.__running_animations:
				self.__running_animations[vehicle_id].stop()

	def __on_animation_done(self, vehicle_id):
		self.__running_animations.pop(vehicle_id, None)
