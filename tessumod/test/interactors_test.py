# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2016  Janne Hakonen
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

import random
import re
import mock
import copy

import helpers
from tessumod import interactors
from tessumod.constants import SettingConstants

class TestInteractorsPairChatUserToPlayer(object):

	def setUp(self):
		self.__client_id = (1, 1)
		self.__channel_id = 2
		self.__chat_clients = {}
		self.__settings_data = {
			SettingConstants.NICK_MAPPINGS: {},
			SettingConstants.NICK_EXTRACT_PATTERNS: [],
			SettingConstants.CHAT_NICK_SEARCH_ENABLED: False,
			SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT: False
		}

		self.__interactor = interactors.PairChatUserToPlayer()

		self.__interactor.usercache = mock.Mock()
		self.__interactor.usercache.get_paired_player_ids.return_value = []
		self.__interactor.chatclient = mock.Mock()
		self.__interactor.chatclient.has_user.side_effect = lambda client_id: client_id in self.__chat_clients
		self.__interactor.chatclient.get_user.side_effect = self.__get_chat_client
		self.__interactor.chatclient.get_current_channel_id.return_value = self.__channel_id
		self.__interactor.players = mock.Mock()
		self.__interactor.settings = mock.Mock()
		self.__interactor.settings.get.side_effect = lambda key: self.__settings_data[key]

	def __get_chat_client(self, client_id):
		client = copy.copy(self.__chat_clients[client_id])
		client["client_id"] = client_id
		return client

	def test_matches_using_metadata(self):
		self.__settings_data[SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT] = True
		self.__interactor.players.get_players.return_value = [dict(name="TestTomato", id=1000)]
		self.__chat_clients[self.__client_id] = dict(
			nick="TestDummy",
			game_nick="TestTomato",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1000, name="TestTomato")
		self.__interactor.usercache.pair.assert_called_with(1000, "deadf00d")

	def test_matches_same_names_case_insensitive(self):
		self.__interactor.players.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_clients[self.__client_id] = dict(
			nick="TestTomato",
			game_nick="",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__interactor.usercache.pair.assert_called_with(1001, "deadf00d")

	def test_extracts_nick_using_regexp_patterns(self):
		self.__settings_data[SettingConstants.NICK_EXTRACT_PATTERNS] = [re.compile(r"\[[^\]]+\]\s*([a-z0-9_]+)", re.IGNORECASE)]
		self.__interactor.players.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_clients[self.__client_id] = dict(
			nick="[T-BAD] TestTomato",
			game_nick="",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__interactor.usercache.pair.assert_called_with(1001, "deadf00d")

	def test_matches_using_mappings(self):
		self.__interactor.players.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato123", id=1001)]
		self.__settings_data[SettingConstants.NICK_MAPPINGS] = dict(matti="TESTtomato123")
		self.__chat_clients[self.__client_id] = dict(
			nick="Matti",
			game_nick="",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1001, name="TESTtomato123")
		self.__interactor.usercache.pair.assert_called_with(1001, "deadf00d")

	def test_matches_using_both_patterns_and_mappings(self):
		self.__interactor.players.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato123", id=1001)]
		self.__settings_data[SettingConstants.NICK_EXTRACT_PATTERNS] = [re.compile(r"\[[^\]]+\]\s*([a-z0-9_]+)", re.IGNORECASE)]
		self.__settings_data[SettingConstants.NICK_MAPPINGS] = dict(matti="TESTtomato123")
		self.__chat_clients[self.__client_id] = dict(
			nick="[T-BAD] Matti",
			game_nick="",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1001, name="TESTtomato123")
		self.__interactor.usercache.pair.assert_called_with(1001, "deadf00d")

	def test_searches_players_from_ts_name(self):
		self.__settings_data[SettingConstants.CHAT_NICK_SEARCH_ENABLED] = True
		self.__interactor.players.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_clients[self.__client_id] = dict(
			nick="[T-BAD] TestTomato",
			game_nick="",
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		)
		self.__interactor.execute(client_id=self.__client_id)
		self.__interactor.usercache.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__interactor.usercache.pair.assert_called_with(1001, "deadf00d")
