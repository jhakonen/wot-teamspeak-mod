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

from gui.mods.tessumod import plugintypes, logutils, models
from gui.mods.tessumod.models import g_player_model, g_user_model, g_pairing_model, PlayerItem

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
	plugintypes.SettingsUIProvider):
	"""
	This plugin ...
	"""

	NS = "voice"

	def __init__(self):
		super(PlayerSpeaking, self).__init__()
		self.__speak_stop_delay = 0
		self.__user_speak_state_timers = {}
		self.__delayed_user_speak_states = {}
		g_player_model.add_namespace(self.NS)

	@logutils.trace_call(logger)
	def initialize(self):
		g_player_model.on('added', self.__repopulate_voice_players)
		g_player_model.on('removed', self.__repopulate_voice_players)
		user_model = models.FilterModel(g_user_model)
		user_model.add_filter(lambda user: user.my_channel)
		user_model.on("added", self.__on_user_added)
		user_model.on("modified", self.__on_user_modified)
		user_model.on("removed", self.__on_user_removed)
		g_pairing_model.on('added', self.__repopulate_voice_players)
		g_pairing_model.on("modified", self.__repopulate_voice_players)
		g_pairing_model.on('removed', self.__repopulate_voice_players)

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
	def __on_user_added(self, user):
		self.__delayed_user_speak_states[user.id] = user.is_speaking
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_modified(self, old_user, new_user):
		id = new_user.id
		if old_user.is_speaking != new_user.is_speaking and id in g_pairing_model:
			if id in self.__user_speak_state_timers:
				BigWorld.cancelCallback(self.__user_speak_state_timers.pop(id))
			if new_user.is_speaking:
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
		self.__delayed_user_speak_states.pop(user.id, None)
		self.__user_speak_state_timers.pop(user.id, None)
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __repopulate_voice_players(self, *args, **kwargs):
		pairs = reduce(self.__pairings_to_pairs, g_pairing_model.itervalues(), [])
		pairs = reduce(self.__add_model_data_to_pairs, pairs, [])
		players = reduce(self.__combine_pairs, pairs, {})
		g_player_model.set_all(self.NS, players.values())

	def __pairings_to_pairs(self, results, pairing):
		return results + [(pairing.id, player_id) for player_id in pairing.player_ids]

	def __add_model_data_to_pairs(self, results, pair):
		player = g_player_model.get(pair[1])
		if player:
			speaking = self.__delayed_user_speak_states.get(pair[0], False)
			results.append((speaking, player))
		return results

	def __combine_pairs(self, players, pair):
		speaking, player = pair
		players[player.id] = PlayerItem(
			id = player.id,
			speaking = (speaking or players[player.id].speaking) if player.id in players else speaking
		)
		return players
