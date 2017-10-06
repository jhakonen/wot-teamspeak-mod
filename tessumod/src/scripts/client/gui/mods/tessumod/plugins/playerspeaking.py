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
from gui.mods.tessumod.items import get_items
from gui.mods.tessumod.lib import logutils
from gui.mods.tessumod.lib import pydash as _
from gui.mods.tessumod.lib.timer import TimerMixin
from gui.mods.tessumod.messages import UserMessage, PairingMessage, PlayerSpeakingMessage
from gui.mods.tessumod.plugintypes import Plugin, SettingsProvider, SettingsUIProvider, EntityProvider

from copy import copy

logger = logutils.logger.getChild("playerspeaking")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return PlayerSpeakingPlugin()

# =============================================================================
#                          IMPLEMENTATION MISSING
#  - Add ability to remove matches (called from settingsui)
# =============================================================================

class PlayerSpeakingPlugin(Plugin, SettingsProvider, SettingsUIProvider, EntityProvider):
	"""
	This plugin ...
	"""

	NS = "voice"

	def __init__(self):
		super(PlayerSpeakingPlugin, self).__init__()
		self.__speak_stop_delay = 0
		self.__notifiers = {}

	@logutils.trace_call(logger)
	def initialize(self):
		self.messages.subscribe(UserMessage, self.__on_user_event)
		self.messages.subscribe(PairingMessage, self.__on_pairing_event)

	@logutils.trace_call(logger)
	def deinitialize(self):
		self.messages.unsubscribe(UserMessage, self.__on_user_event)
		self.messages.unsubscribe(PairingMessage, self.__on_pairing_event)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "General":
			if name == "speak_stop_delay":
				self.__speak_stop_delay = value

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"General": {
				"help": "",
				"variables": [
					{
						"name": "speak_stop_delay",
						"default": 1.0,
						"help": "Delay (in seconds) stopping of speak feedback after users has stopped speaking"
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def get_settingsui_content(self):
		"""
		Implemented from SettingsUIProvider.
		"""
		return {
			"General Settings": [
				{
					"label": "Speak stop delay",
					"help": "Delay stopping of speak feedback after users has stopped speaking",
					"type": "slider",
					"min": 0.0,
					"max": 10.0,
					"step": 0.1,
					"unit": "s",
					"variable": ("General", "speak_stop_delay")
				}
			]
		}

	@logutils.trace_call(logger)
	def has_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		return name == "speaking-players"

	@logutils.trace_call(logger)
	def get_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		if name == "speaking-players":
			return database.speaking_players.clone()

	def __get_paired_players(self, user_unique_id):
		pairings = get_items(self.plugin_manager, ["pairings"], ["player-id", "user-unique-id"])
		return [pairing["player-id"] for pairing in _.filter_(pairings, lambda p: p["user-unique-id"] == user_unique_id)]

	@logutils.trace_call(logger)
	def __on_user_event(self, action, data):
		user_id = data["id"]
		if action == "added":
			self.__notifiers[user_id] = DelayedSpeakNotifier(user_id, data["unique-id"], self.messages)
			self.__notifiers[user_id].set_stop_delay(self.__speak_stop_delay)
			self.__notifiers[user_id].set_player_ids(self.__get_paired_players(data["unique-id"]))
		if action in ["added", "modified"]:
			self.__notifiers[user_id].set_speaking(data["speaking"])
		if action == "removed":
			self.__notifiers[user_id].force_stop()
			del self.__notifiers[user_id]

	@logutils.trace_call(logger)
	def __on_pairing_event(self, action, data):
		key = (data["user-unique-id"], data["player-id"])
		if action == "added":
			for notifier in _.filter_(self.__notifiers, lambda n: n.user_unique_id == data["user-unique-id"]):
				notifier.set_player_ids(self.__get_paired_players(data["user-unique-id"]))
		elif action == "removed":
			for notifier in _.filter_(self.__notifiers, lambda n: n.user_unique_id == data["user-unique-id"]):
				notifier.set_player_ids(self.__get_paired_players(data["user-unique-id"]))

class DelayedSpeakNotifier(TimerMixin):

	def __init__(self, user_id, user_unique_id, messages):
		super(DelayedSpeakNotifier, self).__init__()
		self.user_id = user_id
		self.user_unique_id = user_unique_id
		self.messages = messages
		self.__stop_delay = 0
		self.__player_ids = []
		self.__speaking = False
		self.__timeout_running = False

	def get_speaking_player_ids(self):
		if self.__speaking or self.__timeout_running:
			return self.__player_ids
		return []

	def force_stop(self):
		self.__speaking = False
		self.off_timeout(self.__on_timeout)
		self.__notify(self.__player_ids, self.__speaking)

	def set_stop_delay(self, delay):
		self.__stop_delay = delay

	def set_player_ids(self, player_ids):
		removed_ids = set(self.__player_ids) - set(player_ids)
		added_ids = set(player_ids) - set(self.__player_ids)
		self.__player_ids = player_ids
		if self.__speaking:
			self.__notify(added_ids, True)
			self.__notify(removed_ids, False)
		elif self.__timeout_running:
			self.__notify(removed_ids, False)

	def set_speaking(self, speaking):
		if self.__speaking == speaking:
			return
		self.__speaking = speaking
		if speaking:
			self.off_timeout(self.__on_timeout)
			self.__timeout_running = False
			self.__notify(self.__player_ids, self.__speaking)
		else:
			self.on_timeout(self.__stop_delay, self.__on_timeout)
			self.__timeout_running = True

	def __on_timeout(self):
		self.__timeout_running = False
		if not self.__speaking:
			self.__notify(self.__player_ids, self.__speaking)

	def __notify(self, player_ids, speaking):
		for player_id in player_ids:
			old_player = _.head(database.speaking_players.where(id=player_id))
			if speaking and not old_player:
				new_player = database.DictDataObject({"id": player_id})
				database.speaking_players.insert(new_player)
				self.messages.publish(PlayerSpeakingMessage("added", copy(new_player)))
			elif not speaking and old_player:
				database.speaking_players.remove(old_player)
				self.messages.publish(PlayerSpeakingMessage("removed", old_player))
