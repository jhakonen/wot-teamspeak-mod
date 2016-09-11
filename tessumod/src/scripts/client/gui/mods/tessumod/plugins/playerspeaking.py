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

logger = logutils.logger.getChild("playerspeaking")

class PlayerSpeaking(plugintypes.ModPlugin, plugintypes.UserMatchingMixin,
	plugintypes.PlayerModelProvider):
	"""
	This plugin ...
	"""

	def __init__(self):
		super(PlayerSpeaking, self).__init__()
		self.__model = models.Model()
		self.__model_proxy = models.ImmutableModelProxy(self.__model)
		self.__matches = {}
		self.__all_player_model = None
		self.__user_model = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.__all_player_model = models.CompositeModel(
			pluginutils.get_player_models(self.plugin_manager, ["battle", "prebattle"]))
		self.__all_player_model.on('added', self.__on_player_added)
		self.__all_player_model.on('removed', self.__on_player_removed)

		for plugin_info in self.plugin_manager.getPluginsOfCategory("UserModelProvider"):
			if plugin_info.plugin_object.has_user_model():
				self.__user_model = plugin_info.plugin_object.get_user_model()

		self.__user_model.on("added", self.__on_user_added)
		self.__user_model.on("modified", self.__on_user_modified)
		self.__user_model.on("removed", self.__on_user_removed)

	@logutils.trace_call(logger)
	def deinitialize(self):
		pass

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
	def on_user_matched(self, user_identity, player_id):
		"""
		Implemented from UserMatchingMixin.
		"""
		self.__matches.setdefault(user_identity, set()).add(player_id)
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_player_added(self, player):
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_player_removed(self, player):
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_added(self, user):
		self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_modified(self, old_user, new_user):
		if old_user["is_speaking"] != new_user["is_speaking"] and new_user["identity"] in self.__matches:
			self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def __on_user_removed(self, user):
		self.__repopulate_voice_players()

	def __repopulate_voice_players(self):
		pairs = reduce(self.__matches_to_pairs, self.__matches.iteritems(), [])
		pairs = reduce(self.__add_model_data_to_pairs, pairs, [])
		players = reduce(self.__combine_pairs, pairs, {})
		logger.debug("PLAYERS: %s", repr(players.values()))
		self.__model.set_all(players.values())

	def __matches_to_pairs(self, results, match):
		identity, player_ids = match
		for player_id in player_ids:
			results.append((identity, player_id))
		return results

	def __add_model_data_to_pairs(self, results, pair):
		player = self.__all_player_model.get(pair[1])
		if player:
			for user in self.__user_model.itervalues():
				if user["identity"] == pair[0]:
					results.append((user, player))
		return results

	def __combine_pairs(self, players, pair):
		user, player = pair
		players.setdefault(player["id"], {
			"id": player["id"],
			"name": player["name"],
			"speaking": False
		})
		players[player["id"]]["speaking"] |= user["is_speaking"]
		return players

