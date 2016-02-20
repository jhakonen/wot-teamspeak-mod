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
import re

from ..infrastructure import mytsplugin, clientquery, utils, log

class TeamSpeakChatClientAdapter(object):

	def __init__(self, eventloop, boundaries):
		self.__ts = TeamSpeakClient()
		self.__ts.set_eventloop(eventloop)
		self.__boundaries = boundaries
		self.__ts.on("connected", self.__on_connected_to_ts)
		self.__ts.on("disconnected", self.__on_disconnected_from_ts)
		self.__ts.on("connected-server-name", self.__on_connected_to_ts_server)
		self.__ts.on("disconnected-server", self.__on_disconnected_from_ts_server)
		self.__ts.on("server-tab-changed", self.__on_server_tab_changed)
		self.__ts.on("client-user-added", self.__on_user_added)
		self.__ts.on("client-user-changed", self.__on_user_changed)
		self.__ts.on("client-user-removed", self.__on_user_removed)
		self.__positional_data_api = mytsplugin.PositionalDataAPI()
		self.__selected_schandlerid = None

	def init(self):
		self.__ts.connect()

	def set_host(self, host):
		self.__ts.set_host(host)

	def set_port(self, port):
		self.__ts.set_port(port)

	def set_polling_interval(self, interval):
		self.__ts.start_event_checking(interval)

	def get_current_channel_id(self, schandlerid):
		return self.__ts.get_my_cid(schandlerid)

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
		self.__ts.set_game_nickname(nick)

	def enable_positional_data(self, enabled):
		if enabled:
			self.__positional_data_api.open()
		else:
			self.__positional_data_api.close()

	def update_positional_data(self, camera_position, camera_direction, positions):
		if self.__selected_schandlerid is not None:
			# positional data api doesn't support users other than those in
			# currently selected schandlerid and expects only clid not
			# combination of clid + schandlerid
			fixed_positions = {}
			for client_id in positions:
				if client_id[0] == self.__selected_schandlerid:
					fixed_positions[client_id[1]] = positions[client_id]

			if self.__positional_data_api.is_open():
				self.__positional_data_api.set_data(camera_position, camera_direction, fixed_positions)

	def __on_connected_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client. However, this
		doesn't mean that the client is connected to any TeamSpeak server.
		'''
		log.LOG_NOTE("Connected to TeamSpeak client")
		self.__boundaries.usecase_show_chat_client_plugin_install_message()

	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		log.LOG_NOTE("Disconnected from TeamSpeak client")
		self.__boundaries.usecase_clear_speak_statuses()
		self.__boundaries.usecase_notify_chat_client_disconnected()

	def __on_connected_to_ts_server(self, server_name):
		log.LOG_NOTE("Connected to TeamSpeak server '{0}'".format(server_name))
		self.__boundaries.usecase_notify_connected_to_chat_server(server_name)
		self.__boundaries.usecase_publish_game_nick_to_chat_server()

	def __on_disconnected_from_ts_server(self, schandlerid):
		log.LOG_NOTE("Disconnected from TeamSpeak server")
		self.__boundaries.usecase_clear_speak_statuses()

	def __on_user_added(self, user_data):
		client_id = self.__get_user_client_id(user_data)
		input = self.__get_user_additional_data(user_data)
		self.__boundaries.usecase_insert_chat_user(client_id=client_id, **input)
		self.__boundaries.usecase_pair_chat_user_to_player(client_id=client_id)
		self.__boundaries.usecase_update_chat_user_speak_state(client_id=client_id)

	def __get_user_client_id(self, user_data):
		return (user_data["schandlerid"], user_data["clid"])

	def __get_user_additional_data(self, user_data):
		input = {}
		if "client_nickname" in user_data:
			input["nick"] = user_data["client_nickname"]
		if "game_nickname" in user_data:
			input["game_nick"] = user_data["game_nickname"]
		if "client_unique_identifier" in user_data:
			input["unique_id"] = user_data["client_unique_identifier"]
		if "cid" in user_data:
			input["channel_id"] = user_data["cid"]
		if "talking" in user_data:
			input["speaking"] = user_data["talking"]
		if "is_me" in user_data:
			input["is_me"] = user_data["is_me"]
		if "my_channel" in user_data:
			input["in_my_channel"] = user_data["my_channel"]
		return input		

	def __on_user_removed(self, user_data):
		client_id = self.__get_user_client_id(user_data)
		self.__boundaries.usecase_remove_chat_user(client_id=client_id)

	def __on_user_changed(self, user_data):
		client_id = self.__get_user_client_id(user_data)
		input = self.__get_user_additional_data(user_data)
		self.__boundaries.usecase_insert_chat_user(client_id=client_id, **input)
		self.__boundaries.usecase_pair_chat_user_to_player(client_id=client_id)
		self.__boundaries.usecase_update_chat_user_speak_state(client_id=client_id)

	def __on_server_tab_changed(self, schandlerid):
		log.LOG_NOTE("TeamSpeak client server tab was changed to {0}".format(schandlerid))
		self.__selected_schandlerid = schandlerid

class TeamSpeakClient(clientquery.ClientQuery):

	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		super(TeamSpeakClient, self).__init__()
		self.__host = None
		self.__port = None
		self.__connect_requested = False
		self.on("connected", self.__on_connected)
		self.on("notifycurrentserverconnectionchanged", self.__on_notifycurrentserverconnectionchanged)
		self.on("connected-server", self.__on_connected_server)
		self.on("user-added", self.__on_server_user_added)
		self.on("user-changed", self.__on_server_user_changed)
		self.on("user-removed", self.__on_server_user_removed)
		self.on("error", self.__on_error)

	def set_host(self, host):
		self.__host = host

	def set_port(self, port):
		self.__port = port

	def connect(self):
		super(TeamSpeakClient, self).connect(self.__host, self.__port)

	def set_game_nickname(self, name):
		for schandlerid in self.get_connected_schandlerids():
			metadata = self.get_user(schandlerid, lambda user: user["is_me"]).get("client_meta_data", None)
			if not metadata:
				metadata = ""
			new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
			if re.search(self.NICK_META_PATTERN, metadata):
				metadata = re.sub(self.NICK_META_PATTERN, new_tag, metadata)
			else:
				metadata += new_tag
			self.command_clientupdate("client_meta_data", metadata)

	def __on_connected(self):
		self.register_notify("notifycurrentserverconnectionchanged")

		def on_currentschandlerid_finish(error, result):
			if error:
				log.LOG_ERROR(error)
			else:
				self.emit("server-tab-changed", int(result["schandlerid"]))
		self.command_currentschandlerid(callback=on_currentschandlerid_finish)

	def __on_notifycurrentserverconnectionchanged(self, args):
		self.emit("server-tab-changed", int(args[0]["schandlerid"]))

	def __on_connected_server(self, schandlerid):
		def on_servervariable_finish(error, result):
			name = ""
			if error:
				log.LOG_ERROR(error)
			else:
				name = result["virtualserver_name"]
			self.emit("connected-server-name", name)
		self.command_servervariable("virtualserver_name", schandlerid=schandlerid, callback=on_servervariable_finish)

	def __on_server_user_added(self, **kwargs):
		if "client_meta_data" in kwargs:
			kwargs["game_nickname"] = self.__extract_game_nick_from_metadata(kwargs["client_meta_data"])
		self.emit("client-user-added", kwargs)

	def __on_server_user_changed(self, **kwargs):
		if "client_meta_data" in kwargs:
			kwargs["game_nickname"] = self.__extract_game_nick_from_metadata(kwargs["client_meta_data"])
		self.emit("client-user-changed", kwargs)

	def __on_server_user_removed(self, **kwargs):
		self.emit("client-user-removed", kwargs)

	def __extract_game_nick_from_metadata(self, metadata):
		matches = re.search(self.NICK_META_PATTERN, metadata)
		if matches:
			return matches.group(1)
		return ""

	def __on_error(self, error):
		log.LOG_ERROR(error)
