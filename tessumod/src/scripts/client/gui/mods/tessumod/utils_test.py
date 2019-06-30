# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
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

import os
import sys
base_path  = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.realpath(os.path.join(base_path, "..", "..", "..", "..", "..", "..", "..", "futes", "fakes"))
tmp_path   = os.path.realpath(os.path.join(base_path, "..", "..", "..", "..", "..", "..", "..", "tmp"))
sys.path.append(fakes_path)
import utils
import ts3
import random
import re
import mock

class TestUtilsTSUserToPlayer(object):

	def setUp(self):
		pass

	def create_ts_user(self, nick=None, wot_nick=None):
		ts_user = ts3.User(mock.Mock())
		ts_user.nick = nick
		ts_user.wot_nick = wot_nick
		return ts_user

	def create_players(self, *nicks):
		for nick in nicks:
			yield utils.Player(nick, random.uniform(0, 999999999))

	def create_patterns(self, *patterns):
		for pattern in patterns:
			yield re.compile(pattern, re.IGNORECASE)

	def test_matches_using_metadata(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="TestDummy", wot_nick="TestTomato"),
			players = self.create_players("TestDummy", "TestTomato"),
			use_metadata = True
		)
		assert player is not None
		assert player.name == "TestTomato"

	def test_matches_same_names_case_insensitive(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="TestTomato"),
			players = self.create_players("TestDummy", "TESTtomato")
		)
		assert player is not None
		assert player.name == "TESTtomato"

	def test_extracts_nick_using_regexp_patterns(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="[T-BAD] TestTomato"),
			players = self.create_players("TestDummy", "TESTtomato"),
			extract_patterns = self.create_patterns(r"\[[^\]]+\]\s*([a-z0-9_]+)")
		)
		assert player is not None
		assert player.name == "TESTtomato"

	def test_matches_using_mappings(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="TestTomato"),
			players = self.create_players("TestDummy", "TESTtomato123"),
			mappings = dict(testtomato="testtomato123")
		)
		assert player is not None
		assert player.name == "TESTtomato123"

	def test_matches_using_both_patterns_and_mappings(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="[T-BAD] TestTomato"),
			players = self.create_players("TestDummy", "TESTtomato123"),
			extract_patterns = self.create_patterns(r"\[[^\]]+\]\s*([a-z0-9_]+)"),
			mappings = dict(testtomato="testtomato123")
		)
		assert player is not None
		assert player.name == "TESTtomato123"

	def test_searches_players_from_ts_name(self):
		player = utils.ts_user_to_player(
			ts_user = self.create_ts_user(nick="[T-BAD] TestTomato"),
			players = self.create_players("TestDummy", "TESTtomato"),
			use_ts_nick_search = True
		)
		assert player is not None
		assert player.name == "TESTtomato"
