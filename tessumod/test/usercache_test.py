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
import ConfigParser
import mock
import helpers
from tessumod.adapters.usercache import UserCacheAdapter
from tessumod.infrastructure import timer

ini_path = os.path.join(helpers.temp_dirpath, "tessu_mod_cache.ini")

def get_cache_value(section, name):
	parser = ConfigParser.RawConfigParser()
	parser.read([ini_path])
	return parser.get(section, name)

def has_cache_value(section, name):
	parser = ConfigParser.RawConfigParser()
	parser.read([ini_path])
	return parser.has_option(section, name)

class TestUserCacheAdapter(object):

	def setUp(self):
		try:
			os.makedirs(os.path.dirname(ini_path))
		except:
			pass
		try:
			os.remove(ini_path)
		except:
			pass
		self.eventloop = mock.MagicMock()
		self.app = mock.MagicMock()
		self.app["show-usercache-error-message"].side_effect = self.set_error
		timer.set_eventloop(self.eventloop)
		self.adapter = UserCacheAdapter(self.app)
		self.error_message = ""
		self.adapter.init(ini_path)

	def set_error(self, message):
		self.error_message = message

	def write_cache_file(self, contents):
		contents = "\n".join([line.strip() for line in contents.split("\n")])
		print contents
		with open(ini_path, "w") as file:
			file.write(contents)
		self.adapter.get_backend().reset_last_modified()

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
		self.adapter.get_backend().init()
		print self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")

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
		self.adapter.get_backend().init()
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 4897346 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")

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
		self.adapter.get_backend().init()
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 1234567 in self.adapter.get_paired_player_ids("adfZjcw/gffbE/FO=")

	def test_error_received_on_missing_player_definition(self):
		self.write_cache_file("""
			[TeamSpeakUsers]
			erkki = asaZjcw/gfebE/PM=
			[GamePlayers]
			[UserPlayerPairings]
			erkki = erkkituhoaja
		""")
		orig_contents = self.get_cache_file_contents()
		self.adapter.get_backend().init()
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
		self.adapter.get_backend().init()
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
		self.adapter.get_backend().init()
		assert "erkki" in self.error_message
		self.assert_ini_contents_not_modified(orig_contents)

	def test_file_unchanged_after_read_error_and_modify(self):
		self.test_error_received_on_missing_ts_user_definition()
		orig_contents = self.get_cache_file_contents()
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "erkki")
		self.adapter.get_backend().init()
		self.assert_ini_contents_not_modified(orig_contents)

	def test_can_add_ts_user(self):
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.get_backend().init()
		assert get_cache_value("TeamSpeakUsers", "erkki") == "asaZjcw/gfebE/PM=", self.get_cache_file_contents()

	def test_can_add_player(self):
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.get_backend().init()
		assert get_cache_value("GamePlayers", "erkkituhoaja") == "1234567", self.get_cache_file_contents()

	def test_can_pair(self):
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.pair(1234567, "asaZjcw/gfebE/PM=")
		self.adapter.get_backend().init()
		assert get_cache_value("UserPlayerPairings", "erkki") == "erkkituhoaja", self.get_cache_file_contents()

	def test_can_get_pairing(self):
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.pair(1234567, "asaZjcw/gfebE/PM=")
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_get_two_paired_players_for_one_ts_user(self):
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.add_player(4897346, "Watnao")
		self.adapter.pair(1234567, "asaZjcw/gfebE/PM=")
		self.adapter.pair(4897346, "asaZjcw/gfebE/PM=")
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 4897346 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")

	def test_get_two_paired_ts_users_for_one_player(self):
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.add_chat_user("adfZjcw/gffbE/FO=", "Matti")
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.pair(1234567, "asaZjcw/gfebE/PM=")
		self.adapter.pair(1234567, "adfZjcw/gffbE/FO=")
		assert 1234567 in self.adapter.get_paired_player_ids("asaZjcw/gfebE/PM=")
		assert 1234567 in self.adapter.get_paired_player_ids("adfZjcw/gffbE/FO=")

	def test_disabling_cache_write_does_not_sync_to_file(self):
		self.adapter.set_write_enabled(False)
		self.adapter.add_chat_user("asaZjcw/gfebE/PM=", "Erkki")
		self.adapter.add_player(1234567, "ErkkiTuhoaja")
		self.adapter.pair(1234567, "asaZjcw/gfebE/PM=")
		self.adapter.get_backend().init()
		assert not has_cache_value("TeamSpeakUsers", "Erkki"), self.get_cache_file_contents()
		assert not has_cache_value("GamePlayers", "ErkkiTuhoaja"), self.get_cache_file_contents()
		assert not has_cache_value("UserPlayerPairings", "Erkki"), self.get_cache_file_contents()
