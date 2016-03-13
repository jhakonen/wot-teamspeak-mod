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
from ..infrastructure.inifile import INIFile
import os
import csv
import re
import io

DEFAULT_INI = """
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


; TessuMod will populate this section with TeamSpeak users who are in the same
; TeamSpeak channel with you.
; 
; The users are stored as key/value pairs where key is user's nick name and
; value is user's unique id. The nick doesn't have to be the real user nick
; name, it can be anything. If you modify the nick name, make sure you also
; update names used in UserPlayerPairings.
[TeamSpeakUsers]


; TessuMod will populate this section with players from your friend and clan
; member lists. Players are also added when someone speaks in your TeamSpeak
; channel and TessuMod manages to match the user to player which isn't yet in
; the cache.
; 
; The players are stored as key/value pairs where key is player's nick name and
; value is player's id. The nick doesn't have to be the real player nick name,
; it can be anything. If you modify the nick name, make sure you also update
; names used in UserPlayerPairings.
[GamePlayers]


; This section is updated when TessuMod, using nick matching rules, manages to
; match TeamSpeak user to a WOT player.
; 
; The pairings are stored as key/value pairs where key is TeamSpeak nick name
; and value is a list of WOT nick names that the TeamSpeak user will match
; against. The WOT nick list is a comma-separated-value.
[UserPlayerPairings]
"""

class UserCacheAdapter(object):

	def __init__(self, app):
		self.__inifile = INIFile(DEFAULT_INI)
		self.__inifile.on("file-loaded", self.__on_file_loaded)
		self.__app = app
		self.__ts_users = {}
		self.__players = {}
		self.__pairings = {}
		self.__read_error = False
		self.__write_enabled = True
		self.__initialized = False

	def init(self, cache_filepath):
		self.__inifile.set_filepath(cache_filepath)
		self.__inifile.init()
		self.__initialized = True

	def set_file_check_interval(self, interval):
		self.__inifile.set_file_check_interval(interval)

	def set_write_enabled(self, enabled):
		self.__write_enabled = enabled
		self.__update_write_allowed()

	def add_chat_user(self, unique_id, nick):
		if unique_id not in self.__ts_users:
			self.__ts_users[unique_id] = nick = nick.lower()
			self.__inifile.set("TeamSpeakUsers", nick, unique_id)

	def add_player(self, id, name):
		id = str(id)
		if id not in self.__players:
			self.__players[id] = name = name.lower()
			self.__inifile.set("GamePlayers", name, id)

	def pair(self, player_id, user_unique_id):
		player_id = str(player_id)
		user_unique_id = str(user_unique_id)
		if user_unique_id not in self.__pairings:
			self.__pairings[user_unique_id] = []
		if player_id not in self.__pairings[user_unique_id]:
			self.__pairings[user_unique_id].append(player_id)
			self.__inifile.set_list("UserPlayerPairings",
				self.__ts_users[user_unique_id],
				[self.__players[player_id] for player_id in self.__pairings[user_unique_id]]
			)

	def get_paired_player_ids(self, user_unique_id):
		return [int(player_id) for player_id in self.__pairings.get(user_unique_id, [])]

	def get_config_filepath(self):
		return self.__inifile.get_filepath()

	def get_backend(self):
		return self.__inifile

	def __update_write_allowed(self):
		self.__inifile.set_writing_enabled(self.__write_enabled and not self.__read_error)

	def __on_file_loaded(self):
		error_message = None
		try:
			ts_users = {}
			players = {}
			nick_pairings = {}
			id_pairings   = {}
			for nick, id in self.__inifile.get_dict("TeamSpeakUsers", self.__inifile.get_string).iteritems():
				ts_users[nick.lower()] = id
			for nick, id in self.__inifile.get_dict("GamePlayers", self.__inifile.get_string).iteritems():
				players[nick.lower()] = id
			for ts_nick, p_nicks in self.__inifile.get_dict("UserPlayerPairings", self.__inifile.get_list).iteritems():
				nick_pairings[ts_nick.lower()] = [p_nick.lower() for p_nick in p_nicks]

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
			self.__app["show-usercache-error-message"](error_message if error_message else error)

		# on first load, cleanup chatuser and players who do not appear in the pairings
		if not self.__initialized:
			cleanup_ts_ids = self.__ts_users.keys()
			cleanup_player_ids = self.__players.keys()
			for ts_id, player_ids in self.__pairings.iteritems():
				cleanup_ts_ids.remove(ts_id)
				for player_id in player_ids:
					if player_id in cleanup_player_ids:
						cleanup_player_ids.remove(player_id)
			for id in cleanup_ts_ids:
				name = self.__ts_users[id]
				self.__inifile.remove("TeamSpeakUsers", name)
				del self.__ts_users[id]
			for id in cleanup_player_ids:
				name = self.__players[id]
				self.__inifile.remove("GamePlayers", name)
				del self.__players[id]
