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
import collections
import struct
import time

from ..infrastructure import sharedmemory, clientquery, log

class TeamSpeakChatClientAdapter(object):

	def __init__(self, app):
		self.__ts = TeamSpeakClient()
		self.__app = app
		self.__ts.on("connected", self.__on_connected_to_ts)
		self.__ts.on("disconnected", self.__on_disconnected_from_ts)
		self.__ts.on("connected-server-name", self.__on_connected_to_ts_server)
		self.__ts.on("disconnected-server", self.__on_disconnected_from_ts_server)
		self.__ts.on("server-tab-changed", self.__on_server_tab_changed)
		self.__ts.on("user-added", self.__on_user_added)
		self.__ts.on("user-changed-client-nickname", self.__on_user_changed)
		self.__ts.on("user-changed-game-nickname", self.__on_user_changed)
		self.__ts.on("user-changed-talking", self.__on_user_changed)
		self.__ts.on("user-changed-my-channel", self.__on_user_changed)
		self.__ts.on("user-removed", self.__on_user_removed)
		self.__positional_data_api = PositionalDataAPI()
		self.__selected_schandlerid = None

	def init(self, plugin_filepath):
		self.__plugin_filepath = os.path.normpath(plugin_filepath)
		#self.__ts.connect()

	def set_host(self, host):
		self.__ts.set_host(host)

	def set_port(self, port):
		self.__ts.set_port(port)

	def set_polling_interval(self, interval):
		self.__ts.start_event_checking(interval)

	def get_current_channel_id(self, schandlerid):
		return self.__ts.get_my_cid(schandlerid)

	def get_installed_plugin_version(self):
		with InfoAPI() as api:
			return api.get_api_version()

	def get_plugin_filepath(self):
		return self.__plugin_filepath

	def install_plugin(self):
		threading.Thread(
			target = partial(
				subprocess.call,
				args  = [self.__plugin_filepath],
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

	def has_user(self, client_id):
		return self.__ts.has_user(schandlerid=client_id[0], clid=client_id[1])

	def get_user(self, client_id):
		assert self.has_user(client_id)
		return TeamSpeakUser(client_id, self.__ts)

	def get_users(self):
		for schandlerid, clid in self.__ts.iter_user_ids():
			yield TeamSpeakUser((schandlerid, clid), self.__ts)

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

	def get_clientquery(self):
		return self.__ts

	def __on_connected_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client. However, this
		doesn't mean that the client is connected to any TeamSpeak server.
		'''
		log.LOG_NOTE("Connected to TeamSpeak client")
		self.__app["show-chatclient-plugin-install-message"]()

	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		log.LOG_NOTE("Disconnected from TeamSpeak client")
		self.__app["clear-speakstatuses"]()
		self.__app["notify-chatclient-disconnected"]()

	def __on_connected_to_ts_server(self, server_name):
		log.LOG_NOTE("Connected to TeamSpeak server '{0}'".format(server_name))
		self.__app["notify-connected-to-chatserver"](server_name)
		self.__app["publish-gamenick-to-chatserver"]()

	def __on_disconnected_from_ts_server(self, schandlerid):
		log.LOG_NOTE("Disconnected from TeamSpeak server")
		self.__app["clear-speakstatuses"]()

	def __on_user_added(self, schandlerid, clid):
		client_id = (schandlerid, clid)
		self.__app["cache-chatuser"](client_id=client_id)
		self.__app["pair-chatuser-to-player"](client_id=client_id)
		self.__app["update-chatuser-speakstate"](client_id=client_id)

	def __on_user_removed(self, schandlerid, clid):
		client_id = (schandlerid, clid)
		self.__app["remove-chatuser"](client_id=client_id)

	def __on_user_changed(self, schandlerid, clid, **kwargs):
		client_id = (schandlerid, clid)
		self.__app["cache-chatuser"](client_id=client_id)
		self.__app["pair-chatuser-to-player"](client_id=client_id)
		self.__app["update-chatuser-speakstate"](client_id=client_id)

	def __on_server_tab_changed(self, schandlerid):
		log.LOG_NOTE("TeamSpeak client server tab was changed to {0}".format(schandlerid))
		self.__selected_schandlerid = schandlerid

class TeamSpeakUser(collections.Mapping):

	__KEYS = {
		"client_id": lambda self: self._get_client_id(),
		"nick": lambda self: self._query_parameter("client-nickname"),
		"game_nick": lambda self: self._query_parameter("game-nickname"),
		"unique_id": lambda self: self._query_parameter("client-unique-identifier"),
		"speaking": lambda self: self._query_parameter("talking"),
		"is_me": lambda self: self._query_parameter("is-me"),
		"in_my_channel": lambda self: self._query_parameter("my-channel")
	}

	def _get_client_id(self):
		return self.__client_id

	def _query_parameter(self, name):
		return self.__cq.get_user_parameter(self.__client_id[0], self.__client_id[1], name)

	def __init__(self, client_id, cq):
		self.__client_id = client_id
		self.__cq = cq

	def __getitem__(self, name):
		assert name in self.__KEYS
		return self.__KEYS[name](self)

	def __iter__(self):
		return iter(self.__KEYS.keys())

	def __len__(self):
		return len(self.__KEYS)

class TeamSpeakClient(clientquery.ClientQuery):

	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		super(TeamSpeakClient, self).__init__()
		self.__host = None
		self.__port = None
		self.__connect_requested = False
		self.__game_nicknames = {}
		self.on("connected", self.__on_connected)
		self.on("notifycurrentserverconnectionchanged", self.__on_notifycurrentserverconnectionchanged)
		self.on("connected-server", self.__on_connected_server)
		self.on("user-added", self.__on_user_added)
		self.on("user-changed-client-meta-data", self.__on_user_changed_client_meta_data)
		self.on("user-removed", self.__on_user_removed)
		self.on("error", self.__on_error)

	def set_host(self, host):
		self.__host = host

	def set_port(self, port):
		self.__port = port

	def connect(self):
		super(TeamSpeakClient, self).connect(self.__host, self.__port)

	def get_user_parameter(self, schandlerid, clid, parameter):
		if parameter == "game-nickname":
			client_id = (schandlerid, clid)
			return self.__game_nicknames.get(client_id, None)
		else:
			return super(TeamSpeakClient, self).get_user_parameter(schandlerid, clid, parameter)

	def set_game_nickname(self, name):
		for schandlerid in self.get_connected_schandlerids():
			clid = self.get_my_clid(schandlerid)
			metadata = self.get_user_parameter(schandlerid, clid, "client_meta_data")
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
				log.LOG_ERROR("currentschandlerid command failed", error)
			else:
				self.emit("server-tab-changed", int(result["schandlerid"]))
		self.command_currentschandlerid(callback=on_currentschandlerid_finish)

	def __on_notifycurrentserverconnectionchanged(self, args):
		self.emit("server-tab-changed", int(args[0]["schandlerid"]))

	def __on_connected_server(self, schandlerid):
		def on_servervariable_finish(error, result):
			name = ""
			if error:
				log.LOG_ERROR("servervariable command failed", error)
			else:
				name = result["virtualserver_name"]
			self.emit("connected-server-name", name)
		self.command_servervariable("virtualserver_name", schandlerid=schandlerid, callback=on_servervariable_finish)

	def __on_user_added(self, schandlerid, clid):
		metadata = self.get_user_parameter(schandlerid, clid, "client-meta-data")
		if metadata:
			game_nickname = self.__extract_game_nick_from_metadata(metadata)
			if game_nickname:
				client_id = (schandlerid, clid)
				self.__game_nicknames[client_id] = game_nickname

	def __on_user_changed_client_meta_data(self, schandlerid, clid, old_value, new_value):
		client_id = (schandlerid, clid)
		old_nickname = self.__game_nicknames.get(client_id, None)
		new_nickname = self.__extract_game_nick_from_metadata(new_value)
		if old_nickname != new_nickname:
			self.__game_nicknames[client_id] = new_nickname
			self.emit("user-changed-game-nickname", schandlerid=schandlerid, clid=clid, old_value=old_nickname, new_value=new_nickname)

	def __on_user_removed(self, schandlerid, clid):
		client_id = (schandlerid, clid)
		self.__game_nicknames.pop(client_id, None)

	def __extract_game_nick_from_metadata(self, metadata):
		matches = re.search(self.NICK_META_PATTERN, metadata)
		if matches:
			return matches.group(1)
		return None

	def __on_error(self, error):
		log.LOG_ERROR("An error occured", error)

class InfoAPI(sharedmemory.SharedMemory):

	NAME = "TessuModTSPluginInfo"
	SIZE = 1
	ACCESS_TYPE = sharedmemory.ACCESS_READ

	def get_api_version(self):
		self.seek(0)
		return struct.unpack("=B", self.read(1))[0]

class PositionalDataAPI(sharedmemory.SharedMemory):

	NAME = "TessuModTSPlugin3dAudio"
	SIZE = 1024
	ACCESS_TYPE = sharedmemory.ACCESS_WRITE

	def __init__(self):
		super(PositionalDataAPI, self).__init__()
		self.__previous_camera_position = None
		self.__previous_camera_direction = None
		self.__previous_positions = None
		self.__previous_timestamp = None

	def set_data(self, camera_position, camera_direction, positions):
		timestamp = int(time.time())
		if self.__has_data_updated(timestamp, camera_position, camera_direction, positions):
			self.seek(0)
			self.write(struct.pack("I", timestamp))
			self.write(self.__pack_float_vector(camera_position))
			self.write(self.__pack_float_vector(camera_direction))
			self.write(struct.pack("B", len(positions)))
			for clid, position in positions.iteritems():
				self.write(struct.pack("h", clid))
				self.write(self.__pack_float_vector(position))
			self.__previous_timestamp = timestamp
			self.__previous_camera_position = camera_position
			self.__previous_camera_direction = camera_direction
			self.__previous_positions = positions

	def __has_data_updated(self, timestamp, camera_position, camera_direction, positions):
		return (
			self.__previous_timestamp != timestamp
			or self.__previous_camera_position != camera_position
			or self.__previous_camera_direction != camera_direction
			or self.__previous_positions != positions
		)

	def __pack_float_vector(self, vector):
		return struct.pack("3f", vector[0], vector[1], vector[2])
