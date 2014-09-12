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
from debug_utils import LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
import Event

RETRY_TIMEOUT = 10

class NotConnectedToTSError(Exception):
	pass

class TS3Client(object):

	def __init__(self):
		self.connection = WOTTS3Connection()
		self.thread = None
		self.on_talk_status_changed = Event.Event()
		self.on_connected = Event.Event()
		self.on_disconnected = Event.Event()

	def connect(self):
		self.thread = Thread(target=self.connection.execute, name="TeamSpeak Client Thread")
		self.thread.daemon = True
		self.thread.start()

	def disconnect(self):
		if self.connection and self.thread and self.thread.is_alive():
			self.connection.stop = True
			self.thread.join(RETRY_TIMEOUT + 5)

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

	def execute(self):
		self.stop = False
		self.connected = False

		while self.should_execute():
			try:
				self.socket = self.connect_to_ts()

				# once connected, check if we receive "TS3 Client".
				# If not, this is no TS3 clientquery
				data = clientquery.receive(self.socket)
				if not data or not data[0].lower().startswith('ts3 client'):
					LOG_ERROR("Not a TeamSpeak clientquery interface")
					break

				self.connected = True
				self.event_queue.put(("connected",), block=False)

				while self.should_execute():
					try:
						self.my_client_id = clientquery.getParamValue(self.execute_command("whoami")[0], 'clid')

						for method, event in self.get_matching_method_names("on_(.+)_ts3_event"):
							self.execute_command("clientnotifyregister schandlerid=0 event={0}".format(event))
							self.ts3_event_handlers[event] = getattr(self, method)

						self.get_clients()

						while self.should_execute():
							self.tick()
							self.sleep(0.1)
					except clientquery.Error as err:
						if err.code == 1794: # client isn't connected to any TS server
							self.sleep(RETRY_TIMEOUT)

			except (clientquery.Error, socket.error):
				if self.connected:
					LOG_CURRENT_EXCEPTION()
					self.connected = False
					self.event_queue.put(("disconnected",), block=False)
				self.sleep(RETRY_TIMEOUT)

		if self.socket:
			self.socket.close()

	def should_execute(self):
		return not self.stop

	def connect_to_ts(self):
		# create TCP socket and connect to clientquery on localhost:25639
		try:
			s = socket.create_connection((self.HOST, self.PORT))
			s.settimeout(0.5)
			return s
		except socket.error:
			LOG_ERROR("Failed to connect TeamSpeak clientquery interface at {0}:{1}".format(self.HOST, self.PORT))
			raise

	def execute_command(self, command):
		clientquery.send(self.socket, command)
		return clientquery.receive(self.socket)

	def get_matching_method_names(self, pattern):
		for attr in dir(self):
			matches = re.match(pattern, attr)
			if matches:
				yield attr, matches.group(1)

	def get_client_meta_data(self, client_id):
		data = self.execute_command("clientvariable clid={0} client_meta_data".format(client_id))
		data = clientquery.getParamValue(data[0], "client_meta_data")
		if not isinstance(data, basestring):
			LOG_ERROR("Failed to read ts3 meta data, value:", data)
			return ""
		return data

	def get_clients(self):
		data = self.execute_command("clientlist")
		for client_data in data[0].split('|'):
			client_id = int(clientquery.getParamValue(client_data, 'clid'))
			client_nick = clientquery.getParamValue(client_data, 'client_nickname')
			self.call_handler("on_client_found", client_id, client_nick)

	def tick(self):
		data = clientquery.receive(self.socket)
		if not data:
			return
		for line in data:
			parts = line.split(None, 1)
			if parts[0] in self.ts3_event_handlers:
				self.ts3_event_handlers[parts[0]](parts[1])

	def call_handler(self, name, *args):
		handler = getattr(self, name, None)
		if handler:
			handler(*args)

	def sleep(self, secs):
		end_t = time.time() + secs
		while self.should_execute() and time.time() < end_t:
			time.sleep(0.1)

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

	def tick(self):
		TS3Connection.tick(self)
		# handle commands from command_queue
		while True:
			try:
				command = self.command_queue.get(block=False)
			except Empty:
				break
			self.call_handler("on_{0}_command".format(command[0]), *command[1])

	def get_wot_nickname(self, client_id):
		matches = re.search(self.NICK_META_PATTERN, self.get_client_meta_data(client_id))
		if matches:
			return matches.group(1)
		return ""

	def set_wot_nickname(self, name):
		new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
		data = self.get_client_meta_data(self.my_client_id)
		if re.search(self.NICK_META_PATTERN, data):
			data = re.sub(self.NICK_META_PATTERN, new_tag, data)
		else:
			data += new_tag
		self.execute_command("clientupdate client_meta_data={0}".format(data))[0]

	def on_set_wot_nickname_command(self, name):
		self.set_wot_nickname(name)

	def on_talk_status_changed(self, client_id, talking):
		if client_id in self.clients:
			client = self.clients[client_id]
			data = ("talk_status_changed", {
				"ts": client["ts-nickname"],
				"wot": client["wot-nickname"]
			}, talking)
			self.event_queue.put(data, block=False)

	def on_client_found(self, client_id, client_nick):
		self.clients[client_id] = {
			"ts-nickname": client_nick,
			"wot-nickname": self.get_wot_nickname(client_id)
		}
