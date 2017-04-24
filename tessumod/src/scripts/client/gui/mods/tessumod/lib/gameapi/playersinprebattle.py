# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

"""
This module listens for game events and notifies listeners when players are
added, or removed from prebattle (like platoon, training room, team battle
room, etc...).

Emits following events through given "events" object:
 - prebattle_player_added:   when player joins the prebattle
 - prebattle_player_removed: when player leaves the prebattle

Each event has a dict argument which has following keys and values:
 - id:   player's ID (int)
 - name: player's name (str)
"""

from __future__ import absolute_import
from copy import copy

from gui.prb_control.dispatcher import _PrbControlLoader
from gui.prb_control.entities.listener import IGlobalListener

from .hookutils import hook_method
from .. import logutils

logger = logutils.logger.getChild("gameapi")

_notifier = None

def init(events):
	global _notifier
	_notifier = PlayersInPrebattleNotifier(events)

def deinit():
	_notifier.stopGlobalListening()

@hook_method(_PrbControlLoader, "onAccountShowGUI")
def _onAccountShowGUI(self, ctx):
	_notifier.startGlobalListening()

class PlayersInPrebattleNotifier(IGlobalListener):

	def __init__(self, events):
		"""Constructor.
		:param events: EventEmitter object
		"""
		self.__events = events
		self.__players = {}

	@logutils.trace_call(logger)
	def onPrbEntitySwitching(self):
		for player_id in self.__players.keys():
			self.__remove_player(player_id)

	@logutils.trace_call(logger)
	def onPrbEntitySwitched(self):
		if hasattr(self.prbEntity, "getPlayers"):
			for player_info in self.prbEntity.getPlayers().itervalues():
				self.__add_player(player_info)

	@logutils.trace_call(logger)
	def onPlayerAdded(self, entity, playerInfo):
		"""Called at least in Training Room when player is joins."""
		self.__add_player(playerInfo)

	@logutils.trace_call(logger)
	def onPlayerRemoved(self, entity, playerInfo):
		"""Called at least in Training Room when player is leaves."""
		self.__remove_player(playerInfo.dbID)

	@logutils.trace_call(logger)
	def onUnitPlayerAdded(self, pInfo):
		"""Called at least in Platoon when a player joins."""
		self.__add_player(pInfo)

	@logutils.trace_call(logger)
	def onUnitPlayerRemoved(self, pInfo):
		"""Called at least in Platoon when a player leaves."""
		self.__remove_player(pInfo.dbID)

	def __add_player(self, player_info):
		player = self.__players[player_info.dbID] = {
			"id":   int(player_info.dbID),
			"name": str(player_info.name)
		}
		self.__events.emit("prebattle_player_added", copy(player))

	def __remove_player(self, player_id):
		self.__events.emit("prebattle_player_removed", self.__players.pop(player_id))
