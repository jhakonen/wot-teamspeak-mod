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

import re
import copy

from ..constants import SettingConstants
from ..infrastructure.inifile import INIFile

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

class SettingsAdapter(object):

	def __init__(self, app):
		self.__inifile = INIFile(DEFAULT_INI)
		self.__inifile.on("file-load-before", self.__on_file_load)
		self.__inifile.on("file-load-after", self.__on_file_loaded)
		self.__app = app
		self.__loaded_values = {}

	def set_file_check_interval(self, interval):
		self.__inifile.set_file_check_interval(interval)

	def get(self, key):
		return copy.copy(self.__loaded_values[key])

	def init(self, settings_filepath):
		self.__inifile.set_filepath(settings_filepath)
		self.__inifile.init()

	def __on_file_load(self):
		self.__inifile.add_section("General")
		self.__inifile.set("General", "log_level", "1")
		self.__inifile.set("General", "ini_check_interval", "5")
		self.__inifile.set("General", "speak_stop_delay", "1")
		self.__inifile.set("General", "get_wot_nick_from_ts_metadata", "on")
		self.__inifile.set("General", "update_cache_in_replays", "off")
		self.__inifile.set("General", "ts_nick_search_enabled", "on")
		self.__inifile.set("General", "nick_extract_patterns", "")
		self.__inifile.add_section("NameMappings")
		self.__inifile.add_section("TSClientQueryService")
		self.__inifile.set("TSClientQueryService", "host", "localhost")
		self.__inifile.set("TSClientQueryService", "port", "25639")
		self.__inifile.set("TSClientQueryService", "polling_interval", "0.1")
		self.__inifile.add_section("VoiceChatNotifications")
		self.__inifile.set("VoiceChatNotifications", "enabled", "on")
		self.__inifile.set("VoiceChatNotifications", "self_enabled", "on")
		self.__inifile.add_section("MinimapNotifications")
		self.__inifile.set("MinimapNotifications", "enabled", "on")
		self.__inifile.set("MinimapNotifications", "self_enabled", "on")
		self.__inifile.set("MinimapNotifications", "action", "attackSender")
		self.__inifile.set("MinimapNotifications", "repeat_interval", "3.5")

	def __on_file_loaded(self):
		self.__loaded_values = {
			SettingConstants.LOG_LEVEL                      : self.__inifile.get_int("General", "log_level"),
			SettingConstants.FILE_CHECK_INTERVAL            : self.__inifile.get_float("General", "ini_check_interval"),
			SettingConstants.SPEAK_STOP_DELAY               : self.__inifile.get_float("General", "speak_stop_delay"),
			SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT : self.__inifile.get_boolean("General", "get_wot_nick_from_ts_metadata"),
			SettingConstants.UPDATE_CACHE_IN_REPLAYS        : self.__inifile.get_boolean("General", "update_cache_in_replays"),
			SettingConstants.CHAT_NICK_SEARCH_ENABLED       : self.__inifile.get_boolean("General", "ts_nick_search_enabled"),
			SettingConstants.NICK_EXTRACT_PATTERNS          : [re.compile(pattern, re.IGNORECASE) for pattern in self.__inifile.get_list("General", "nick_extract_patterns")],
			SettingConstants.NICK_MAPPINGS                  : {k.lower(): v.lower() for k, v in self.__inifile.get_dict("NameMappings", self.__inifile.get_string).iteritems()},
			SettingConstants.CHAT_CLIENT_HOST               : self.__inifile.get_string("TSClientQueryService", "host"),
			SettingConstants.CHAT_CLIENT_PORT               : self.__inifile.get_int("TSClientQueryService", "port"),
			SettingConstants.CHAT_CLIENT_POLLING_INTERVAL   : self.__inifile.get_float("TSClientQueryService", "polling_interval"),
			SettingConstants.VOICE_CHAT_NOTIFY_ENABLED      : self.__inifile.get_boolean("VoiceChatNotifications", "enabled"),
			SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED : self.__inifile.get_boolean("VoiceChatNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ENABLED         : self.__inifile.get_boolean("MinimapNotifications", "enabled"),
			SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED    : self.__inifile.get_boolean("MinimapNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ACTION          : self.__inifile.get_string("MinimapNotifications", "action"),
			SettingConstants.MINIMAP_NOTIFY_REPEAT_INTERVAL : self.__inifile.get_float("MinimapNotifications", "repeat_interval")
		}
		self.__app["load-settings"](self.__loaded_values)
