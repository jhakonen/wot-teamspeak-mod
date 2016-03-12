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

from ..infrastructure import log
from ..infrastructure.timer import TimerMixin

from ..thirdparty.iniparse import ConfigParser
import os
import csv
import re
import io
import cStringIO

_GENERAL_HELP = """
; This file stores paired TeamSpeak users and WOT players. When TessuMod
; manages to match a TeamSpeak user to a WOT player ingame it stores the match
; into this file. This allows TessuMod to match users in future even if the
; player's name changes in TeamSpeak or in game.
; 
; This file can be modified and changes are automatically loaded even when game
; is running. The frequency of checks is determined by 'ini_check_interval'
; option in tessu_mod.ini.
;
; This file will not update with new users, players or pairings when playing
; replays. Although, if modified by user the done changes are still loaded
; automatically. To enable updates with replays toggle 'update_cache_in_replays'
; option in tessu_mod.ini to 'on'.
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

class UserCacheAdapter(TimerMixin):

	def __init__(self, app):
		super(UserCacheAdapter, self).__init__()
		self.__app = app

		self.__ts_users = {}
		self.__players = {}
		self.__pairings = {}
		self.__read_error = False
		self.__write_enabled = True

		self.on_timeout(1, self.__on_sync_timeout, repeat=True)

	def init(self, cache_filepath):
		self.__ini_cache = INICache(cache_filepath)
		self.__ini_cache.on_init_cleanup = self.__on_init_cleanup
		self.__ini_cache.on_read = self.__on_read
		self.__ini_cache.on_write = self.__on_write
		self.__ini_cache.on_write_io = self.__on_write_io
		self.__ini_cache.init()

	def set_file_check_interval(self, interval):
		self.on_timeout(interval, self.__on_sync_timeout, repeat=True)

	def set_write_enabled(self, enabled):
		self.__write_enabled = enabled
		self.__update_write_allowed()

	def add_chat_user(self, unique_id, nick):
		if unique_id not in self.__ts_users:
			self.__ts_users[unique_id] = nick.lower()
			self.__ini_cache.write_needed()

	def add_player(self, id, name):
		id = str(id)
		if id not in self.__players:
			self.__players[id] = name.lower()
			self.__ini_cache.write_needed()

	def pair(self, player_id, user_unique_id):
		player_id = str(player_id)
		user_unique_id = str(user_unique_id)
		if user_unique_id not in self.__pairings:
			self.__pairings[user_unique_id] = []
		if player_id not in self.__pairings[user_unique_id]:
			self.__pairings[user_unique_id].append(player_id)
			self.__ini_cache.write_needed()

	def get_paired_player_ids(self, user_unique_id):
		user_unique_id = str(user_unique_id)
		if user_unique_id in self.__pairings:
			for player_id in self.__pairings[user_unique_id]:
				yield int(player_id)

	def get_config_filepath(self):
		return self.__ini_cache.ini_path

	def get_backend(self):
		return self.__ini_cache

	def __update_write_allowed(self):
		self.__ini_cache.is_write_allowed = self.__write_enabled and not self.__read_error

	def __on_init_cleanup(self):
		'''Removes TeamSpeak user and WOT players who do not appear in the pairings.'''
		cleanup_ts_ids = [id for id in self.__ts_users]
		cleanup_player_ids = [id for id in self.__players]
		for ts_id, player_ids in self.__pairings.iteritems():
			cleanup_ts_ids.remove(ts_id)
			for player_id in self.__pairings[ts_id]:
				try:
					cleanup_player_ids.remove(player_id)
				except:
					pass
		for id in cleanup_ts_ids:
			del self.__ts_users[id]
		for id in cleanup_player_ids:
			del self.__players[id]

	def __on_read(self, parser):
		error_message = None
		try:
			ts_users      = {nick.lower(): id for nick, id in parser.items("TeamSpeakUsers")}
			players       = {nick.lower(): id for nick, id in parser.items("GamePlayers")}
			nick_pairings = {ts_nick.lower(): csv_split(p_nicks.lower()) for ts_nick, p_nicks in parser.items("UserPlayerPairings")}
			id_pairings   = {}

			for ts_nick in nick_pairings:
				try:
					player_ids = [players[player_nick] for player_nick in nick_pairings[ts_nick]]
				except KeyError as error:
					error_message = "Player {0} is not defined".format(error)
					raise
				try:
					id_pairings[ts_users[ts_nick]] = player_ids
				except KeyError as error:
					error_message = "TeamSpeak user {0} is not defined".format(error)
					raise

			self.__ts_users = {id: nick for nick, id in ts_users.iteritems()}
			self.__players = {id: nick for nick, id in players.iteritems()}
			self.__pairings = id_pairings
			self.__read_error = False
			self.__update_write_allowed()
		except Exception as error:
			self.__read_error = True
			self.__update_write_allowed()
			self.__on_read_error(error_message if error_message else error)

	def __on_write(self, parser):
		parser.add_section("TeamSpeakUsers")
		parser.add_section("GamePlayers")
		parser.add_section("UserPlayerPairings")
		for id, nick in self.__ts_users.iteritems():
			parser.set("TeamSpeakUsers", ini_escape(nick), str(id))
		for id, nick in self.__players.iteritems():
			parser.set("GamePlayers", ini_escape(nick), str(id))
		for ts_id, player_ids in self.__pairings.iteritems():
			parser.set("UserPlayerPairings",
				ini_escape(self.__ts_users[ts_id]),
				ini_escape(csv_join([self.__players[player_id] for player_id in player_ids]))
			)

	def __on_write_io(self, string_io):
		ini_contents = string_io.getvalue()
		ini_contents = ini_contents.replace("[TeamSpeakUsers]",     _TS_USERS_HELP + "\n[TeamSpeakUsers]", 1)
		ini_contents = ini_contents.replace("[GamePlayers]",        _PLAYERS_HELP  + "\n[GamePlayers]", 1)
		ini_contents = ini_contents.replace("[UserPlayerPairings]", _PAIRINGS_HELP + "\n[UserPlayerPairings]", 1)
		string_io.truncate(0)
		string_io.write(_GENERAL_HELP + "\n\n\n" + ini_contents)

	def __on_read_error(self, error_message):
		'''This function is called if user cache's reading fails.'''
		self.__app["show-usercache-error-message"](error_message)

	def __on_sync_timeout(self):
		if self.__ini_cache:
			self.__ini_cache.sync()

class INICache(object):

	def __init__(self, ini_path):
		self.__sync_time = 0
		self.__parser = None
		self.__write_needed = False
		self.__initialized = False
		self.ini_path = ini_path
		self.on_init_cleanup = noop
		self.on_read = noop
		self.on_write = noop
		self.on_write_io = noop
		self.is_write_allowed = True

	def init(self):
		if self.__initialized:
			return
		ini_dirpath = os.path.dirname(self.ini_path)
		if not os.path.exists(ini_dirpath):
			os.makedirs(ini_dirpath)
		self.__read_cache_file()
		self.on_init_cleanup()
		self.__write_cache_file()
		self.sync()
		self.__initialized = True

	def write_needed(self):
		self.__write_needed = True

	def __read_cache_file(self):
		if not os.path.isfile(self.ini_path):
			return
		parser = ConfigParser()
		if not parser.read(self.ini_path):
			log.LOG_ERROR("Failed to parse ini file '{0}'"
				.format(self.ini_path))
			return
		self.on_read(parser)
		self.__update_sync_time()

	def __update_sync_time(self):
		self.__sync_time = self.__get_modified_time()

	def __write_cache_file(self):
		if self.is_write_allowed:
			parser = ConfigParser()
			self.on_write(parser)
			with open(self.ini_path, "w") as f:
				string_io = cStringIO.StringIO()
				parser.write(string_io)
				self.on_write_io(string_io)
				f.write(string_io.getvalue())
			self.__update_sync_time()
		self.__write_needed = False

	def sync(self):
		if self.__is_cache_file_modified():
			self.__read_cache_file()
		elif self.__should_write_cache_file():
			self.__write_cache_file()

	def __get_modified_time(self):
		return os.path.getmtime(self.ini_path)

	def __is_cache_file_modified(self):
		return self.__sync_time < self.__get_modified_time()

	def __should_write_cache_file(self):
		return self.__write_needed or not os.path.isfile(self.ini_path)

def noop(*args, **kwargs):
	pass

def csv_split(string_value):
	return csv.reader([string_value]).next()

def csv_join(list_value):
	bytes_io = io.BytesIO()
	csv_out = csv.writer(bytes_io)
	csv_out.writerow(list_value)
	return bytes_io.getvalue().rstrip("\r\n")

def ini_escape(value):
	return re.sub(r"[\[\]=:\\]", "*", value)
