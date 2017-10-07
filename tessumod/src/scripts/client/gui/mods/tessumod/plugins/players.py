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
from gui.mods.tessumod.plugintypes import Plugin

logger = logutils.logger.getChild("players")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return PlayersPlugin()

class PlayersPlugin(Plugin):
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

	@logutils.trace_call(logger)
	def __on_my_player_received(self, player):
		database.set_me_player(**player)

	@logutils.trace_call(logger)
	def __on_battle_player_added(self, player):
		database.insert_battle_player(**_.pick(player, 'id', 'name'))
		database.insert_vehicle(id=player['vehicle_id'], player_id=player['id'], is_alive=player['is_alive'])

	@logutils.trace_call(logger)
	def __on_battle_player_modified(self, player):
		database.update_vehicle(id=player['vehicle_id'], player_id=player['id'], is_alive=player['is_alive'])

	@logutils.trace_call(logger)
	def __on_battle_player_removed(self, player):
		database.remove_battle_player(id=player['id'])
		database.remove_vehicle(id=player['vehicle_id'])

	@logutils.trace_call(logger)
	def __on_prebattle_player_added(self, player):
		database.insert_prebattle_player(**player)

	@logutils.trace_call(logger)
	def __on_prebattle_player_removed(self, player):
		database.remove_prebattle_player(id=player['id'])
