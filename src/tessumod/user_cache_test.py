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
import ConfigParser

base_path  = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.realpath(os.path.join(base_path, "..", "..", "test", "fakes"))
tmp_path   = os.path.realpath(os.path.join(base_path, "..", "..", "tmp"))
ini_path   = os.path.join(tmp_path, "tessu_mod_cache.ini")

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
		try:
			os.makedirs(os.path.dirname(ini_path))
		except:
			pass
		try:
			os.remove(ini_path)
		except:
			pass

		self.cache = UserCache(ini_path)
		self.cache.on_read_error += self.set_error
		self.error_message = ""
		self.cache.init()

	def set_error(self, message):
		self.error_message = message

	def write_cache_file(self, contents):
		contents = "\n".join([line.strip() for line in contents.split("\n")])
		print contents
		with open(ini_path, "w") as file:
			file.write(contents)
		self.cache._ini_cache._sync_time = 0

	def get_cache_file_contents(self):
		with open(ini_path, "r") as file:
			return file.read()

	def assert_ini_contents_not_modified(self, orig_contents):
		assert orig_contents == self.get_cache_file_contents(), "INI-file has not been modifed"

	def test_can_read_pairings(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			erkki = asaZjcw/gfebE/PM=
			[GamePlayers]
			erkkituhoaja = 1234567
			[UserPlayerPairings]
			erkki = erkkituhoaja
		""")
		self.cache.sync()
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_read_multiple_players_paired_to_single_ts_user(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			erkki = asaZjcw/gfebE/PM=
			[GamePlayers]
			erkkituhoaja = 1234567
			watnao = 4897346
			[UserPlayerPairings]
			erkki = erkkituhoaja,watnao
		""")
		self.cache.sync()
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 4897346 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_read_multiple_ts_users_paired_to_single_player(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			erkki = asaZjcw/gfebE/PM=
			matti = adfZjcw/gffbE/FO=
			[GamePlayers]
			erkkituhoaja = 1234567
			[UserPlayerPairings]
			erkki = erkkituhoaja
			matti = erkkituhoaja
		""")
		self.cache.sync()
		assert 1234567 in self.cache.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 1234567 in self.cache.get_paired_player_ids("adfZjcw/gffbE/FO=")

	def test_error_received_on_missing_player_definition(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			erkki = asaZjcw/gfebE/PM=
			[GamePlayers]
			[UserPlayerPairings]
			erkki = erkkituhoaja
		""")
		orig_contents = self.get_cache_file_contents()
		self.cache.sync()
		assert "erkkituhoaja" in self.error_message
		self.assert_ini_contents_not_modified(orig_contents)

	def test_error_received_on_missing_ts_user_definition(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			[GamePlayers]
			erkkituhoaja = 1234567
			[UserPlayerPairings]
			matti = erkkituhoaja
		""")
		orig_contents = self.get_cache_file_contents()
		self.cache.sync()
		assert "matti" in self.error_message
		self.assert_ini_contents_not_modified(orig_contents)

	def test_error_received_on_missing_section(self):
		self.write_cache_file("""
			[GamePlayers]
			erkkituhoaja = 1234567
			[UserPlayerPairings]
			erkki = erkkituhoaja
		""")
		orig_contents = self.get_cache_file_contents()
		self.cache.sync()
		assert "TeamSpeakUsers" in self.error_message
		self.assert_ini_contents_not_modified(orig_contents)

	def test_file_unchanged_after_read_error_and_modify(self):
		self.test_error_received_on_missing_ts_user_definition()
		orig_contents = self.get_cache_file_contents()
		self.cache.add_ts_user("erkki", "asaZjcw/gfebE/PM=")
		self.cache.sync()
		self.assert_ini_contents_not_modified(orig_contents)

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
