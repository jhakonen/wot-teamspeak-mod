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
from gui.mods.tessumod.lib import pydash as _
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
			return database.battle_players.clone()
		if name == "prebattle-players":
			return database.prebattle_players.clone()
		if name == "vehicles":
			return database.vehicles.clone()
		if name == "me-player":
			return [self.__is_me] if self.__is_me else []

	@logutils.trace_call(logger)
	def __on_my_player_received(self, player):
		db_player = self.__to_internal_player(player)
		self.__is_me = db_player
		self.messages.publish(PlayerMeMessage("added", copy(db_player)))

	@logutils.trace_call(logger)
	def __on_battle_player_added(self, player):
		if not database.battle_players.where(id=player["id"]):
			new_player = self.__to_internal_player(player)
			database.battle_players.insert(new_player)
			self.messages.publish(BattlePlayerMessage("added", copy(new_player)))
		if not database.vehicles.where(id=player["vehicle_id"]):
			new_vehicle = self.__to_internal_vehicle(player)
			database.vehicles.insert(new_vehicle)
			self.messages.publish(VehicleMessage("added", copy(new_vehicle)))

	@logutils.trace_call(logger)
	def __on_battle_player_modified(self, player):
		if database.vehicles.delete(id=player["vehicle_id"]):
			new_vehicle = self.__to_internal_vehicle(player)
			database.vehicles.insert(new_vehicle)
			self.messages.publish(VehicleMessage("modified", copy(new_vehicle)))

	@logutils.trace_call(logger)
	def __on_battle_player_removed(self, player):
		old_player = _.head(database.battle_players.where(id=player["id"]))
		if old_player:
			database.battle_players.remove(old_player)
			self.messages.publish(BattlePlayerMessage("removed", old_player))
		old_vehicle = _.head(database.vehicles.where(id=player["vehicle_id"]))
		if old_vehicle:
			database.vehicles.remove(old_vehicle)
			self.messages.publish(VehicleMessage("removed", old_vehicle))

	@logutils.trace_call(logger)
	def __on_prebattle_player_added(self, player):
		if not database.prebattle_players.where(id=player["id"]):
			new_player = self.__to_internal_player(player)
			database.prebattle_players.insert(new_player)
			self.messages.publish(PrebattlePlayerMessage("added", copy(new_player)))

	@logutils.trace_call(logger)
	def __on_prebattle_player_removed(self, player):
		old_player = _.head(database.prebattle_players.where(id=player["id"]))
		if old_player:
			database.prebattle_players.remove(old_player)
			self.messages.publish(PrebattlePlayerMessage("removed", old_player))

	def __to_internal_player(self, player):
		return database.DictDataObject({"id": player["id"], "name": player["name"]})

	def __to_internal_vehicle(self, player):
		return database.DictDataObject({"id": player["vehicle_id"], "player-id": player["id"], "is-alive": player["is_alive"]})
