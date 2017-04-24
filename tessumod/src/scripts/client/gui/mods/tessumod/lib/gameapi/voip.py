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

from __future__ import absolute_import
from messenger.proto.events import g_messengerEvents
from VOIP.VOIPManager import VOIPManager

from .hookutils import hook_method, CALL_WITH_ORIGINAL
from .. import logutils

logger = logutils.logger.getChild("gameapi")

_speak_states = {}

@logutils.trace_call(logger)
def set_player_speaking(player_id, speaking):
	_speak_states[player_id] = speaking
	g_messengerEvents.voip.onPlayerSpeaking(player_id, speaking)

@hook_method(VOIPManager, "isParticipantTalking", call_style=CALL_WITH_ORIGINAL)
def _isParticipantTalking(original, self, dbid):
	return _speak_states.get(dbid, False) or original(self, dbid)
