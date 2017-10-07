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
from gui.mods.tessumod.messages import PlayerSpeakingMessage, PlayerMeMessage
from gui.mods.tessumod.plugintypes import Plugin, SettingsProvider

logger = logutils.logger.getChild("speakindicator")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return SpeakIndicatorPlugin()

class SpeakIndicatorPlugin(Plugin, SettingsProvider):
	"""
	This plugin renders speech indicator notifications in game when a user
	matched a player speaks. The indicator is shown as a green ripple effect
	under player's name. There is also a speaker icon shown over tanks in battle.
	"""

	def __init__(self):
		super(SpeakIndicatorPlugin, self).__init__()
		self.__enabled = None
		self.__self_enabled = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.messages.subscribe(PlayerSpeakingMessage, self.__on_player_speaking_event)
		self.messages.subscribe(PlayerMeMessage, self.__on_player_is_me_event)

	@logutils.trace_call(logger)
	def deinitialize(self):
		self.messages.unsubscribe(PlayerSpeakingMessage, self.__on_player_speaking_event)
		self.messages.unsubscribe(PlayerMeMessage, self.__on_player_is_me_event)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "VoiceChatNotifications":
			if name == "enabled":
				self.__enabled = value
			if name == "self_enabled":
				self.__self_enabled = value
				self.__update_player_speaking(database.get_my_player_id())

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
	def __on_player_speaking_event(self, action, data):
		self.__update_player_speaking(data["id"])

	@logutils.trace_call(logger)
	def __on_player_is_me_event(self, action, data):
		self.__update_player_speaking(database.get_my_player_id())

	def __update_player_speaking(self, player_id):
		gameapi.set_player_speaking(player_id, self.__is_player_speaking(player_id))

	def __is_player_speaking(self, player_id):
		return \
			self.__enabled and \
			(self.__self_enabled or player_id != database.get_my_player_id()) and \
			database.is_player_speaking(player_id)
