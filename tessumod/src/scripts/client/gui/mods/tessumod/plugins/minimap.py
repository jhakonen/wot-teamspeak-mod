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

from gui.mods.tessumod import database
from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.messages import VehicleMessage, PlayerSpeakingMessage, PlayerMeMessage
from gui.mods.tessumod.plugintypes import Plugin, SettingsProvider, SettingsUIProvider

import pydash as _

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
				_.for_each(database.get_all_vehicles(), lambda v: self.__render_to_minimap(v))
			if name == "self_enabled":
				self.__self_enabled = value
				self.__render_to_minimap(database.get_my_vehicle())
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

	@logutils.trace_call(logger)
	def __on_vehicle_event(self, action, vehicle):
		self.__render_to_minimap(vehicle)

	@logutils.trace_call(logger)
	def __on_player_speaking_event(self, action, speaking_player):
		self.__render_to_minimap(database.get_player_vehicle(player_id=speaking_player.id))

	@logutils.trace_call(logger)
	def __on_player_is_me_event(self, action, player):
		self.__render_to_minimap(database.get_my_vehicle())

	def __render_to_minimap(self, vehicle):
		if not vehicle:
			return
		speaking = \
			self.__enabled and \
			(self.__self_enabled or vehicle.player_id != database.get_my_player_id()) and \
			vehicle.is_alive and \
			database.is_player_speaking(vehicle.player_id)
		if speaking:
			if vehicle.id not in self.__running_animations:
				anim = gameapi.create_minimap_animation(vehicle.id, self.__interval, self.__action, self.__on_animation_done)
				self.__running_animations[vehicle.id] = anim
			self.__running_animations[vehicle.id].start()
		else:
			if vehicle.id in self.__running_animations:
				self.__running_animations[vehicle.id].stop()

	def __on_animation_done(self, vehicle_id):
		self.__running_animations.pop(vehicle_id, None)
