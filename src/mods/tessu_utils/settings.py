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
from utils import LOG_ERROR
import BigWorld
import Event

DEFAULT_INI = """
; Defines configuration options for TessuMod. Uncomment and change value of
; options below to take them into use.

[General]
; Defines minimum level of logging to python.log, possible values includes:
;   0: DEBUG
;   1: NOTE
;   2: WARNING
;   3: ERROR
log_level: 1

; Interval (as seconds) that this ini-file is checked for modifications, and
; reloaded if modified
ini_check_interval: 5

; Delay (in seconds) stopping of speak feedback after users has stopped speaking
speak_stop_delay: 1

; Defines regular expression for extracting WOT nickname from user's
; TS nickname, e.g. if TS nickname is:
;   "wot_nickname | real name"
; Following expression will extract the wot_nickname:
;   nick_extract_patterns: ([a-z0-9_]+)
; For more info, see: https://docs.python.org/2/library/re.html
; The captured nickname is also stripped of any surrounding white space and
; compared case insensitive manner to seen WOT players.
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
;  - firstEnemy
;  - enemySPG
;  - help_me
;  - help_meSPG
;  - follow_me
;  - follow_meSPG
;  - attack
;  - attackSPG
;  - attackSender
;  - attackSenderSPG
;  - reloading_gun
;  - reloading_gunSPG
;  - negative
;  - negativeSPG
;  - positive
;  - positiveSPG
;  - stop
;  - stopSPG
;  - help_me_ex
;  - help_me_exSPG
;  - turn_back
;  - turn_backSPG
action: attackSender

; Define repeat interval (in seconds) of the notification animation
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
		self._delayed_reload()

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

	def _delayed_reload(self):
		def reload():
			if self._is_modified():
				self._load_parser()
				self.on_reloaded()
			self._delayed_reload()
		BigWorld.callback(self.get_ini_check_interval(), reload)

	def _is_modified(self):
		return self._load_time < self._get_modified_time()

	def get_log_level(self):
		return self._parser.getint("General", "log_level")

	def get_ini_check_interval(self):
		return self._parser.getfloat("General", "ini_check_interval")

	def get_speak_stop_delay(self):
		return self._parser.getfloat("General", "speak_stop_delay")

	def get_nick_extract_patterns(self):
		patterns = []
		for row in csv.reader([self._parser.get("General", "nick_extract_patterns")]):
			for pattern in row:
				patterns.append(pattern)
		return patterns

	def get_name_mappings(self):
		results = {}
		for option in self._parser.options("NameMappings"):
			results[option.lower()] = self._parser.get("NameMappings", option).lower()
		return results

	def get_client_query_host(self):
		return self._parser.get("TSClientQueryService", "host")

	def get_client_query_port(self):
		return self._parser.getint("TSClientQueryService", "port")

	def get_client_query_interval(self):
		return self._parser.getfloat("TSClientQueryService", "polling_interval")

	def is_voice_chat_notifications_enabled(self):
		return self._parser.getboolean("VoiceChatNotifications", "enabled")

	def is_self_voice_chat_notifications_enabled(self):
		return self._parser.getboolean("VoiceChatNotifications", "self_enabled")

	def is_minimap_notifications_enabled(self):
		return self._parser.getboolean("MinimapNotifications", "enabled")

	def is_self_minimap_notifications_enabled(self):
		return self._parser.getboolean("MinimapNotifications", "self_enabled")

	def get_minimap_action(self):
		return self._parser.get("MinimapNotifications", "action")

	def get_minimap_action_interval(self):
		return self._parser.getfloat("MinimapNotifications", "repeat_interval")
