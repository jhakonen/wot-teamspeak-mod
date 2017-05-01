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
added, modified, or removed from battlefield.

Emits following events through given "events" object:
 - battle_player_added:    when player is added to battlefield
 - battle_player_modified: when player's vehicle is killed
 - battle_player_removed:  when battle ends and players are removed

Each event has a dict argument which has following keys and values:
 - id:         player's ID (int)
 - name:       player's name (str)
 - vehicle_id: player's vehicle ID (int)
 - is_alive:   is player alive (bool)
"""

from __future__ import absolute_import
from copy import copy

import BigWorld
from PlayerEvents import g_playerEvents
from .. import logutils

logger = logutils.logger.getChild("gameapi")

_events = None
_players = {}

def init(events):
	global _events
	_events = events
	g_playerEvents.onAvatarBecomePlayer += _on_avatar_become_player
	g_playerEvents.onAvatarBecomeNonPlayer += _on_avatar_become_non_player

def deinit():
	g_playerEvents.onAvatarBecomePlayer -= _on_avatar_become_player
	g_playerEvents.onAvatarBecomeNonPlayer -= _on_avatar_become_non_player

def _arena():
	arena = BigWorld.player().arena
	if not arena:
		raise RuntimeError("Arena does not exist")
	return arena

@logutils.trace_call(logger)
def _on_avatar_become_player():
	arena = _arena()
	arena.onNewVehicleListReceived += _on_new_vehicle_list_received
	arena.onVehicleAdded += _on_vehicle_added
	arena.onVehicleKilled += _on_vehicle_killed

@logutils.trace_call(logger)
def _on_avatar_become_non_player():
	for vehicle_id in _players.keys():
		player = _players.pop(vehicle_id)
		_events.emit("battle_player_removed", copy(player))

@logutils.trace_call(logger)
def _on_new_vehicle_list_received():
	for vehicle_id, vehicle in _arena().vehicles.iteritems():
		player = _players[vehicle_id] = {
			"id":         int(vehicle["accountDBID"]),
			"name":       str(vehicle["name"]),
			"vehicle_id": int(vehicle_id),
			"is_alive":   True
		}
		_events.emit("battle_player_added", player)

@logutils.trace_call(logger)
def _on_vehicle_added(vehicle_id):
	vehicle = _arena().vehicles[vehicle_id]
	player = _players[vehicle_id] = {
		"id":         int(vehicle["accountDBID"]),
		"name":       str(vehicle["name"]),
		"vehicle_id": int(vehicle_id),
		"is_alive":   True
	}
	_events.emit("battle_player_added", copy(player))

@logutils.trace_call(logger)
def _on_vehicle_killed(vehicle_id, *args, **kwargs):
	_players[vehicle_id]["is_alive"] = False
	_events.emit("battle_player_modified", copy(_players[vehicle_id]))
