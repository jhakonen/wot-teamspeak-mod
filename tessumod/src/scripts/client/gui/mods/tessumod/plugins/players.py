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

from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.messages import (PlayerMeMessage, BattlePlayerMessage,
	VehicleMessage, PrebattlePlayerMessage)
from gui.mods.tessumod.plugintypes import Plugin, EntityProvider

from copy import copy

logger = logutils.logger.getChild("players")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return PlayersPlugin()

class PlayersPlugin(Plugin, EntityProvider):
	"""
	This plugin provides models of players for other plugins.
	"""

	NS_ME = "me"
	NS_BATTLE = "battle"
	NS_PREBATTLE = "prebattle"

	def __init__(self):
		super(PlayersPlugin, self).__init__()
		self.__battle_players = {}
		self.__prebattle_players = {}
		self.__vehicles = {}
		self.__is_me = {}


	@logutils.trace_call(logger)
	def initialize(self):
		gameapi.events.on("my_player_received", self.__on_my_player_received)
		gameapi.events.on("battle_player_added", self.__on_battle_player_added)
		gameapi.events.on("battle_player_modified", self.__on_battle_player_modified)
		gameapi.events.on("battle_player_removed", self.__on_battle_player_removed)
		gameapi.events.on("prebattle_player_added", self.__on_prebattle_player_added)
		gameapi.events.on("prebattle_player_removed", self.__on_prebattle_player_removed)

	@logutils.trace_call(logger)
	def deinitialize(self):
		gameapi.events.off("my_player_received", self.__on_my_player_received)
		gameapi.events.off("battle_player_added", self.__on_battle_player_added)
		gameapi.events.off("battle_player_modified", self.__on_battle_player_modified)
		gameapi.events.off("battle_player_removed", self.__on_battle_player_removed)
		gameapi.events.off("prebattle_player_added", self.__on_prebattle_player_added)
		gameapi.events.off("prebattle_player_removed", self.__on_prebattle_player_removed)

	def has_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		return name in ["battle-players", "prebattle-players", "vehicles", "me-player"]

	def get_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		if name == "battle-players":
			return self.__battle_players.values()
		if name == "prebattle-players":
			return self.__prebattle_players.values()
		if name == "vehicles":
			return self.__vehicles.values()
		if name == "me-player":
			return [self.__is_me] if self.__is_me else []

	@logutils.trace_call(logger)
	def __on_my_player_received(self, player):
		self.__is_me = self.__to_internal_player(player)
		self.messages.publish(PlayerMeMessage("added", copy(self.__is_me)))

	@logutils.trace_call(logger)
	def __on_battle_player_added(self, player):
		self.__battle_players[player["id"]] = self.__to_internal_player(player)
		self.__vehicles[player["vehicle_id"]] = self.__to_internal_vehicle(player)
		self.messages.publish(BattlePlayerMessage("added", copy(self.__battle_players[player["id"]])))
		self.messages.publish(VehicleMessage("added", copy(self.__vehicles[player["vehicle_id"]])))

	@logutils.trace_call(logger)
	def __on_battle_player_modified(self, player):
		self.__vehicles[player["vehicle_id"]] = self.__to_internal_vehicle(player)
		self.messages.publish(VehicleMessage("modified", copy(self.__vehicles[player["vehicle_id"]])))

	@logutils.trace_call(logger)
	def __on_battle_player_removed(self, player):
		del self.__battle_players[player["id"]]
		del self.__vehicles[player["vehicle_id"]]
		self.messages.publish(BattlePlayerMessage("removed", self.__to_internal_player(player)))
		self.messages.publish(VehicleMessage("removed", self.__to_internal_vehicle(player)))

	@logutils.trace_call(logger)
	def __on_prebattle_player_added(self, player):
		self.__prebattle_players[player["id"]] = self.__to_internal_player(player)
		self.messages.publish(BattlePlayerMessage("added", copy(self.__prebattle_players[player["id"]])))

	@logutils.trace_call(logger)
	def __on_prebattle_player_removed(self, player):
		del self.__prebattle_players[player["id"]]
		self.messages.publish(BattlePlayerMessage("removed", self.__to_internal_player(player)))

	def __to_internal_player(self, player):
		return {"id": player["id"], "name": player["name"]}

	def __to_internal_vehicle(self, player):
		return {"id": player["vehicle_id"], "player-id": player["id"], "is-alive": player["is_alive"]}
