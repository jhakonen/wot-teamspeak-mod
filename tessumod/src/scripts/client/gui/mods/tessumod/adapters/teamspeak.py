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

import os
import threading
import subprocess
from functools import partial

from ..infrastructure import mytsplugin, utils, log

class TeamSpeakChatClientAdapter(object):

	def __init__(self, eventloop, ts, usecases):
		self.__ts = ts
		self.__usecases = usecases
		self.__ts.on_connected += self.__on_connected_to_ts
		self.__ts.on_disconnected += self.__on_disconnected_from_ts
		self.__ts.on_connected_to_server += self.__on_connected_to_ts_server
		self.__ts.on_disconnected_from_server += self.__on_disconnected_from_ts_server
		self.__ts.users.on_added += self.__on_user_added
		self.__ts.users.on_removed += self.__on_user_removed
		self.__ts.users.on_modified += self.__on_user_modified
		self.__ts.on_channel_changed += self.__current_chat_channel_changed
		self.__positional_data_api = mytsplugin.PositionalDataAPI()
		self.__check_repeater = eventloop.create_callback_repeater(self.__ts.check_events)

	def set_host(self, host):
		self.__ts.HOST = host

	def set_port(self, port):
		self.__ts.PORT = port

	def set_polling_interval(self, interval):
		self.__check_repeater.start(interval)

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

	def set_game_nickname(self, nick):
		self.__ts.set_wot_nickname(nick)

	def enable_positional_data(self, enabled):
		if enabled:
			self.__positional_data_api.open()
		else:
			self.__positional_data_api.close()

	def update_positional_data(self, camera_position, camera_direction, positions):
		if self.__positional_data_api.is_open():
			self.__positional_data_api.set_data(camera_position, camera_direction, positions)

	def __on_connected_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client. However, this
		doesn't mean that the client is connected to any TeamSpeak server.
		'''
		log.LOG_NOTE("Connected to TeamSpeak client")
		self.__usecases.usecase_show_chat_client_plugin_install_message()

	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		log.LOG_NOTE("Disconnected from TeamSpeak client")
		self.__usecases.usecase_clear_speak_statuses()
		self.__usecases.usecase_notify_chat_client_disconnected()

	def __on_connected_to_ts_server(self, server_name):
		log.LOG_NOTE("Connected to TeamSpeak server '{0}'".format(server_name))
		self.__usecases.usecase_notify_connected_to_chat_server(server_name)
		self.__usecases.usecase_publish_game_nick_to_chat_server()

	def __on_disconnected_from_ts_server(self):
		log.LOG_NOTE("Disconnected from TeamSpeak server")
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
		self.__usecases.usecase_pair_chat_user_to_player(user["client_id"])
		self.__usecases.usecase_update_chat_user_speak_state(user["client_id"])

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
		self.__usecases.usecase_pair_chat_user_to_player(user["client_id"])
		self.__usecases.usecase_update_chat_user_speak_state(user["client_id"])

	def __current_chat_channel_changed(self):
		self.__usecases.usecase_change_chat_channel(self.get_current_channel_id())
