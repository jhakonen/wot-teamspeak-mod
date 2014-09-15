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

import socket
import clientquery
import time
import re
from debug_utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
import Event
import select
from utils import with_args, ThreadCaller
import BigWorld

RETRY_TIMEOUT = 10

def noop(*args, **kwargs):
	pass

class ConnectionError(Exception):
	pass

class ClientQueryError(Exception):
	def __init__(self, code, message):
		Exception.__init__(self, message)
		self.code = code

class TS3Client(object):
	
	HOST = "localhost"
	PORT = 25639
	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		self.clients = {}
		self.talk_states = {}
		self.my_client_id = None
		self.my_wot_nickname = None
		self.callback_handles = []
		self.connected = False
		self.socket = None
		self.handler = None
		self.clientuidfromclid_cache = {}
		self.thread_caller = ThreadCaller()

		self.on_connected = Event.Event()
		self.on_disconnected = Event.Event()
		self.on_talk_status_changed = Event.Event()

	def connect(self):
		def on_connect_to_ts(err, socket):
			if err:
				LOG_DEBUG(err)
				LOG_ERROR("Failed to connect TeamSpeak clientquery interface at {0}:{1}".format(self.HOST, self.PORT))
				self.call_later(RETRY_TIMEOUT, self.connect)
			else:
				LOG_NOTE("Connected to TeamSpeak clientquery interface")
				self.socket = socket

		def set_connected():
			self.connected = True
			self.on_connected()

		def register_notifications():
			self.handler.send_command("clientnotifyregister schandlerid=0 event=notifytalkstatuschange", on_command_finish)
			self.handler.send_command("clientnotifyregister schandlerid=0 event=notifycliententerview", on_command_finish)
			self.handler.send_command("clientnotifyregister schandlerid=0 event=notifyclientupdated", on_command_finish)
			self.handler.send_command("clientnotifyregister schandlerid=0 event=notifyclientuidfromclid", on_command_finish)

		def on_command_finish(err, data):
			if err:
				LOG_ERROR("command failed:", err)
				raise ClientQueryError(*err)

		def ping():
			'''Ping TS client with some command to keep connection alive.'''
			self.get_my_client_id()
			self.call_later(300, ping)

		self.connected = False
		self.socket = None
		self.handler = ClientQueryHandler(self)
		self.cancel_all_call_laters()
		self.handler.on_ready += set_connected
		self.handler.on_ready += register_notifications
		self.handler.on_ready += ping
		self.connect_to_ts(on_connect_to_ts)

	def check_events(self):
		try:
			self.thread_caller.tick()

			if self.socket is not None:
				read, write, err = select.select([self.socket], [self.socket], [self.socket], 0)
				if err:
					raise ConnectionError("Error in socket")
				if read:
					data = self.socket.recv(1024)
					LOG_DEBUG("<<", data)
					if len(data) == 0:
						raise ConnectionError("Unable to recv data")
					self.handler.handle_in_data(data)
				if write:
					if self.handler.has_out_data():
						count = self.socket.send(self.handler.get_out_data())
						LOG_DEBUG(">>", self.handler.get_out_data())
						if count == 0:
							raise ConnectionError("Unable to send data")
						self.handler.reduce_out_data(count)
				self.handler.handle_out_commands()

		except (ConnectionError, ClientQueryError, socket.error):
			if self.socket is not None:
				self.socket.close()
				self.socket = None
			if self.connected:
				LOG_CURRENT_EXCEPTION()
				self.connected = False
				self.on_disconnected()
			self.call_later(RETRY_TIMEOUT, self.connect)

	def connect_to_ts(self, callback):
		def create_socket():
			# executed in another thread
			s = socket.create_connection((self.HOST, self.PORT))
			s.setblocking(0)
			return s
		self.thread_caller.call(create_socket, callback)

	def call_later(self, secs, func):
		'''Enhanced version of BigWorld.callback() which keeps track of
		waiting callbacks.
		'''
		def wrapper():
			try:
				func()
			finally:
				try:
					self.callback_handles.remove(handle)
				except ValueError:
					# protect against 'handle' not being in the list anymore
					# due of cancel_all_call_laters()
					pass
		handle = BigWorld.callback(secs, wrapper)
		self.callback_handles.append(handle)

	def cancel_all_call_laters(self):
		for handle in self.callback_handles:
			BigWorld.cancelCallback(handle)
		self.callback_handles = []

	def get_matching_method_names(self, pattern):
		for attr in dir(self):
			matches = re.match(pattern, attr)
			if matches:
				yield attr, matches.group(1)

	def get_my_client_id(self, callback=noop):
		def on_whoami(err, lines):
			if err:
				LOG_ERROR("get_my_client_id() failed, error:", err)
				callback(err, None)
			else:
				client_id = int(clientquery.getParamValue(lines[0], 'clid'))
				callback(None, client_id)
		self.handler.send_command("whoami", on_whoami)

	def get_client_meta_data(self, client_id, callback=noop):
		def on_finish(err, lines):
			if err:
				LOG_ERROR("get_client_meta_data failed:", err)
				callback(err, "")
			else:
				data = clientquery.getParamValue(lines[0], "client_meta_data")
				if data is None:
					LOG_ERROR("get_client_meta_data failed, value:", data)
					callback(None, "")
				else:
					callback(None, data)
		self.handler.send_command("clientvariable clid={0} client_meta_data".format(client_id), on_finish)

	def get_wot_nickname(self, client_id, callback=noop):
		def on_finish(err, data):
			if err:
				callback(err, None)
			else:
				matches = re.search(self.NICK_META_PATTERN, data)
				if matches:
					callback(None, matches.group(1))
				else:
					callback(None, "")
		self.get_client_meta_data(client_id, on_finish)

	def set_wot_nickname(self, name):
		def on_get_my_client_id(err, client_id):
			def on_get_client_meta_data(err, data):
				if data is not None:
					new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
					if re.search(self.NICK_META_PATTERN, data):
						data = re.sub(self.NICK_META_PATTERN, new_tag, data)
					else:
						data += new_tag
					self.handler.send_command("clientupdate client_meta_data={0}".format(data))
					self.invalidate_client_id(client_id)

			if client_id is not None:
				self.get_client_meta_data(client_id, on_get_client_meta_data)

		self.get_my_client_id(on_get_my_client_id)

	def invalidate_client_id(self, client_id):
		try:
			del self.clients[client_id]
		except:
			pass

	def get_client(self, client_id, callback=noop):
		def on_get_client_info(err, client_info):
			if err:
				callback(err, None)
			else:
				self.save_client_data(
					client_id=client_info[0],
					client_nick=client_info[1],
					wot_nick=client_info[2]
				)
				callback(None, self.clients[client_id])

		if client_id in self.clients:
			callback(None, self.clients[client_id])
		else:
			self.get_client_info(client_id, on_get_client_info)

	def get_clientlist(self, callback=noop):
		def on_clientlist(err, lines):
			if err:
				LOG_ERROR("get_clientlist() failed, error:", err)
				callback(err, None)
			else:
				clientlist = []
				for client_data in lines[0].split('|'):
					clientlist.append((
						int(clientquery.getParamValue(client_data, 'clid')),
						clientquery.getParamValue(client_data, 'client_nickname')
					))
				callback(None, clientlist)
		self.handler.send_command("clientlist", on_clientlist)

	def get_client_info(self, client_id, callback=noop):
		def on_query_clientgetuidfromclid(err, ts_nickname):
			def on_get_wot_nickname(err, wot_nickname):
				if err:
					callback(err, None)
				else:
					callback(None, (client_id, ts_nickname, wot_nickname))
			if err:
				callback(err, None)
			else:
				self.get_wot_nickname(client_id, on_get_wot_nickname)
		self.query_clientgetuidfromclid(client_id, on_query_clientgetuidfromclid)

	def query_clientgetuidfromclid(self, client_id, callback=noop):
		try:
			del self.clientuidfromclid_cache[client_id]
		except KeyError:
			pass

		wait_end_t = time.time() + 10

		def wait_notify():
			if client_id in self.clientuidfromclid_cache:
				callback(None, self.clientuidfromclid_cache[client_id])
			elif time.time() < wait_end_t:
				self.call_later(0.1, wait_notify)
			else:
				LOG_ERROR("Event notifyclientuidfromclid not received")
				callback("Event notifyclientuidfromclid not received", None)

		def on_clientgetuidfromclid(err, lines):
			if err:
				LOG_ERROR("clientgetuidfromclid failed, error:", err)
				callback(err, None)
			else:
				wait_notify()
		self.handler.send_command("clientgetuidfromclid clid={0}".format(client_id), on_clientgetuidfromclid)

	def on_notifytalkstatuschange_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		talking = int(clientquery.getParamValue(line, 'status')) == 1
		if client_id not in self.talk_states:
			self.talk_states[client_id] = False
		if self.talk_states[client_id] != talking:
			self.talk_states[client_id] = talking

			def on_get_client(err, client):
				if not err:
					self.on_talk_status_changed({
						"ts": client["ts-nickname"],
						"wot": client["wot-nickname"]
					}, talking)
			self.get_client(client_id, on_get_client)

	def on_notifycliententerview_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		self.invalidate_client_id(client_id)

	def on_notifyclientupdated_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		self.invalidate_client_id(client_id)

	def on_notifyclientuidfromclid_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		nickname = clientquery.getParamValue(line, "nickname")
		self.clientuidfromclid_cache[client_id] = nickname

	def save_client_data(self, client_id, client_nick, wot_nick):
		self.clients[client_id] = {
			"ts-nickname": client_nick,
			"wot-nickname": wot_nick
		}

class ClientQueryHandler(object):
	def __init__(self, event_receiver):
		self.event_handlers = {}
		self.in_buffer = ""
		self.out_buffer = ""
		self.ts_client_checked = False
		self.commands = []
		self.data_in_handler = self._handle_in_data_welcome_message

		self.on_ready = Event.Event()

		for attr in dir(event_receiver):
			matches = re.match("on_(.+)_ts3_event", attr)
			if matches:
				name = matches.group(1)
				self.event_handlers[name] = getattr(event_receiver, attr)

	def handle_in_data(self, data):
		self.in_buffer = data
		splits = self.in_buffer.split("\n\r")
		self.in_buffer = splits[-1]
		lines = splits[:-1]
		for line in lines:
			self.data_in_handler(line)

	def _handle_in_data_welcome_message(self, line):
		line = line.lower()
		if not self.ts_client_checked:
			if "ts3 client" in line:
				self.ts_client_checked = True
			else:
				raise RuntimeError("Not TS client query protocol")
		if "selected schandlerid" in line:
			self.data_in_handler = self._handle_in_data_actions
			self.on_ready()

	def _handle_in_data_actions(self, line):
		if line.split(None, 1)[0] in self.event_handlers:
			self.event_handlers[line.split(None, 1)[0]](line)
			return

		try:
			cmd = self.commands[0]
			cmd.handle_line(line)
			if cmd.is_done:
				self.commands.remove(cmd)
		except IndexError:
			pass

	def handle_out_commands(self):
		try:
			cmd = self.commands[0]
			if not cmd.is_sent:
				self.out_buffer += cmd.command + "\n\r"
				cmd.is_sent = True
		except IndexError:
			pass

	def has_out_data(self):
		return len(self.out_buffer) != 0

	def get_out_data(self):
		return self.out_buffer

	def reduce_out_data(self, byte_count):
		self.out_buffer = self.out_buffer[byte_count:]

	def send_command(self, command, callback=noop):
		self.commands.append(ClientQueryCommand(command, callback))

class ClientQueryCommand(object):

	def __init__(self, command, callback):
		self.command = command
		self.callback = callback
		self.response_lines = []
		self.is_done = False
		self.is_sent = False

	def handle_line(self, line):
		if line.startswith("error "):
			err = clientquery.checkError([line])
			try:
				if err:
					self.callback(err, None)
				else:
					self.callback(None, self.response_lines)
			finally:
				self.is_done = True
		else:
			self.response_lines.append(line)
