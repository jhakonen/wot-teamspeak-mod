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

import ConfigParser
import os
import csv
import re
import io
import cStringIO
from utils import LOG_ERROR, LOG_NOTE
import BigWorld
import Event

_GENERAL_HELP = """
; This file stores paired TeamSpeak users and WOT players. When TessuMod
; manages to match a TeamSpeak user to a WOT player ingame it stores the match
; into this file. This allows TessuMod to match users in future even if the
; player's name changes in TeamSpeak or in game.
; 
; All nick names in this cache are stored in lower case, no matter how they are
; written in WOT or in TeamSpeak. Also, any ini-syntax's reserved characters
; are replaced with '*'.
""".strip()

_TS_USERS_HELP = """
; TessuMod will populate this section with TeamSpeak users who are in the same
; TeamSpeak channel with you.
; 
; The users are stored as key/value pairs where key is user's nick name and
; value is user's unique id. The nick doesn't have to be the real user nick
; name, it can be anything. If you modify the nick name, make sure you also
; update names used in UserPlayerPairings.
""".strip()

_PLAYERS_HELP  = """
; TessuMod will populate this section with players from your friend and clan
; member lists. Players are also added when someone speaks in your TeamSpeak
; channel and TessuMod manages to match the user to player which isn't yet in
; the cache.
; 
; The players are stored as key/value pairs where key is player's nick name and
; value is player's id. The nick doesn't have to be the real player nick name,
; it can be anything. If you modify the nick name, make sure you also update
; names used in UserPlayerPairings.
""".strip()

_PAIRINGS_HELP = """
; This section is updated when TessuMod, using nick matching rules, manages to
; match TeamSpeak user to a WOT player.
; 
; The pairings are stored as key/value pairs where key is TeamSpeak nick name
; and value is a list of WOT nick names that the TeamSpeak user will match
; against. The WOT nick list is a comma-separated-value.
""".strip()

class UserCache(object):

	def __init__(self, ini_path):
		self._ts_users = {}
		self._players = {}
		self._pairings = {}
		self._ini_cache = INICache(ini_path)
		self._ini_cache.on_init_cleanup = self._on_init_cleanup
		self._ini_cache.on_read += self._on_read
		self._ini_cache.on_write += self._on_write
		self._ini_cache.on_write_io += self._on_write_io
		self._ini_cache.init()

	def _on_read(self, parser):
		ts_users      = {nick.lower(): id for nick, id in parser.items("TeamSpeakUsers")}
		players       = {nick.lower(): id for nick, id in parser.items("GamePlayers")}
		nick_pairings = {ts_nick.lower(): csv_split(p_nicks.lower()) for ts_nick, p_nicks in parser.items("UserPlayerPairings")}
		id_pairings   = {}

		for ts_nick in nick_pairings:
			id_pairings[ts_users[ts_nick]] = [players[player_nick] for player_nick in nick_pairings[ts_nick]]

		self._ts_users = {id: nick for nick, id in ts_users.iteritems()}
		self._players = {id: nick for nick, id in players.iteritems()}
		self._pairings = id_pairings

	def _on_init_cleanup(self):
		'''Removes TeamSpeak user and WOT players who do not appear in the pairings.'''
		cleanup_ts_ids = [id for id in self._ts_users]
		cleanup_player_ids = [id for id in self._players]
		for ts_id, player_ids in self._pairings.iteritems():
			cleanup_ts_ids.remove(ts_id)
			for player_id in self._pairings[ts_id]:
				try:
					cleanup_player_ids.remove(player_id)
				except:
					pass
		for id in cleanup_ts_ids:
			del self._ts_users[id]
		for id in cleanup_player_ids:
			del self._players[id]

	def _on_write(self, parser):
		parser.add_section("TeamSpeakUsers")
		parser.add_section("GamePlayers")
		parser.add_section("UserPlayerPairings")
		for id, nick in self._ts_users.iteritems():
			parser.set("TeamSpeakUsers", ini_escape(nick), str(id))
		for id, nick in self._players.iteritems():
			parser.set("GamePlayers", ini_escape(nick), str(id))
		for ts_id, player_ids in self._pairings.iteritems():
			parser.set("UserPlayerPairings",
				ini_escape(self._ts_users[ts_id]),
				ini_escape(csv_join([self._players[player_id] for player_id in player_ids]))
			)

	def _on_write_io(self, string_io):
		ini_contents = string_io.getvalue()
		ini_contents = ini_contents.replace("[TeamSpeakUsers]",     _TS_USERS_HELP + "\n[TeamSpeakUsers]", 1)
		ini_contents = ini_contents.replace("[GamePlayers]",        _PLAYERS_HELP  + "\n[GamePlayers]", 1)
		ini_contents = ini_contents.replace("[UserPlayerPairings]", _PAIRINGS_HELP + "\n[UserPlayerPairings]", 1)
		string_io.truncate(0)
		string_io.write(_GENERAL_HELP + "\n\n\n" + ini_contents)

	def add_ts_user(self, name, id):
		if id not in self._ts_users:
			self._ts_users[id] = name.lower()
			self._ini_cache.write_needed()

	def add_player(self, name, id):
		id = str(id)
		if id not in self._players:
			self._players[id] = name.lower()
			self._ini_cache.write_needed()

	def pair(self, player_id, ts_user_id):
		player_id = str(player_id)
		ts_user_id = str(ts_user_id)
		if ts_user_id not in self._pairings:
			self._pairings[ts_user_id] = []
			self._ini_cache.write_needed()
		if player_id not in self._pairings[ts_user_id]:
			self._pairings[ts_user_id].append(player_id)
			self._ini_cache.write_needed()

	def get_paired_player_ids(self, ts_user_id):
		ts_user_id = str(ts_user_id)
		if ts_user_id in self._pairings:
			for player_id in self._pairings[ts_user_id]:
				yield int(player_id)

	def sync(self):
		self._ini_cache.sync()

class INICache(object):

	def __init__(self, ini_path):
		self._sync_time = 0
		self._parser = None
		self._write_needed = False
		self._ini_path = ini_path
		self.on_init_cleanup = Event.Event()
		self.on_read = Event.Event()
		self.on_write = Event.Event()
		self.on_write_io = Event.Event()

	def init(self):
		self._read_cache_file()
		self.on_init_cleanup()
		self._write_cache_file()
		self.sync()

	def write_needed(self):
		self._write_needed = True

	def _read_cache_file(self):
		if not os.path.isfile(self._ini_path):
			return
		parser = ConfigParser.RawConfigParser()
		if not parser.read(self._ini_path):
			LOG_ERROR("Failed to parse ini file '{0}'"
				.format(self._ini_path))
			return
		self.on_read(parser)
		self._update_sync_time()

	def _update_sync_time(self):
		self._sync_time = self._get_modified_time()

	def _write_cache_file(self):
		parser = ConfigParser.RawConfigParser()
		self.on_write(parser)
		with open(self._ini_path, "w") as f:
			string_io = cStringIO.StringIO()
			parser.write(string_io)
			self.on_write_io(string_io)
			f.write(string_io.getvalue())
		self._update_sync_time()
		self._write_needed = False

	def sync(self):
		if self._is_cache_file_modified():
			self._read_cache_file()
		elif self._should_write_cache_file():
			self._write_cache_file()

	def _get_modified_time(self):
		return os.path.getmtime(self._ini_path)

	def _is_cache_file_modified(self):
		return self._sync_time < self._get_modified_time()

	def _should_write_cache_file(self):
		return self._write_needed or not os.path.isfile(self._ini_path)

def csv_split(string_value):
	return csv.reader([string_value]).next()

def csv_join(list_value):
	bytes_io = io.BytesIO()
	csv_out = csv.writer(bytes_io)
	csv_out.writerow(list_value)
	return bytes_io.getvalue().rstrip("\r\n")

def ini_escape(value):
	return re.sub(r"[\[\]=:\\]", "*", value)
