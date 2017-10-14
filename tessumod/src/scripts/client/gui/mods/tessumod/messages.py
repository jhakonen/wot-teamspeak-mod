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

from .lib import messagepump

import pydash as _

import collections
import itertools

class UserMessage(messagepump.Message):
	ACTIONS = ("added", "modified", "removed")
	PARAMETERS = {
		"id":         tuple,
		"name":       basestring,
		"game_name":  basestring,
		"unique_id":  basestring,
		"speaking":   bool,
		"is_me":      bool,
		"my_channel": bool
	}

class BattlePlayerMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class PrebattlePlayerMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class VehicleMessage(messagepump.Message):
	ACTIONS = ("added", "modified", "removed")
	PARAMETERS = {
		"id":        int,
		"player_id": int,
		"is_alive":  bool
	}

class PairingMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	PARAMETERS = {
		"player_id":      int,
		"user_unique_id": basestring
	}

class PlayerMeMessage(messagepump.Message):
	ACTIONS = ("added",)
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class PlayerSpeakingMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	PARAMETERS = {
		"id": int
	}
