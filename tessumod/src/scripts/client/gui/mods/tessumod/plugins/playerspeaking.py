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
import re
from operator import or_
import functools
import BigWorld

logger = logutils.logger.getChild("playerspeaking")

# =============================================================================
#                          IMPLEMENTATION MISSING
#  - Add ability to remove matches (called from settingsui)
#  - snapshot interface
# =============================================================================

class PlayerSpeaking(plugintypes.ModPlugin, plugintypes.SettingsMixin,
	plugintypes.SettingsUIProvider, plugintypes.PlayerModelProvider):
	"""
	This plugin ...
	"""

	def __init__(self):
		super(PlayerSpeaking, self).__init__()
		self.__model = models.Model()
		self.__model_proxy = models.ImmutableModelProxy(self.__model)
		self.__all_player_model = None
		self.__user_model = None
		self.__speak_stop_delay = 0
		self.__user_speak_state_timers = {}
		self.__delayed_user_speak_states = {}

	@logutils.trace_call(logger)
	def initialize(self):
		self.__all_player_model = pluginutils.get_player_model(self.plugin_manager, ["battle", "prebattle"])
		self.__all_player_model.on('added', self.__repopulate_voice_players)
		self.__all_player_model.on('removed', self.__repopulate_voice_players)

		self.__user_model = pluginutils.get_user_model(self.plugin_manager, ["voice"])
		self.__user_model.on("added", self.__on_user_added)
		self.__user_model.on("modified", self.__on_user_modified)
		self.__user_model.on("removed", self.__on_user_removed)

		self.__pairing_model = self.plugin_manager.getPluginsOfCategory("UserCache")[0].plugin_object.get_pairing_model()
		self.__pairing_model.on('added', self.__repopulate_voice_players)
		self.__pairing_model.on("modified", self.__repopulate_voice_players)
		self.__pairing_model.on('removed', self.__repopulate_voice_players)

	@logutils.trace_call(logger)
	def deinitialize(self):
		pass

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "General":
			if name == "speak_stop_delay":
				self.__speak_stop_delay = value

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsMixin.
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
	def has_player_model(self, name):
		"""
		Implemented from PlayerModelProvider.
		"""
		return name == "voice"

	@logutils.trace_call(logger)
	def get_player_model(self, name):
		"""
		Implemented from PlayerModelProvider.
		"""
		if self.has_player_model(name):
			return self.__model_proxy

	@logutils.trace_call(logger)
	def __on_user_added(self, user):
		self.__delayed_user_speak_states[user["id"]] = user["is_speaking"]
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_modified(self, old_user, new_user):
		id = new_user["id"]
		if old_user["is_speaking"] != new_user["is_speaking"] and id in self.__pairing_model:
			if id in self.__user_speak_state_timers:
				BigWorld.cancelCallback(self.__user_speak_state_timers.pop(id))
			if new_user["is_speaking"]:
				self.__delayed_user_speak_states[id] = True
			else:
				self.__user_speak_state_timers[id] = BigWorld.callback(self.__speak_stop_delay,
					functools.partial(self.__on_delayed_speak_stop, id))
			self.__repopulate_voice_players()

	def __on_delayed_speak_stop(self, id):
		if id in self.__delayed_user_speak_states:
			self.__delayed_user_speak_states[id] = False
		self.__user_speak_state_timers.pop(id, None)
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_removed(self, user):
		self.__delayed_user_speak_states.pop(user["id"], None)
		self.__user_speak_state_timers.pop(user["id"], None)
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __repopulate_voice_players(self, *args, **kwargs):
		pairs = reduce(self.__pairings_to_pairs, self.__pairing_model.itervalues(), [])
		pairs = reduce(self.__add_model_data_to_pairs, pairs, [])
		players = reduce(self.__combine_pairs, pairs, {})
		self.__model.set_all(players.values())

	def __pairings_to_pairs(self, results, pairing):
		return results + [(pairing["id"], player_id) for player_id in pairing["player_ids"]]

	def __add_model_data_to_pairs(self, results, pair):
		player = self.__all_player_model.get(pair[1])
		if player:
			speaking = self.__delayed_user_speak_states.get(pair[0], False)
			results.append((speaking, player))
		return results

	def __combine_pairs(self, players, pair):
		speaking, player = pair
		if player["id"] not in players:
			players[player["id"]] = {
				"id": player["id"],
				"name": player["name"],
				"speaking": False
			}
		players[player["id"]]["speaking"] |= speaking
		return players
