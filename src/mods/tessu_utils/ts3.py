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

from threading import Thread
from Queue import Empty, Queue
import socket
import clientquery
import time
import re
from debug_utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
import Event
import select
from utils import with_args

RETRY_TIMEOUT = 10

class NotConnectedToTSError(Exception):
	pass

class StopExecution(Exception):
	pass

class TS3Client(object):

	def __init__(self):
		self.connection = WOTTS3Connection()
		self.thread = Thread(target=self.connection.execute, name="TeamSpeak Client Thread")
		self.on_talk_status_changed = Event.Event()
		self.on_connected = Event.Event()
		self.on_disconnected = Event.Event()

	def connect(self):
		self.thread.start()

	def disconnect(self):
		self.connection.stop = True
		self.thread.join()

	def set_wot_nickname(self, nickname):
		self.connection.command_queue.put(("set_wot_nickname", (nickname,)), block=False)

	def check_events(self):
		if not self.thread.is_alive():
			raise NotConnectedToTSError("Not connected to TeamSpeak")
		try:
			event = self.connection.event_queue.get(block=False)
		except Empty:
			return
		event_type = event[0]
		if event_type == "talk_status_changed":
			self.on_talk_status_changed(event[1], event[2])
		elif event_type == "connected":
			self.on_connected()
		elif event_type == "disconnected":
			self.on_disconnected()

class ClientQueryHandler(object):
	def __init__(self, event_receiver):
		self.event_handlers = {}
		self.reset()
		for attr in dir(event_receiver):
			matches = re.match("on_(.+)_ts3_event", attr)
			if matches:
				name = matches.group(1)
				self.event_handlers[name] = getattr(event_receiver, attr)

	def reset(self):
		self.in_buffer = ""
		self.out_buffer = ""
		self.ts_client_checked = False
		self.on_ready = Event.Event()
		self.commands = []
		self.data_in_handler = self._handle_in_data_welcome_message

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

	def send_command(self, command, callback, errback):
		self.commands.append(ClientQueryCommand(command, callback, errback))

class ClientQueryCommand(object):

	def __init__(self, command, callback, errback):
		self.command = command
		self.callback = callback
		self.errback = errback
		self.response_lines = []
		self.is_done = False
		self.is_sent = False

	def handle_line(self, line):
		if line.startswith("error "):
			err = clientquery.checkError([line])
			if err and self.errback:
				self.errback(err)
			elif self.callback:
				self.callback(self.response_lines)
			self.is_done = True
		else:
			self.response_lines.append(line)

class EventLoop(object):

	def __init__(self):
		self.on_tick = Event.Event()
		self._callback_events = []

	def set_socket(self, socket, handler):
		self._socket = socket
		self._handler = handler

	def callback(self, secs, func):
		self._callback_events.append((time.time()+secs, func))

	def stop(self):
		self._is_stopped = True

	def run(self):
		self._is_stopped = False

		while not self._is_stopped:
			read, write, err = select.select([self._socket], [self._socket], [self._socket], 0.1)
			if err:
				raise ConnectionError("Error in socket")
			if read:
				data = self._socket.recv(1024)
				LOG_DEBUG("<<", data)
				if len(data) == 0:
					raise ConnectionError("Unable to recv data")
				self._handler.handle_in_data(data)
			if write:
				if self._handler.has_out_data():
					count = self._socket.send(self._handler.get_out_data())
					LOG_DEBUG(">>", self._handler.get_out_data())
					if count == 0:
						raise ConnectionError("Unable to send data")
					self._handler.reduce_out_data(count)

			t = time.time()
			for event in self._callback_events:
				if t > event[0]:
					self._callback_events.remove(event)
					event[1]()

			self.on_tick()

class ConnectionError(Exception):
	pass

class TS3Connection(object):
	
	HOST = "localhost"
	PORT = 25639
	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		self.socket = None
		self.received_data = ""
		self.clients = {}
		self.talk_states = {}
		self.my_client_id = None
		self.ts3_event_handlers = {}
		self.stop = False
		self.command_queue = Queue()
		self.event_queue = Queue()
		self.handler = ClientQueryHandler(self)

	def execute(self):
		self.stop = False
		self.connected = False

		try:
			while True:
				try:
					self.raise_on_stop()
					self.socket = self.connect_to_ts()
					self.handler.reset()

					def set_connected():
						self.connected = True
						self.event_queue.put(("connected",), block=False)

					def register_notifications():
						self.handler.send_command("clientnotifyregister schandlerid=0 event=notifytalkstatuschange", None, on_command_error)
						self.handler.send_command("clientnotifyregister schandlerid=0 event=notifycliententerview", None, on_command_error)

					def update_info():
						def on_error(err):
							if err[0] != 1794: # not connected to TS server
								LOG_ERROR(err)
							self.loop.callback(RETRY_TIMEOUT, update_info)

						def on_whoami(lines):
							self.my_client_id = int(clientquery.getParamValue(lines[0], 'clid'))
						self.handler.send_command("whoami", on_whoami, on_error)

						def on_clientlist(lines):
							for client_data in lines[0].split('|'):
								client_id = int(clientquery.getParamValue(client_data, 'clid'))
								client_nick = clientquery.getParamValue(client_data, 'client_nickname')
								self.call_handler("on_client_found", client_id, client_nick)
							# refresh info
							self.loop.callback(60, update_info)
						self.handler.send_command("clientlist", on_clientlist, on_error)

					def on_command_error(err):
						LOG_ERROR("command failed:", err)
						raise clientquery.Error(*err)

					self.handler.on_ready += set_connected
					self.handler.on_ready += register_notifications
					self.handler.on_ready += update_info

					def stop_on_request():
						if self.stop:
							self.loop.stop()

					self.loop = EventLoop()
					self.loop.on_tick += self.handler.handle_out_commands
					self.loop.on_tick += self.tick
					self.loop.on_tick += stop_on_request
					self.loop.set_socket(self.socket, self.handler)
					self.loop.run()

				except (ConnectionError, clientquery.Error, socket.error):
					if self.connected:
						LOG_CURRENT_EXCEPTION()
						self.connected = False
						self.event_queue.put(("disconnected",), block=False)
					self.sleep(RETRY_TIMEOUT)

		except StopExecution:
			LOG_NOTE("Stopping TeamSpeak thread on StopExecution request")

		if self.socket:
			self.socket.close()

	def raise_on_stop(self):
		if self.stop:
			raise StopExecution()

	def connect_to_ts(self):
		# create TCP socket and connect to clientquery on localhost:25639
		try:
			s = socket.create_connection((self.HOST, self.PORT))
			s.setblocking(0)
			return s
		except socket.error:
			LOG_ERROR("Failed to connect TeamSpeak clientquery interface at {0}:{1}".format(self.HOST, self.PORT))
			raise

	def get_matching_method_names(self, pattern):
		for attr in dir(self):
			matches = re.match(pattern, attr)
			if matches:
				yield attr, matches.group(1)

	def get_client_meta_data(self, client_id, callback):
		def on_finish(lines):
			data = clientquery.getParamValue(lines[0], "client_meta_data")
			if data is None:
				LOG_ERROR("get_client_meta_data failed, value:", data)
				callback("")
			callback(data)

		def on_error(err):
			LOG_ERROR("get_client_meta_data failed:", err)
			callback("")

		self.handler.send_command("clientvariable clid={0} client_meta_data".format(client_id), on_finish, on_error)

	def tick(self):
		pass

	def call_handler(self, name, *args):
		handler = getattr(self, name, None)
		if handler:
			handler(*args)

	def sleep(self, secs):
		end_t = time.time() + secs
		while time.time() < end_t:
			self.raise_on_stop()
			time.sleep(0.1)
		self.raise_on_stop()

	def on_notifytalkstatuschange_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		talking = int(clientquery.getParamValue(line, 'status')) == 1
		if client_id not in self.talk_states:
			self.talk_states[client_id] = False
		if self.talk_states[client_id] != talking:
			self.talk_states[client_id] = talking
			self.call_handler("on_talk_status_changed", client_id, talking)

	def on_notifycliententerview_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		client_nick = clientquery.getParamValue(line, 'client_nickname')
		self.call_handler("on_client_found", client_id, client_nick)

class WOTTS3Connection(TS3Connection):
	
	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		TS3Connection.__init__(self)
		self.clients = {}
		self.my_wot_nickname = None

	def tick(self):
		TS3Connection.tick(self)
		# handle commands from command_queue
		while True:
			try:
				command = self.command_queue.get(block=False)
			except Empty:
				break
			self.call_handler("on_{0}_command".format(command[0]), *command[1])

	def get_wot_nickname(self, client_id, callback):
		def on_finish(data):
			matches = re.search(self.NICK_META_PATTERN, data)
			if matches:
				callback(matches.group(1))
			else:
				callback("")
		self.get_client_meta_data(client_id, on_finish)

	def set_wot_nickname(self, name):
		def on_finish(data):
			new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
			if re.search(self.NICK_META_PATTERN, data):
				data = re.sub(self.NICK_META_PATTERN, new_tag, data)
			else:
				data += new_tag
			self.handler.send_command("clientupdate client_meta_data={0}".format(data), None, None)
		self.get_client_meta_data(self.my_client_id, on_finish)
		self.my_wot_nickname = name

	def on_set_wot_nickname_command(self, name):
		self.set_wot_nickname(name)

	def on_talk_status_changed(self, client_id, talking):
		if client_id in self.clients:
			client = self.clients[client_id]
			has_cached_nickname = (client_id == self.my_client_id) and self.my_wot_nickname is not None

			data = ("talk_status_changed", {
				"ts": client["ts-nickname"],
				"wot": self.my_wot_nickname if has_cached_nickname else client["wot-nickname"]
			}, talking)
			self.event_queue.put(data, block=False)

	def on_client_found(self, client_id, client_nick):
		def on_finish(wot_nickname):
			self.clients[client_id] = {
				"ts-nickname": client_nick,
				"wot-nickname": wot_nickname
			}
		self.get_wot_nickname(client_id, on_finish)
