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
import re
from operator import or_

logger = logutils.logger.getChild("pairing")

class PlayerSpeaking(plugintypes.ModPlugin, plugintypes.PlayerNotificationsMixin,
	plugintypes.VoiceUserNotificationsMixin, plugintypes.UserMatchingMixin):
	"""
	This plugin ...
	"""

	def __init__(self):
		super(PlayerSpeaking, self).__init__()
		self.__source_to_model = {
			"battle": models.PlayerModel(),
			"prebattle": models.PlayerModel()
		}
		self.__all_player_model = models.CompositeModel(self.__source_to_model.values())
		self.__voice_user_model = models.PlayerModel()
		self.__voice_player_model = models.PlayerModel()
		self.__matches = {}

	@logutils.trace_call(logger)
	def initialize(self):
		pass

	@logutils.trace_call(logger)
	def deinitialize(self):
		pass

	@logutils.trace_call(logger)
	def on_player_added(self, source, player):
		"""
		Implemented from PlayerNotificationsMixin.
		"""
		if source in self.__source_to_model:
			self.__source_to_model[source].set(player)

	@logutils.trace_call(logger)
	def on_player_modified(self, source, player):
		"""
		Implemented from PlayerNotificationsMixin.
		"""
		if source in self.__source_to_model:
			self.__source_to_model[source].set(player)

	@logutils.trace_call(logger)
	def on_player_removed(self, source, player):
		"""
		Implemented from PlayerNotificationsMixin.
		"""
		if source in self.__source_to_model:
			self.__source_to_model[source].remove(player["id"])

	@logutils.trace_call(logger)
	def on_voice_user_added(self, new_user):
		"""
		Implemented from VoiceUserNotificationsMixin.
		"""
		self.__voice_user_model.set(new_user)

	@logutils.trace_call(logger)
	def on_voice_user_modified(self, old_user, new_user):
		"""
		Implemented from VoiceUserNotificationsMixin.
		"""
		self.__voice_user_model.set(new_user)
		if old_user["speaking"] != new_user["speaking"] and new_user["identity"] in self.__matches:
			self.__repopulate_voice_players()

	@logutils.trace_call(logger)
	def on_voice_user_removed(self, old_user):
		"""
		Implemented from VoiceUserNotificationsMixin.
		"""
		self.__voice_user_model.remove(old_user["id"])

	@logutils.trace_call(logger)
	def on_user_matched(self, user_identity, player_id):
		"""
		Implemented from UserMatchingMixin.
		"""
		self.__matches.setdefault(user_identity, set()).add(player_id)
		self.__repopulate_voice_players()

	def __repopulate_voice_players(self):
		pairs = reduce(self.__matches_to_pairs, self.__matches.iteritems(), [])
		pairs = reduce(self.__add_model_data_to_pairs, pairs, [])
		players = reduce(self.__combine_pairs, pairs, {})
		self.__voice_player_model.set_all(players.itervalues())

	def __matches_to_pairs(results, match):
		identity, player_ids = match
		for player_id in player_ids:
			results.append((identity, player_id))

	def __add_model_data_to_pairs(results, pair):
		player = self.__all_player_model.get(pair[1])
		if player:
			for user in self.__user_model:
				if user["identity"] == pair[0]:
					results.append((user, player))

	def __combine_pairs(players, pair):
		user, player = pair
		players.setdefault(player["id"], {
			"id": player["id"],
			"name": player["name"],
			"speaking": False
		})
		players[player["id"]]["speaking"] |= user["speaking"]

