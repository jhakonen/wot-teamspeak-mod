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
