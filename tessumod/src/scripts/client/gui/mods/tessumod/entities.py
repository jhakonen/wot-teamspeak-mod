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

class ChatClientUser(object):

	def __init__(self, nick, game_nick, client_id, unique_id, channel_id, speaking, is_me, in_my_channel):
		self.__nick = nick
		self.__game_nick = game_nick
		self.__client_id = client_id
		self.__unique_id = unique_id
		self.__channel_id = channel_id
		self.__speaking = speaking
		self.__is_me = is_me
		self.__in_my_channel = in_my_channel

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

	@property
	def is_me(self):
		return self.__is_me

	@property
	def in_my_channel(self):
		return self.__in_my_channel

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
		return "ChatClientUser(client_id={0}, nick={1}, wot_nick={2}, unique_id={3}, channel_id={4}, speaking={5}, is_me={6}, in_my_channel={7})".format(
			repr(self.__client_id),
			repr(self.__nick),
			repr(self.__game_nick),
			repr(self.__unique_id),
			repr(self.__channel_id),
			repr(self.__speaking),
			repr(self.__is_me),
			repr(self.__in_my_channel)
		)
