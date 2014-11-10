import os
import sys
import ConfigParser

base_path = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.join(base_path, "..", "..", "..", "features", "helpers", "fakes")
tmp_path = os.path.join(base_path, "..", "..", "..", "tmp")
ini_path = os.path.join(tmp_path, "tessu_mod_cache.ini")

sys.path.append(fakes_path)
from user_cache import UserCache

def get_cache_value(section, name):
	parser = ConfigParser.RawConfigParser()
	parser.read([ini_path])
	return parser.get(section, name)

def has_cache_value(section, name):
	parser = ConfigParser.RawConfigParser()
	parser.read([ini_path])
	return parser.has_option(section, name)

class TestUserCache(object):

	def setUp(self):
		self.cache = UserCache(ini_path)

	def tearDown(self):
		os.remove(ini_path)

	def test_can_add_ts_user(self):
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.sync()
		assert get_cache_value("TeamSpeakUsers", "erkki") == "asaZjcw/gfebE/PM="

	def test_can_add_player(self):
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.sync()
		assert get_cache_value("GamePlayers", "erkkituhoaja") == "1234567"

	def test_can_pair(self):
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.pair(1234567, "asaZjcw/gfebE/PM=")
		self.cache.sync()
		assert get_cache_value("UserPlayerPairings", "erkki") == "erkkituhoaja"

	def test_can_get_pairing(self):
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.pair(1234567, "asaZjcw/gfebE/PM=")
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_get_two_paired_players_for_one_ts_user(self):
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.add_player("Watnao", 4897346)
		self.cache.pair(1234567, "asaZjcw/gfebE/PM=")
		self.cache.pair(4897346, "asaZjcw/gfebE/PM=")
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 4897346 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_get_two_paired_ts_users_for_one_player(self):
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.add_ts_user("Matti", "adfZjcw/gffbE/FO=")
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.pair(1234567, "asaZjcw/gfebE/PM=")
		self.cache.pair(1234567, "adfZjcw/gffbE/FO=")
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 1234567 in self.cache.get_paired_player_ids("adfZjcw/gffbE/FO=")

	def test_disabling_cache_write_does_not_sync_to_file(self):
		self.cache.is_write_enabled = False
		self.cache.add_ts_user("Erkki", "asaZjcw/gfebE/PM=")
		self.cache.add_player("ErkkiTuhoaja", 1234567)
		self.cache.pair(1234567, "asaZjcw/gfebE/PM=")
		self.cache.sync()
		assert not has_cache_value("TeamSpeakUsers", "Erkki")
		assert not has_cache_value("GamePlayers", "ErkkiTuhoaja")
		assert not has_cache_value("UserPlayerPairings", "Erkki")
