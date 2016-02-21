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

import helpers
from tessumod import boundaries, repositories
from tessumod.constants import SettingConstants
from tessumod import entities

class TestInteractorsPairChatUserToPlayer(object):

	def setUp(self):
		self.__user_cache_api = mock.Mock()
		self.__chat_client_api = mock.Mock()
		self.__player_api = mock.Mock()
		self.__settings_api = mock.Mock()
		self.__settings_api.get.side_effect = lambda key: self.__settings[key]
		self.__chat_user_repository = repositories.ChatUserRepository()
		boundaries.provide_dependency("user_cache_api",         self.__user_cache_api)
		boundaries.provide_dependency("chat_client_api",        self.__chat_client_api)
		boundaries.provide_dependency("player_api",             self.__player_api)
		boundaries.provide_dependency("settings_api",           self.__settings_api)
		boundaries.provide_dependency("chat_user_repository",   self.__chat_user_repository)
		self.__settings = {
			SettingConstants.NICK_MAPPINGS: {},
			SettingConstants.NICK_EXTRACT_PATTERNS: [],
			SettingConstants.CHAT_NICK_SEARCH_ENABLED: False,
			SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT: False
		}
		self.__user_cache_api.get_paired_player_ids.return_value = []
		self.__channel_id = 2
		self.__chat_client_api.get_current_channel_id.return_value = self.__channel_id

	def create_players(self, *nicks):
		for nick in nicks:
			yield dict(name=nick, id=random.uniform(0, 999999999))

	def create_patterns(self, *patterns):
		for pattern in patterns:
			yield re.compile(pattern, re.IGNORECASE)

	def test_matches_using_metadata(self):
		self.__settings[SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT] = True
		self.__player_api.get_players.return_value = [dict(name="TestTomato", id=1000)]
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="TestDummy",
			game_nick="TestTomato",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1000, name="TestTomato")
		self.__user_cache_api.pair.assert_called_with(1000, "deadf00d")

	def test_matches_same_names_case_insensitive(self):
		self.__player_api.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="TestTomato",
			game_nick="",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__user_cache_api.pair.assert_called_with(1001, "deadf00d")

	def test_extracts_nick_using_regexp_patterns(self):
		self.__settings[SettingConstants.NICK_EXTRACT_PATTERNS] = [re.compile(r"\[[^\]]+\]\s*([a-z0-9_]+)", re.IGNORECASE)]
		self.__player_api.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="[T-BAD] TestTomato",
			game_nick="",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__user_cache_api.pair.assert_called_with(1001, "deadf00d")

	def test_matches_using_mappings(self):
		self.__player_api.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato123", id=1001)]
		self.__settings[SettingConstants.NICK_MAPPINGS] = dict(matti="TESTtomato123")
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="Matti",
			game_nick="",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1001, name="TESTtomato123")
		self.__user_cache_api.pair.assert_called_with(1001, "deadf00d")

	def test_matches_using_both_patterns_and_mappings(self):
		self.__player_api.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato123", id=1001)]
		self.__settings[SettingConstants.NICK_EXTRACT_PATTERNS] = [re.compile(r"\[[^\]]+\]\s*([a-z0-9_]+)", re.IGNORECASE)]
		self.__settings[SettingConstants.NICK_MAPPINGS] = dict(matti="TESTtomato123")
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="[T-BAD] Matti",
			game_nick="",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1001, name="TESTtomato123")
		self.__user_cache_api.pair.assert_called_with(1001, "deadf00d")

	def test_searches_players_from_ts_name(self):
		self.__settings[SettingConstants.CHAT_NICK_SEARCH_ENABLED] = True
		self.__player_api.get_players.return_value = [dict(name="TestDummy", id=1000), dict(name="TESTtomato", id=1001)]
		self.__chat_user_repository.set(entities.ChatClientUser(
			nick="[T-BAD] TestTomato",
			game_nick="",
			client_id=0,
			unique_id="deadf00d",
			channel_id=self.__channel_id,
			speaking=True,
			is_me=False,
			in_my_channel=True
		))
		boundaries.usecase_pair_chat_user_to_player(client_id=0)
		self.__user_cache_api.add_player.assert_called_with(id=1001, name="TESTtomato")
		self.__user_cache_api.pair.assert_called_with(1001, "deadf00d")
