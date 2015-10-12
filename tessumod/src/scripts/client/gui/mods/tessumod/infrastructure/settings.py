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
from utils import LOG_ERROR
import BigWorld
import Event

DEFAULT_INI = """
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
repeat_interval: 3.5
"""

_g_settings = None

def settings(ini_file_path=None):
	global _g_settings
	if _g_settings is None and ini_file_path is not None:
		_g_settings = Settings(ini_file_path)
	if _g_settings is None:
		raise RuntimeError("Settings not initialized")
	return _g_settings

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
			with open(self._ini_path, "w") as f:
				f.write(DEFAULT_INI)

	def _load_parser(self):
		self._parser = ConfigParser.SafeConfigParser()
		self._parser.add_section("General")
		self._parser.set("General", "log_level", "1")
		self._parser.set("General", "ini_check_interval", "5")
		self._parser.set("General", "speak_stop_delay", "1")
		self._parser.set("General", "get_wot_nick_from_ts_metadata", "on")
		self._parser.set("General", "update_cache_in_replays", "off")
		self._parser.set("General", "ts_nick_search_enabled", "on")
		self._parser.set("General", "nick_extract_patterns", "")
		self._parser.add_section("NameMappings")
		self._parser.add_section("TSClientQueryService")
		self._parser.set("TSClientQueryService", "host", "localhost")
		self._parser.set("TSClientQueryService", "port", "25639")
		self._parser.set("TSClientQueryService", "polling_interval", "0.1")
		self._parser.add_section("VoiceChatNotifications")
		self._parser.set("VoiceChatNotifications", "enabled", "on")
		self._parser.set("VoiceChatNotifications", "self_enabled", "on")
		self._parser.add_section("MinimapNotifications")
		self._parser.set("MinimapNotifications", "enabled", "on")
		self._parser.set("MinimapNotifications", "self_enabled", "on")
		self._parser.set("MinimapNotifications", "action", "attackSender")
		self._parser.set("MinimapNotifications", "repeat_interval", "3.5")
		if self._parser.read(self._ini_path):
			self._load_time = self._get_modified_time()
		else:
			LOG_ERROR("Failed to parse ini file '{0}'".format(self._ini_path))

	def _get_modified_time(self):
		return os.path.getmtime(self._ini_path)

	def sync(self):
		if self._is_modified():
			self._load_parser()
			self.on_reloaded()

	def _is_modified(self):
		return self._load_time < self._get_modified_time()

	def get_str(self, section, option):
		return self._parser.get(section, option)

	def get_int(self, section, option):
		return self._parser.getint(section, option)

	def get_float(self, section, option):
		return self._parser.getfloat(section, option)

	def get_boolean(self, section, option):
		return self._parser.getboolean(section, option)

	def get_list(self, section, option):
		items = []
		for row in csv.reader([self._parser.get(section, option)]):
			for item in row:
				items.append(item)
		return items

	def get_dict(self, section):
		return {option: self._parser.get(section, option) for option in self._parser.options(section)}
