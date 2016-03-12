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

from ..thirdparty.iniparse import ConfigParser
import csv
import re
import copy
import os

from ..constants import SettingConstants
from ..infrastructure.timer import TimerMixin
from ..infrastructure import log

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

class SettingsAdapter(TimerMixin):

	def __init__(self, app):
		super(SettingsAdapter, self).__init__()
		self.__app = app
		self.__loaded_values = {}

	def set_file_check_interval(self, interval):
		self.on_timeout(interval, self.__sync, repeat=True)

	def get(self, key):
		return copy.copy(self.__loaded_values[key])

	def init(self, settings_filepath):
		# make sure that ini-folder exists
		try:
			os.makedirs(settings_filepath)
		except os.error:
			pass
		self.__load_time = 0
		self.__parser = None
		self.__ini_filepath = settings_filepath
		self.__write_default_file()
		self.__sync()

	def __write_default_file(self):
		ini_dirpath = os.path.dirname(self.__ini_filepath)
		if not os.path.exists(ini_dirpath):
			os.makedirs(ini_dirpath)
		if not os.path.isfile(self.__ini_filepath):
			with open(self.__ini_filepath, "w") as f:
				f.write(DEFAULT_INI)

	def __sync(self):
		if self._is_modified():
			self.__load_parser()
			self.__on_settings_reloaded()

	def _is_modified(self):
		return self.__load_time < self.__get_modified_time()

	def __get_modified_time(self):
		return os.path.getmtime(self.__ini_filepath)

	def __load_parser(self):
		self.__parser = ConfigParser()
		self.__parser.add_section("General")
		self.__parser.set("General", "log_level", "1")
		self.__parser.set("General", "ini_check_interval", "5")
		self.__parser.set("General", "speak_stop_delay", "1")
		self.__parser.set("General", "get_wot_nick_from_ts_metadata", "on")
		self.__parser.set("General", "update_cache_in_replays", "off")
		self.__parser.set("General", "ts_nick_search_enabled", "on")
		self.__parser.set("General", "nick_extract_patterns", "")
		self.__parser.add_section("NameMappings")
		self.__parser.add_section("TSClientQueryService")
		self.__parser.set("TSClientQueryService", "host", "localhost")
		self.__parser.set("TSClientQueryService", "port", "25639")
		self.__parser.set("TSClientQueryService", "polling_interval", "0.1")
		self.__parser.add_section("VoiceChatNotifications")
		self.__parser.set("VoiceChatNotifications", "enabled", "on")
		self.__parser.set("VoiceChatNotifications", "self_enabled", "on")
		self.__parser.add_section("MinimapNotifications")
		self.__parser.set("MinimapNotifications", "enabled", "on")
		self.__parser.set("MinimapNotifications", "self_enabled", "on")
		self.__parser.set("MinimapNotifications", "action", "attackSender")
		self.__parser.set("MinimapNotifications", "repeat_interval", "3.5")
		if self.__parser.read(self.__ini_filepath):
			self.__load_time = self.__get_modified_time()
		else:
			log.LOG_ERROR("Failed to parse ini file '{0}'".format(self.__ini_filepath))

	def __on_settings_reloaded(self):
		self.__loaded_values = {
			SettingConstants.LOG_LEVEL                      : self.__parser.getint("General", "log_level"),
			SettingConstants.FILE_CHECK_INTERVAL            : self.__parser.getfloat("General", "ini_check_interval"),
			SettingConstants.SPEAK_STOP_DELAY               : self.__parser.getfloat("General", "speak_stop_delay"),
			SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT : self.__parser.getboolean("General", "get_wot_nick_from_ts_metadata"),
			SettingConstants.UPDATE_CACHE_IN_REPLAYS        : self.__parser.getboolean("General", "update_cache_in_replays"),
			SettingConstants.CHAT_NICK_SEARCH_ENABLED       : self.__parser.getboolean("General", "ts_nick_search_enabled"),
			SettingConstants.NICK_EXTRACT_PATTERNS          : [re.compile(pattern, re.IGNORECASE) for pattern in self.__get_list("General", "nick_extract_patterns")],
			SettingConstants.NICK_MAPPINGS                  : {k.lower(): v.lower() for k, v in self.__get_dict("NameMappings").iteritems()},
			SettingConstants.CHAT_CLIENT_HOST               : self.__parser.get("TSClientQueryService", "host"),
			SettingConstants.CHAT_CLIENT_PORT               : self.__parser.getint("TSClientQueryService", "port"),
			SettingConstants.CHAT_CLIENT_POLLING_INTERVAL   : self.__parser.getfloat("TSClientQueryService", "polling_interval"),
			SettingConstants.VOICE_CHAT_NOTIFY_ENABLED      : self.__parser.getboolean("VoiceChatNotifications", "enabled"),
			SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED : self.__parser.getboolean("VoiceChatNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ENABLED         : self.__parser.getboolean("MinimapNotifications", "enabled"),
			SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED    : self.__parser.getboolean("MinimapNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ACTION          : self.__parser.get("MinimapNotifications", "action"),
			SettingConstants.MINIMAP_NOTIFY_REPEAT_INTERVAL : self.__parser.getfloat("MinimapNotifications", "repeat_interval")
		}
		self.__app["load-settings"](self.__loaded_values)

	def __get_list(self, section, option):
		items = []
		for row in csv.reader([self.__parser.get(section, option)]):
			for item in row:
				items.append(item)
		return items

	def __get_dict(self, section):
		return {option: self.__parser.get(section, option) for option in self.__parser.options(section)}
