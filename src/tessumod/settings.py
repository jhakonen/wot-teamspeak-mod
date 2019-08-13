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

import csv
import io
import os
import re

import BigWorld
import Event

from .py3compat import to_unicode
from .unicode_aware import ConfigParser
from .utils import LOG_ERROR

DEFAULT_INI = u"""
; Defines configuration options for TessuMod.

[General]
; Defines minimum level of logging to python.log, possible values includes:
;   0: DEBUG
;   1: NOTE
;   2: WARNING
;   3: ERROR
; DEBUG level also adds timestamps to log output.
log_level: 1

; Interval (as seconds) that this ini-file is checked for modifications, and
; reloaded if modified
ini_check_interval: 5

; Delay (in seconds) stopping of speak feedback after users has stopped speaking
speak_stop_delay: 1

; Enables or disables WOT nickname fetching from speaking TS user's meta data.
; If disabled, matching TS user to WOT nickname relies only either TS nickname
; to be same as WOT nickname or extract patterns and name mappings to be able
; to convert TS nickname to WOT nickname.
; Useful for testing different extract patterns and name mappings.
; Use as follows:
;  1. Start one of your replays (from game's replays-folder)
;  2. Connect to TeamSpeak
;  3. Change your TS nickname to form you wish to test
;  4. Change this option to 'off'
;  5. Try talking and see if the speak notifications appear in-game.
;  6. If nothing happens, adjust 'nick_extract_patterns' and [NameMappings] options.
;  7. Jump back to step 5
get_wot_nick_from_ts_metadata: on

; When turned on enables updating of tessu_mod_cache.ini when playing replays.
; Note that when playing someone else's replay your TS user will get paired
; with the replay's player name if this option is turned on.
; Useful for debugging purposes.
; Changing this value requires game restart
update_cache_in_replays: off

; Enables or disables searching of WOT player nicknames from within speaking TS
; user's nickname. With this option enabled you usually do not need to define
; anything in 'nick_extract_patterns' as the mod tries automatically to do the
; extracting for you.
; Disable this if the automatic searching pairs wrong TS users to wrong
; WOT players.
ts_nick_search_enabled: on

; Defines regular expressions for extracting WOT nickname from user's
; TS nickname, e.g. if TS nickname is:
;   "wot_nickname | real name"
; Following expression will extract the wot_nickname:
;   nick_extract_patterns: ([a-z0-9_]+)
; For more info, see: https://docs.python.org/2/library/re.html
; The captured nickname is also stripped of any surrounding white space and
; compared case insensitive manner to seen WOT players.
; You can also define multiple patterns separated with commas (,). First
; pattern that matches will be used.
; As a more complex example, if you need to extract 'nick' from following
; TS nicknames:
;   nick [tag]
;   nick (tag)
;   nick (real name) [tag]
;   nick/real name [tag]
;   [tag] nick
; Use patterns:
;   nick_extract_patterns: ([a-z0-9_]+),\[[^\]]+\]\s*([a-z0-9_]+)
nick_extract_patterns:

[NameMappings]
; This section defines a mapping of users' TeamSpeak and WOT nicknames.
; Use TS nickname as key and WOT nickname as value.
; If any 'nick_extract_patterns' are defined and a TS nickname matches to a
; pattern then the captured string is used as TS nickname instead.
; It is unnecessary define mapping for users who:
;  - have TessuMod already installed or
;  - have same name both in TS and WOT (matched case insensitive)
;ts_nickname: wot_nickname

[TSClientQueryService]
; API key (must be set with TeamSpeak version 3.1.3 or newer)
api_key:

; Host and port of the TeamSpeak clientquery plugin
host: localhost
port: 25639

; Interval (as seconds) to poll clientquery's socket
;  - high value causes reaction delay to speak notifications
;  - low value may have negative impact to game performance
; Changing this value requires game restart
polling_interval: 0.1

[VoiceChatNotifications]
; Enable or disable speak notifications in player panels and showing of
; speaker icons above tanks
enabled: on
; Enable or disable notifications when you're speaking
self_enabled: on

[MinimapNotifications]
; Enable or disable speak notifications in minimap
enabled: on
; Enable or disable notifications when you're speaking
self_enabled: on

; Define notification animation's appearance
; Can be one of the following:
;  - attack
;  - attackSPG
;  - attackSender
;  - attackSenderSPG
;  - enemySPG
;  - firstEnemy
;  - follow_me
;  - follow_meSPG
;  - help_me
;  - help_meSPG
;  - help_me_ex
;  - help_me_exSPG
;  - negative
;  - negativeSPG
;  - positive
;  - positiveSPG
;  - reloading_gun
;  - reloading_gunSPG
;  - stop
;  - stopSPG
;  - turn_back
;  - turn_backSPG
action: attackSender

; Define repeat interval (in seconds) of the notification animation.
; Adjust this until the animation animates continuously while someone is
; speaking.
repeat_interval: 2
"""

class Settings(object):

	def __init__(self, ini_path):
		self.on_reloaded = Event.Event()
		self._load_time = 0
		self._parser = None
		self._ini_path = ini_path
		self._write_default_file()
		self._load_parser()

	def _write_default_file(self):
		if not os.path.isfile(self._ini_path):
			with io.open(self._ini_path, "wt", encoding="utf8") as f:
				f.write(DEFAULT_INI)

	def _load_parser(self):
		self._parser = ConfigParser()
		self._parser.add_section(u"General")
		self._parser.set(u"General", u"log_level", u"1")
		self._parser.set(u"General", u"ini_check_interval", u"5")
		self._parser.set(u"General", u"speak_stop_delay", u"1")
		self._parser.set(u"General", u"get_wot_nick_from_ts_metadata", u"on")
		self._parser.set(u"General", u"update_cache_in_replays", u"off")
		self._parser.set(u"General", u"ts_nick_search_enabled", u"on")
		self._parser.set(u"General", u"nick_extract_patterns", u"")
		self._parser.add_section(u"NameMappings")
		self._parser.add_section(u"TSClientQueryService")
		self._parser.set(u"TSClientQueryService", u"host", u"localhost")
		self._parser.set(u"TSClientQueryService", u"port", u"25639")
		self._parser.set(u"TSClientQueryService", u"polling_interval", u"0.1")
		self._parser.add_section(u"VoiceChatNotifications")
		self._parser.set(u"VoiceChatNotifications", u"enabled", u"on")
		self._parser.set(u"VoiceChatNotifications", u"self_enabled", u"on")
		self._parser.add_section(u"MinimapNotifications")
		self._parser.set(u"MinimapNotifications", u"enabled", u"on")
		self._parser.set(u"MinimapNotifications", u"self_enabled", u"on")
		self._parser.set(u"MinimapNotifications", u"action", u"attackSender")
		self._parser.set(u"MinimapNotifications", u"repeat_interval", u"3.5")

		try:
			with io.open(self._ini_path, "rt", encoding="utf8") as f:
				self._parser.readfp(f)
				self._load_time = self._get_modified_time()
		except Exception as error:
			LOG_ERROR(u"Failed to parse ini file '{0}', reason: {1}"
				.format(self._ini_path, to_unicode(error)))

	def _get_modified_time(self):
		return os.path.getmtime(self._ini_path)

	def sync(self, force=False):
		if force or self._is_modified():
			self._load_parser()
			self.on_reloaded()

	def get_filepath(self):
		'''Returns path to the settings file.'''
		return self._ini_path

	def _is_modified(self):
		return self._load_time < self._get_modified_time()

	def get_log_level(self):
		return self._parser.getint(u"General", u"log_level")

	def get_ini_check_interval(self):
		return self._parser.getfloat(u"General", u"ini_check_interval")

	def get_speak_stop_delay(self):
		return self._parser.getfloat(u"General", u"speak_stop_delay")

	def get_wot_nick_from_ts_metadata(self):
		return self._parser.getboolean(u"General", u"get_wot_nick_from_ts_metadata")

	def should_update_cache_in_replays(self):
		return self._parser.getboolean(u"General", u"update_cache_in_replays")

	def is_ts_nick_search_enabled(self):
		return self._parser.getboolean(u"General", u"ts_nick_search_enabled")

	def get_nick_extract_patterns(self):
		patterns = []
		for row in csv.reader([self._parser.get(u"General", u"nick_extract_patterns")]):
			for pattern in row:
				patterns.append(re.compile(pattern, re.IGNORECASE))
		return patterns

	def get_name_mappings(self):
		results = {}
		for option in self._parser.options(u"NameMappings"):
			results[option.lower()] = self._parser.get(u"NameMappings", option).lower()
		return results

	def get_client_query_apikey(self):
		return self._parser.get(u"TSClientQueryService", u"api_key")

	def get_client_query_host(self):
		return self._parser.get(u"TSClientQueryService", u"host")

	def get_client_query_port(self):
		return self._parser.getint(u"TSClientQueryService", u"port")

	def get_client_query_interval(self):
		return self._parser.getfloat(u"TSClientQueryService", u"polling_interval")

	def is_voice_chat_notifications_enabled(self):
		return self._parser.getboolean(u"VoiceChatNotifications", u"enabled")

	def is_self_voice_chat_notifications_enabled(self):
		return self._parser.getboolean(u"VoiceChatNotifications", u"self_enabled")

	def is_minimap_notifications_enabled(self):
		return self._parser.getboolean(u"MinimapNotifications", u"enabled")

	def is_self_minimap_notifications_enabled(self):
		return self._parser.getboolean(u"MinimapNotifications", u"self_enabled")

	def get_minimap_action(self):
		return self._parser.get(u"MinimapNotifications", u"action")

	def get_minimap_action_interval(self):
		return self._parser.getfloat(u"MinimapNotifications", u"repeat_interval")
