# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2015  Janne Hakonen
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

g_settings = None
g_minimap = None
g_user_cache = None

class SettingsAdapter(object):

	def __init__(self, settings):
		self.__settings = settings

	def get_log_level(self):
		return self.__settings.get_int("General", "log_level")

	def get_ini_check_interval(self):
		return self.__settings.get_float("General", "ini_check_interval")

	def get_speak_stop_delay(self):
		return self.__settings.get_float("General", "speak_stop_delay")

	def get_wot_nick_from_ts_metadata(self):
		return self.__settings.get_boolean("General", "get_wot_nick_from_ts_metadata")

	def should_update_cache_in_replays(self):
		return self.__settings.get_boolean("General", "update_cache_in_replays")

	def is_ts_nick_search_enabled(self):
		return self.__settings.get_boolean("General", "ts_nick_search_enabled")

	def get_nick_extract_patterns(self):
		return [re.compile(pattern, re.IGNORECASE) for pattern in self.__settings.get_list("General", "nick_extract_patterns")]

	def get_name_mappings(self):
		return {k.lower(): v.lower() for k, v in self.__settings.get_dict("NameMappings").iteritems()}

	def get_client_query_host(self):
		return self.__settings.get_str("TSClientQueryService", "host")

	def get_client_query_port(self):
		return self.__settings.get_int("TSClientQueryService", "port")

	def get_client_query_interval(self):
		return self.__settings.get_float("TSClientQueryService", "polling_interval")

	def is_voice_chat_notifications_enabled(self):
		return self.__settings.get_boolean("VoiceChatNotifications", "enabled")

	def is_self_voice_chat_notifications_enabled(self):
		return self.__settings.get_boolean("VoiceChatNotifications", "self_enabled")

	def is_minimap_notifications_enabled(self):
		return self.__settings.get_boolean("MinimapNotifications", "enabled")

	def is_self_minimap_notifications_enabled(self):
		return self.__settings.get_boolean("MinimapNotifications", "self_enabled")

	def get_minimap_action(self):
		return self.__settings.get_str("MinimapNotifications", "action")

	def get_minimap_action_interval(self):
		return self.__settings.get_float("MinimapNotifications", "repeat_interval")

class MinimapAdapter(object):

	def __init__(self, minimap_ctrl):
		self.__minimap_ctrl = minimap_ctrl

	def set_player_speaking(self, player, speaking):
		if speaking:
			self.__minimap_ctrl.start(player.vehicle_id, g_settings.get_minimap_action(), g_settings.get_minimap_action_interval())
		else:
			self.__minimap_ctrl.stop(player.vehicle_id)

class UserCacheAdapter(object):

	def __init__(self, user_cache):
		self.__user_cache = user_cache

	def add_teamspeak_user(self, user):
		self.__user_cache.add_ts_user(user.nick, user.unique_id)

	def add_player(self, player):
		self.__user_cache.add_player(player.name, player.id)

	def pair(self, player, user):
		self.__user_cache.pair(player_id=player.id, ts_user_id=user.unique_id)

	def get_paired_player_ids(self, user):
		return self.__user_cache.get_paired_player_ids(user.unique_id)
