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

from lib.littletable.littletable import Table
from collections import Mapping

class DictDataObject(Mapping):
	def __init__(self, data):
		self.__data = data

	def __repr__(self):
		return repr(self.__data)

	def __getattr__(self, name):
		try:
			return self.__data[name.replace('_', '-')]
		except KeyError, e:
			raise AttributeError(e)

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

battle_players = Table('battle_players')
battle_players.create_index('id', unique=True)

prebattle_players = Table('prebattle_players')
prebattle_players.create_index('id', unique=True)

speaking_players = Table('speaking_players')
speaking_players.create_index('id', unique=True)

vehicles = Table('vehicles')
vehicles.create_index('id', unique=True)

users = Table('users')
users.create_index('id', unique=True)

cached_users = Table('cached_users')
cached_users.create_index('unique_id', unique=True)

cached_players = Table('cached_players')
cached_players.create_index('id', unique=True)

pairings = Table('pairings')
pairings.create_index('player_id')
pairings.create_index('user_unique_id')
