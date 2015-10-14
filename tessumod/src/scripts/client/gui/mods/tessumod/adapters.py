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
import os
import threading
import subprocess
from functools import partial

from infrastructure.utils import LOG_NOTE
from infrastructure import mytsplugin, utils

class TeamSpeakChatClientAdapter(object):

	def __init__(self, ts, usecases):
		self.__ts = ts
		self.__usecases = usecases
		self.__ts.on_connected += self.__on_connected_to_ts
		self.__ts.on_disconnected += self.__on_disconnected_from_ts
		self.__ts.on_disconnected_from_server += self.__on_disconnected_from_ts_server
		self.__ts.users.on_added += self.__on_user_added
		self.__ts.users.on_removed += self.__on_user_removed
		self.__ts.users.on_modified += self.__on_user_modified
		self.__ts.on_channel_changed += self.__current_chat_channel_changed

	def get_current_channel_id(self):
		return self.__ts.get_current_channel_id()

	def get_installed_plugin_version(self):
		with mytsplugin.InfoAPI() as api:
			return api.get_api_version()

	def install_plugin(self):
		threading.Thread(
			target = partial(
				subprocess.call,
				args  = [os.path.normpath(utils.get_plugin_installer_path())],
				shell = True
			)
		).start()

	def show_plugin_info_url(self, url):
		subprocess.call(["start", url], shell=True)

	def __on_connected_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client. However, this
		doesn't mean that the client is connected to any TeamSpeak server.
		'''
		LOG_NOTE("Connected to TeamSpeak client")
		self.__usecases.usecase_show_chat_client_plugin_install_message()

	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		LOG_NOTE("Disconnected from TeamSpeak client")
		self.__usecases.usecase_clear_speak_statuses()
		self.__usecases.usecase_notify_chat_client_disconnected()

	def __on_disconnected_from_ts_server(self):
		LOG_NOTE("Disconnected from TeamSpeak server")
		self.__usecases.usecase_clear_speak_statuses()

	def __on_user_added(self, client_id):
		user = self.__ts.users[client_id]
		self.__usecases.usecase_insert_chat_user(
			nick = user["nick"],
			game_nick = user["wot_nick"],
			client_id = user["client_id"],
			unique_id = user["unique_id"],
			channel_id = user["channel_id"],
			speaking = user["speaking"]
		)

	def __on_user_removed(self, client_id):
		self.__usecases.usecase_remove_chat_user(client_id=client_id)

	def __on_user_modified(self, client_id):
		user = self.__ts.users[client_id]
		self.__usecases.usecase_insert_chat_user(
			nick = user["nick"],
			game_nick = user["wot_nick"],
			client_id = user["client_id"],
			unique_id = user["unique_id"],
			channel_id = user["channel_id"],
			speaking = user["speaking"]
		)

	def __current_chat_channel_changed(self):
		self.__usecases.usecase_change_chat_channel(self.get_current_channel_id())

class SettingsAdapter(object):

	def __init__(self, settings):
		self.__settings = settings

	def get_log_level(self):
		return self.__settings.get_int("General", "log_level")

	def get_ini_check_interval(self):
		return self.__settings.get_float("General", "ini_check_interval")

	def get_speak_stop_delay(self):
		return self.__settings.get_float("General", "speak_stop_delay")

	def get_game_nick_from_chat_metadata(self):
		return self.__settings.get_boolean("General", "get_wot_nick_from_ts_metadata")

	def should_update_cache_in_replays(self):
		return self.__settings.get_boolean("General", "update_cache_in_replays")

	def is_chat_nick_search_enabled(self):
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

class ChatIndicatorAdapter(object):

	def __init__(self, voip_manager):
		self.__voip_manager = voip_manager
		self.__speakers = set()

	def set_player_speaking(self, player, speaking):
		if speaking and player["id"] not in self.__speakers:
			self.__speakers.add(player["id"])
			self.__voip_manager.onPlayerSpeaking(player["id"], True)
		elif not speaking and player["id"] in self.__speakers:
			self.__speakers.remove(player["id"])
			self.__voip_manager.onPlayerSpeaking(player["id"], False)

	def clear_all_players_speaking(self):
		for speaker in self.__speakers:
			self.__voip_manager.onPlayerSpeaking(speaker, False)
		self.__speakers.clear()

class MinimapAdapter(object):

	def __init__(self, minimap_ctrl, settings_api):
		self.__minimap_ctrl = minimap_ctrl
		self.__settings_api = settings_api

	def set_player_speaking(self, player, speaking):
		if speaking:
			self.__minimap_ctrl.start(player["vehicle_id"], self.__settings_api.get_minimap_action(), self.__settings_api.get_minimap_action_interval())
		else:
			self.__minimap_ctrl.stop(player["vehicle_id"])

	def clear_all_players_speaking(self):
		self.__minimap_ctrl.stop_all()

class UserCacheAdapter(object):

	def __init__(self, user_cache):
		self.__user_cache = user_cache

	def add_chat_user(self, nick, unique_id):
		self.__user_cache.add_ts_user(nick, unique_id)

	def add_player(self, id, name):
		self.__user_cache.add_player(name, id)

	def pair(self, player_id, user_unique_id):
		self.__user_cache.pair(player_id=player_id, ts_user_id=user_unique_id)

	def get_paired_player_ids(self, user_unique_id):
		return self.__user_cache.get_paired_player_ids(user_unique_id)

class NotificationsAdapter(object):

	def __init__(self, notifications, usecases):
		self.__notifications = notifications
		self.__usecases = usecases
		self.__notifications.add_event_handler(notifications.TSPLUGIN_INSTALL, self.__on_plugin_install)
		self.__notifications.add_event_handler(notifications.TSPLUGIN_IGNORED, self.__on_plugin_ignore_toggled)
		self.__notifications.add_event_handler(notifications.TSPLUGIN_MOREINFO, self.__on_plugin_moreinfo_clicked)

	def show_warning_message(self, message):
		self.__notifications.push_warning_message(message)

	def show_plugin_install_message(self, **data):
		self.__notifications.push_ts_plugin_install_message(
			moreinfo_url = "https://github.com/jhakonen/wot-teamspeak-mod/wiki/TeamSpeak-Plugins#tessumod-plugin",
			ignore_state = "off"
		)

	def __on_plugin_install(self, type_id, msg_id, data):
		self.__usecases.usecase_install_chat_client_plugin()

	def __on_plugin_ignore_toggled(self, type_id, msg_id, data):
		new_state = False if data["ignore_state"] == "on" else True
		data["ignore_state"] = "on" if new_state else "off"
		self.__usecases.usecase_ignore_chat_client_plugin_install_message(new_state)
		self.__notifications.update_message(type_id, msg_id, data)

	def __on_plugin_moreinfo_clicked(self, type_id, msg_id, data):
		self.__usecases.usecase_show_chat_client_plugin_info_url(data["moreinfo_url"])
