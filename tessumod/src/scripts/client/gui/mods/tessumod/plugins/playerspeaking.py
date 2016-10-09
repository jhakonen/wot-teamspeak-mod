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
from gui.mods.tessumod.models import g_player_model, g_user_model, g_pairing_model, PlayerItem, FilterModel

import functools
from itertools import ifilter, imap

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
		user_model = FilterModel(g_user_model)
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
		pairing_data_iter = iter(reduce(self.__reduce_to_pairing_data, g_pairing_model.itervalues(), []))
		pairing_data_iter = ifilter(self.__is_pairing_data_in_player_model, pairing_data_iter)
		pairing_data_iter = imap(self.__add_speaking_status, pairing_data_iter)
		player_data_iter = reduce(self.__combine_player_data, pairing_data_iter, {}).itervalues()
		player_item_iter = imap(self.__convert_to_player_items, player_data_iter)
		g_player_model.set_all(self.NS, player_item_iter)

	def __reduce_to_pairing_data(self, results, pairing):
		return results + [{ "user_id": pairing.id, "player_id": player_id } for player_id in pairing.player_ids]

	def __is_pairing_data_in_player_model(self, pairing_data):
		return pairing_data["player_id"] in g_player_model

	def __add_speaking_status(self, pairing_data):
		return dict(pairing_data, speaking=self.__delayed_user_speak_states.get(pairing_data["user_id"], False))

	def __combine_player_data(self, players, pairing_data):
		if pairing_data["player_id"] in players:
			player_data = dict(players[pairing_data["player_id"]])
			player_data["speaking"] |= pairing_data["speaking"]
			player_data["user_ids"].add(pairing_data["user_id"])
		else:
			player_data = {
				"id": pairing_data["player_id"],
				"user_ids": set([pairing_data["user_id"]]),
				"speaking": pairing_data["speaking"]
			}
		return dict(players, **{player_data["id"]: player_data})

	def __convert_to_player_items(self, player_data):
		return PlayerItem(
			id=player_data["id"],
			user_ids=list(player_data["user_ids"]),
			speaking=player_data["speaking"]
		)
