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
from .lib import pydash as _

import collections
import itertools

class _ItemBase(collections.Mapping):
	PARAMETERS = {}

	def __init__(self, parameters):
		for key, value in parameters.iteritems():
			assert key in self.PARAMETERS, "Invalid parameter: '%s'" % key
			assert isinstance(value, self.PARAMETERS[key]), \
				"Invalid value for key '%s': %s (type must be: %s)" % (key, value, self.PARAMETERS[key])
		assert set(self.PARAMETERS.keys()).issubset(set(parameters.keys())), \
			"Missing required keys: %s" % ", ".join(set(self.PARAMETERS.keys()) - set(parameters.keys()))
		self.__parameters = parameters

	def __getitem__(self, name):
		return self.__parameters[name]

	def __iter__(self):
		return iter(self.__parameters)

	def __len__(self):
		return len(self.__parameters)

class User(_ItemBase):
	PARAMETERS = {
		"id":         tuple,
		"name":       basestring,
		"game-name":  basestring,
		"unique-id":  basestring,
		"speaking":   bool,
		"is-me":      bool,
		"my-channel": bool
	}

class BattlePlayer(_ItemBase):
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class PrebattlePlayer(_ItemBase):
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class Vehicle(_ItemBase):
	PARAMETERS = {
		"id":        int,
		"player-id": int,
		"is-alive":  bool
	}

class Pairing(_ItemBase):
	PARAMETERS = {
		"player-id":      int,
		"user-unique-id": basestring
	}

class PlayerMe(_ItemBase):
	PARAMETERS = {
		"id":   int,
		"name": basestring
	}

class PlayerSpeaking(_ItemBase):
	PARAMETERS = {
		"id": int
	}

class UserMessage(messagepump.Message):
	ACTIONS = ("added", "modified", "removed")
	ITEM = User

class BattlePlayerMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	ITEM = BattlePlayer

class PrebattlePlayerMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	ITEM = PrebattlePlayer

class VehicleMessage(messagepump.Message):
	ACTIONS = ("added", "modified", "removed")
	ITEM = Vehicle

class PairingMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	ITEM = Pairing

class PlayerMeMessage(messagepump.Message):
	ACTIONS = ("added",)
	ITEM = PlayerMe

class PlayerSpeakingMessage(messagepump.Message):
	ACTIONS = ("added", "removed")
	ITEM = PlayerSpeaking
