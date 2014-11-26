import os
import sys
base_path = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.join(base_path, "..", "..", "..", "features", "helpers", "fakes")
sys.path.append(fakes_path)
import utils
import ts3
import random
import re

class TestUtilsTSUserToPlayer(object):

	def setUp(self):
		pass

	def create_ts_user(self, nick=None, wot_nick=None):
		ts_user = ts3.User()
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
