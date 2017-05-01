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
This module listens for game events to determine my own player ID.
Emits "my_player_received" event with player ID as int when available.

The event has a dict argument which has following keys and values:
 - id:         player's ID (int)
 - name:       player's name (str)
"""

from __future__ import absolute_import
import BigWorld
from messenger.storage import storage_getter
from PlayerEvents import g_playerEvents

from .. import logutils

logger = logutils.logger.getChild("gameapi")

_events = None

@storage_getter('users')
def users_storage(self):
	return None

def init(events):
	global _events
	_events = events
	g_playerEvents.onAccountShowGUI += _on_account_show_gui
	g_playerEvents.onAvatarReady += _on_avatar_ready

def deinit():
	g_playerEvents.onAccountShowGUI -= _on_account_show_gui
	g_playerEvents.onAvatarReady -= _on_avatar_ready

@logutils.trace_call(logger)
def _on_account_show_gui(ctx):
	# databaseID is set when GUI is shown and will be available before
	# onAccountShowGUI() is called
	_events.emit("my_player_received", {
		"id": int(BigWorld.player().databaseID),
		"name": users_storage.getUser(BigWorld.player().databaseID)
	})

@logutils.trace_call(logger)
def _on_avatar_ready():
	vehicle_id = int(BigWorld.player().playerVehicleID)
	vehicle = BigWorld.player().arena.vehicles[vehicle_id]
	_events.emit("my_player_received", {
		"id": int(vehicle["accountDBID"]),
		"name": vehicle["name"]
	})
