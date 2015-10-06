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

class PositionalData(object):

	def __init__(self):
		self.camera_position = None
		self.camera_direction = None
		self.client_positions = {}

class Vector(object):

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

class TeamSpeakUser(object):

	def __init__(self):
		self.nick = None
		self.wot_nick = None
		self.client_id = None
		self.unique_id = None
		self.channel_id = None
		self.speaking = False

	def __hash__(self):
		return (
			hash(self.client_id) ^
			hash(self.nick) ^
			hash(self.wot_nick) ^
			hash(self.unique_id) ^
			hash(self.channel_id)
		)

	def __eq__(self, other):
		return hash(self) == hash(other)

	def __repr__(self):
		return "TeamSpeakUser(client_id={0}, nick={1}, wot_nick={2}, unique_id={3}, channel_id={4}, speaking={5})".format(
			repr(self.client_id),
			repr(self.nick),
			repr(self.wot_nick),
			repr(self.unique_id),
			repr(self.channel_id),
			repr(self.speaking)
		)

class GamePlayer(object):

	def __init__(self, name, id):
		self._name = name
		self._id = id

	@property
	def name(self):
		return self._name

	@property
	def id(self):
		return self._id

	def __repr__(self):
		return "GamePlayer(name={0}, id={1})".format(self._name, self._id)
