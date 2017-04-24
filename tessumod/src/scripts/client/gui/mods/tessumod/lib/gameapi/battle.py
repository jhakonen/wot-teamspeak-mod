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
This module notifies listeners when battle starts, finishes, and replay starts.

Emits following events:
 - battle_started:        when battle has started
 - battle_finished:       when battle has finished
 - battle_replay_started: when replay file playback is started
"""

from __future__ import absolute_import

import BigWorld
from PlayerEvents import g_playerEvents
from BattleReplay import BattleReplay

from .hookutils import hook_method
from .. import logutils

logger = logutils.logger.getChild("gameapi")

_events = None

def init(events):
	global _events
	_events = events
	g_playerEvents.onAvatarBecomePlayer += _on_avatar_become_player
	g_playerEvents.onAvatarBecomeNonPlayer += _on_avatar_become_non_player

def deinit():
	g_playerEvents.onAvatarBecomePlayer -= _on_avatar_become_player
	g_playerEvents.onAvatarBecomeNonPlayer -= _on_avatar_become_non_player

def get_camera_position():
	vector = BigWorld.camera().position
	return (vector.x, vector.y, vector.z)

def get_camera_direction():
	vector = BigWorld.camera().direction
	return (vector.x, vector.y, vector.z)

def get_vehicle_position(vehicle_id):
	entity = BigWorld.entities.get(vehicle_id)
	if not entity:
		return None
	vector = entity.position
	return (vector.x, vector.y, vector.z)

@logutils.trace_call(logger)
def _on_avatar_become_player():
	_events.emit("battle_started")

@logutils.trace_call(logger)
def _on_avatar_become_non_player():
	_events.emit("battle_finished")

@hook_method(BattleReplay, "play")
def _play(self, fileName=None):
	_events.emit("battle_replay_started")
