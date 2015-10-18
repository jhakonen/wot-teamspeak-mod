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

class TeamSpeakUser(object):

	def __init__(self, nick, game_nick, client_id, unique_id, channel_id, speaking):
		self.__nick = nick
		self.__game_nick = game_nick
		self.__client_id = client_id
		self.__unique_id = unique_id
		self.__channel_id = channel_id
		self.__speaking = speaking

	@property
	def nick(self):
		return self.__nick

	@property
	def game_nick(self):
		return self.__game_nick

	@property
	def client_id(self):
		return self.__client_id

	@property
	def unique_id(self):
		return self.__unique_id

	@property
	def channel_id(self):
		return self.__channel_id

	@property
	def speaking(self):
		return self.__speaking

	def __hash__(self):
		return (
			hash(self.__client_id) ^
			hash(self.__nick) ^
			hash(self.__game_nick) ^
			hash(self.__unique_id) ^
			hash(self.__channel_id)
		)

	def __eq__(self, other):
		return hash(self) == hash(other)

	def __repr__(self):
		return "TeamSpeakUser(client_id={0}, nick={1}, wot_nick={2}, unique_id={3}, channel_id={4}, speaking={5})".format(
			repr(self.__client_id),
			repr(self.__nick),
			repr(self.__game_nick),
			repr(self.__unique_id),
			repr(self.__channel_id),
			repr(self.__speaking)
		)

class Vehicle(object):

	def __init__(self, repository, vehicle_id, is_alive):
		self.__repository = repository
		self.__id = vehicle_id
		self.__is_alive = is_alive

	@property
	def id(self):
		return self.__id

	@property
	def is_alive(self):
		return self.__is_alive

	@property
	def position(self):
		return self.__repository.get_vehicle_position(self.__id)

	def __repr__(self):
		return "Vehicle(id={0}, is_alive={1}, position={2})".format(
			self.id,
			self.is_alive,
			self.position
		)
