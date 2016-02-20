# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2015  Janne Hakonen
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

import copy
import collections
import entities

class ChatUserRepository(collections.Iterable):

	def __init__(self):
		self.__entities = {}

	def has(self, client_id):
		return client_id in self.__entities

	def get(self, client_id):
		return copy.copy(self.__entities.get(client_id))

	def set(self, user):
		self.__entities[user.client_id] = user
		return user

	def remove(self, client_id):
		del self.__entities[client_id]

	def __iter__(self):
		return self.__entities.itervalues()

class VehicleRepository(object):

	def __init__(self, battle):
		self.__battle = battle
		self.__entities = {}

	def get(self, player_id):
		vehicle_id = self.__battle.find_vehicle_id(lambda v: v["accountDBID"] == player_id)
		if vehicle_id is None:
			return None
		vehicle = self.__battle.get_vehicle(vehicle_id)
		return entities.Vehicle(repository=self, vehicle_id=vehicle_id, is_alive=vehicle["isAlive"])

	def get_vehicle_position(self, vehicle_id):
		entity = self.__battle.get_entity(vehicle_id)
		if entity:
			return (entity.position.x, entity.position.y, entity.position.z)

class KeyValueRepository(object):

	def __init__(self, engine):
		self.__entities = engine

	def get(self, name):
		return copy.copy(self.__entities.get(name))

	def set(self, name, value):
		self.__entities[name] = value
		return value
