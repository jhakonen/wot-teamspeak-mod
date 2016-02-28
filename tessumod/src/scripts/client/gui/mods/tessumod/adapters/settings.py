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
import os

from ..constants import SettingConstants
from ..infrastructure.settings import Settings

class SettingsAdapter(object):

	def __init__(self, eventloop, boundaries):
		self.__eventloop = eventloop
		self.__boundaries = boundaries
		self.__loaded_values = {}

	def init(self, settings_filepath):
		# make sure that ini-folder exists
		try:
			os.makedirs(settings_filepath)
		except os.error:
			pass
		self.__settings = Settings(settings_filepath)
		self.__settings.on_reloaded += self.__on_settings_reloaded
		self.__sync_repeater = self.__eventloop.create_callback_repeater(self.__settings.sync)
		self.__settings.sync()

	def set_file_check_interval(self, interval):
		self.__sync_repeater.start(interval)

	def get(self, key):
		return copy.copy(self.__loaded_values[key])

	def __on_settings_reloaded(self):
		self.__loaded_values = {
			SettingConstants.LOG_LEVEL                      : self.__settings.get_int("General", "log_level"),
			SettingConstants.FILE_CHECK_INTERVAL            : self.__settings.get_float("General", "ini_check_interval"),
			SettingConstants.SPEAK_STOP_DELAY               : self.__settings.get_float("General", "speak_stop_delay"),
			SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT : self.__settings.get_boolean("General", "get_wot_nick_from_ts_metadata"),
			SettingConstants.UPDATE_CACHE_IN_REPLAYS        : self.__settings.get_boolean("General", "update_cache_in_replays"),
			SettingConstants.CHAT_NICK_SEARCH_ENABLED       : self.__settings.get_boolean("General", "ts_nick_search_enabled"),
			SettingConstants.NICK_EXTRACT_PATTERNS          : [re.compile(pattern, re.IGNORECASE) for pattern in self.__settings.get_list("General", "nick_extract_patterns")],
			SettingConstants.NICK_MAPPINGS                  : {k.lower(): v.lower() for k, v in self.__settings.get_dict("NameMappings").iteritems()},
			SettingConstants.CHAT_CLIENT_HOST               : self.__settings.get_str("TSClientQueryService", "host"),
			SettingConstants.CHAT_CLIENT_PORT               : self.__settings.get_int("TSClientQueryService", "port"),
			SettingConstants.CHAT_CLIENT_POLLING_INTERVAL   : self.__settings.get_float("TSClientQueryService", "polling_interval"),
			SettingConstants.VOICE_CHAT_NOTIFY_ENABLED      : self.__settings.get_boolean("VoiceChatNotifications", "enabled"),
			SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED : self.__settings.get_boolean("VoiceChatNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ENABLED         : self.__settings.get_boolean("MinimapNotifications", "enabled"),
			SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED    : self.__settings.get_boolean("MinimapNotifications", "self_enabled"),
			SettingConstants.MINIMAP_NOTIFY_ACTION          : self.__settings.get_str("MinimapNotifications", "action"),
			SettingConstants.MINIMAP_NOTIFY_REPEAT_INTERVAL : self.__settings.get_float("MinimapNotifications", "repeat_interval")
		}
		self.__boundaries.usecase_load_settings(self.__loaded_values)
