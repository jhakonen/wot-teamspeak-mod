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

'''This module contains implementation for communicating with TeamSpeak's
client query interface.

For more information of client query, see:
   http://forum.teamspeak.com/showthread.php/66509-Official-ClientQuery-Plugin

The main entry point is TS3Client class. After instancing call connect() to
connect to the TeamSpeak client. The TS3Client will continue to connect until
connection to the client is succesfully made.
The TS3Client has check_events() method which implements event handling
mechanism and it needs to be called periodically, e.g. with
BigWorld.callback().

The class provides several functions for querying information from TS client in
a non-blocking asyncronous manner.
'''

import socket
import errno
import clientquery
import time
import re
import asyncore
import asynchat
import functools
import Event
import BigWorld
from utils import (
	with_args,
	LOG_CALL,
	LOG_DEBUG,
	LOG_NOTE,
	LOG_WARNING,
	LOG_ERROR,
	LOG_CURRENT_EXCEPTION
)

_RETRY_TIMEOUT = 10
_API_NOT_CONNECTED_TO_SERVER = 1794

def _LOG_API_ERROR(message, err):
	if err:
		if err[0] == _API_NOT_CONNECTED_TO_SERVER:
			LOG_DEBUG(message, err)
		else:
			LOG_ERROR(message, err)

def _noop(*args, **kwargs):
	'''Function that does nothing. A safe default value for callback
	parameters.
	'''
	pass

def _would_block_windows_workaround(func, fix_func):
	'''Function decorator which caughts socket errors of type WSAEWOULDBLOCK
	while other exceptions will propagate through.
	'''
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except socket.error as err:
			if err.args[0] == errno.WSAEWOULDBLOCK:
				return fix_func(*args, **kwargs)
			raise
	functools.update_wrapper(wrapper, func)
	return wrapper

class _ClientQueryProtocol(asynchat.async_chat):
	'''This class handles low level communication with the client query interface.'''

	def __init__(self, event_receiver, map):
		asynchat.async_chat.__init__(self, map=map)

		# public events
		self.on_connected = Event.Event()
		self.on_closed = Event.Event()
		self.on_ready = Event.Event()

		self._event_handlers = {}
		for attr in dir(event_receiver):
			matches = re.match("on_(.+)_ts3_event", attr)
			if matches:
				name = matches.group(1)
				self._event_handlers[name] = getattr(event_receiver, attr)
		self.set_terminator("\n\r")

		def connect_fix(address):
			self.addr = address
		self.connect = _would_block_windows_workaround(self.connect, connect_fix)
		self.send = _would_block_windows_workaround(self.send, lambda self, data: 0)

	def close(self):
		'''Closes connection.'''
		asynchat.async_chat.close(self)
		self._data_in_handler = _noop
		self.on_closed()

	def handle_connect(self):
		'''Hook method which is called by async_chat when connection is
		established. Initializes variables and prepares for protocol testing.
		'''
		self._commands = []
		self._in_line = ""
		self._data_in_handler = self._handle_in_data_proto_test
		self.on_connected()

	def handle_close(self):
		'''Hook method which is called by async_chat when connection is closed
		or lost.
		'''
		self.close()

	@LOG_CALL(msg="<< {data}")
	def collect_incoming_data(self, data):
		'''Hook method which is called by async_chat to provide incoming data.
		Data is provided just enough until terminator is found.
		'''
		self._in_line += data

	def found_terminator(self):
		'''Hook method which is called by async_chat to indicate end-of-line.
		Feeds collected line to data handling.
		'''
		self._data_in_handler(self._in_line)
		self._in_line = ""

	@LOG_CALL(msg=">> {data}")
	def push(self, data):
		asynchat.async_chat.push(self, data)

	def _handle_in_data_proto_test(self, line):
		'''Checks that we really contacted TeamSpeak client query interface and
		nothing something totally else.
		'''
		if "ts3 client" in line.lower():
			LOG_NOTE("TS client query protocol detected")
			self._data_in_handler = self._handle_in_data_welcome_message
		else:
			LOG_ERROR("Not TS client query protocol")
			self.close()

	def _handle_in_data_welcome_message(self, line):
		'''Consumes welcome message.'''
		if "selected schandlerid" in line:
			self._data_in_handler = self._handle_in_data_actions
			self.on_ready()

	def _handle_in_data_actions(self, line):
		'''Handles received events and responses to commands.'''
		first_word = line.split(None, 1)[0]
		# maybe an event?
		if first_word in self._event_handlers:
			self._event_handlers[first_word](line)
		# if not, then maybe a response to command?
		else: 
			try:
				self._commands[0].handle_line(line)
			except IndexError:
				pass

	def handle_out_commands(self):
		'''Sends commands to client query (if any) in a serialized manner, not
		sending more than one command at once. This so that we know which
		response is meant for which command.
		'''
		if self._data_in_handler == self._handle_in_data_actions:
			try:
				cmd = self._commands[0]
				if not cmd.is_sent:
					self.push(cmd.command + "\n\r")
					cmd.is_sent = True
				if cmd.is_done:
					self._commands.remove(cmd)
			except IndexError:
				pass

	def send_command(self, command, callback=_noop):
		'''Queues command for sending to client query.'''
		self._commands.append(_ClientQueryCommand(command, callback))

class _ClientQueryCommand(object):
	'''Container for a single command, handles receiving response lines and
	calling a callback provided by the caller with the response, or error.
	'''

	def __init__(self, command, callback):
		self.command = command
		self.is_done = False
		self.is_sent = False
		self._callback = callback
		self._response_lines = []

	def handle_line(self, line):
		'''Handles a single line received from client query.'''
		# last response line, if contains error status
		if line.startswith("error "):
			err = clientquery.checkError([line])
			try:
				if err:
					self._callback(err, None)
				else:
					self._callback(None, self._response_lines)
			finally:
				# mark as done so that this command is removed from
				# command queue
				self.is_done = True
		# collect lines before error status line
		else:
			self._response_lines.append(line)

class TS3Client(object):
	'''Main entry point for access to TeamSpeak's client query interface.'''
	
	HOST = "localhost"
	PORT = 25639
	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		# public events
		self.on_connected = Event.Event()
		self.on_disconnected = Event.Event()
		self.on_talk_status_changed = Event.Event()
		self.on_connected_to_server = Event.Event()
		self.on_disconnected_from_server = Event.Event()

		self._clients = {}
		self._speak_states = {}
		self._callback_handles = []
		self._connected = False
		self._connected_to_server = False
		self._clientuidfromclid_cache = {}
		self._socket_map = {}

		self._protocol = _ClientQueryProtocol(self, self._socket_map)
		self._protocol.on_ready += self._set_connected
		self._protocol.on_ready += self._register_notifications
		self._protocol.on_ready += self._ping
		self._protocol.on_connected += self._on_protocol_connected
		self._protocol.on_closed += self._on_protocol_closed

	def connect(self):
		'''Starts connect attempt and continues to try until succesfully
		connected.
		'''
		self._connected = False
		self._cancel_all__call_laters()
		self._protocol.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self._protocol.connect((self.HOST, self.PORT))

	def check_events(self):
		'''Event handler method. Call this periodically.'''
		asyncore.loop(timeout=0, count=1, map=self._socket_map)
		self._protocol.handle_out_commands()

	def _set_connected(self):
		self._connected = True
		self.on_connected()

	def _register_notifications(self):
		def on_command_finish(err, data):
			self._handle_api_error(err, "Event registering failed")

		self._protocol.send_command("clientnotifyregister schandlerid=0 event=notifytalkstatuschange", on_command_finish)
		self._protocol.send_command("clientnotifyregister schandlerid=0 event=notifycliententerview", on_command_finish)
		self._protocol.send_command("clientnotifyregister schandlerid=0 event=notifyclientupdated", on_command_finish)
		self._protocol.send_command("clientnotifyregister schandlerid=0 event=notifyclientuidfromclid", on_command_finish)

	def _handle_api_error(self, err, msg):
		if err:
			if err[0] == _API_NOT_CONNECTED_TO_SERVER:
				if self._connected_to_server:
					self._connected_to_server = False
					self.on_disconnected_from_server()
			else:
				_LOG_API_ERROR(msg + ":", err)
				LOG_NOTE("Closing connection")
				self._protocol.close()

	def _ping(self):
		'''Ping TS client with some command to keep connection alive.'''
		def on_finish(err, result):
			if not err and not self._connected_to_server:
				self._connected_to_server = True
				self.on_connected_to_server()
			self._call_later(_RETRY_TIMEOUT, self._ping)

		self.get_my_client_id(on_finish)

	def _on_protocol_connected(self):
		LOG_NOTE("Connected to TeamSpeak clientquery interface")

	def _on_protocol_closed(self):
		LOG_ERROR("Failed to connect TeamSpeak clientquery interface at {0}:{1}".format(self.HOST, self.PORT))
		self._connected = False
		self.on_disconnected()
		self._call_later(_RETRY_TIMEOUT, self.connect)

	def _call_later(self, secs, func):
		'''Enhanced version of BigWorld.callback() which keeps track of
		waiting callbacks.
		'''
		def wrapper():
			try:
				func()
			finally:
				try:
					self._callback_handles.remove(handle)
				except ValueError:
					# protect against 'handle' not being in the list anymore
					# due of _cancel_all__call_laters()
					pass
		handle = BigWorld.callback(secs, wrapper)
		self._callback_handles.append(handle)

	def _cancel_all__call_laters(self):
		for handle in self._callback_handles:
			BigWorld.cancelCallback(handle)
		self._callback_handles = []

	def get_my_client_id(self, callback=_noop):
		def on_whoami(err, lines):
			if err:
				self._handle_api_error(err, "get_my_client_id() failed")
				callback(err, None)
			else:
				client_id = int(clientquery.getParamValue(lines[0], 'clid'))
				callback(None, client_id)
		self._protocol.send_command("whoami", on_whoami)

	def get_client_meta_data(self, client_id, callback=_noop):
		def on_finish(err, lines):
			if err:
				self._handle_api_error(err, "get_client_meta_data() failed")
				callback(err, "")
			else:
				data = clientquery.getParamValue(lines[0], "client_meta_data")
				if data is None:
					LOG_WARNING("get_client_meta_data failed, value:", data)
					callback(None, "")
				else:
					callback(None, data)
		self._protocol.send_command("clientvariable clid={0} client_meta_data".format(client_id), on_finish)

	def get_wot_nickname(self, client_id, callback=_noop):
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
		if name is None:
			return

		def on_get_my_client_id(err, client_id):
			def on_get_client_meta_data(err, data):
				if data is not None:
					new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
					if re.search(self.NICK_META_PATTERN, data):
						data = re.sub(self.NICK_META_PATTERN, new_tag, data)
					else:
						data += new_tag
					self._protocol.send_command("clientupdate client_meta_data={0}".format(data))
					self._invalidate_client_id(client_id)

			if client_id is not None:
				self.get_client_meta_data(client_id, on_get_client_meta_data)

		self.get_my_client_id(on_get_my_client_id)

	def _invalidate_client_id(self, client_id):
		try:
			del self._clients[client_id]
		except:
			pass

	def get_client(self, client_id, callback=_noop):
		def on_get_client_info(err, client_info):
			if err:
				callback(err, None)
			else:
				self._save_client_data(
					client_id=client_info[0],
					client_nick=client_info[1],
					wot_nick=client_info[2]
				)
				callback(None, self._clients[client_id])

		if client_id in self._clients:
			callback(None, self._clients[client_id])
		else:
			self.get_client_info(client_id, on_get_client_info)

	def get_clientlist(self, callback=_noop):
		def on_clientlist(err, lines):
			if err:
				self._handle_api_error(err, "get_clientlist() failed")
				callback(err, None)
			else:
				clientlist = []
				for client_data in lines[0].split('|'):
					clientlist.append((
						int(clientquery.getParamValue(client_data, 'clid')),
						clientquery.getParamValue(client_data, 'client_nickname')
					))
				callback(None, clientlist)
		self._protocol.send_command("clientlist", on_clientlist)

	def get_client_info(self, client_id, callback=_noop):
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

	def query_clientgetuidfromclid(self, client_id, callback=_noop):
		try:
			del self._clientuidfromclid_cache[client_id]
		except KeyError:
			pass

		wait_end_t = time.time() + 10

		def wait_notify():
			if client_id in self._clientuidfromclid_cache:
				callback(None, self._clientuidfromclid_cache[client_id])
			elif time.time() < wait_end_t:
				self._call_later(0.1, wait_notify)
			else:
				LOG_ERROR("Event notifyclientuidfromclid not received")
				callback("Event notifyclientuidfromclid not received", None)

		def on_clientgetuidfromclid(err, lines):
			if err:
				self._handle_api_error(err, "clientgetuidfromclid() failed")
				callback(err, None)
			else:
				wait_notify()
		self._protocol.send_command("clientgetuidfromclid clid={0}".format(client_id), on_clientgetuidfromclid)

	def on_notifytalkstatuschange_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		talking = int(clientquery.getParamValue(line, 'status')) == 1
		if client_id not in self._speak_states:
			self._speak_states[client_id] = False
		if self._speak_states[client_id] != talking:
			self._speak_states[client_id] = talking

			def on_get_client(err, client):
				if not err:
					self.on_talk_status_changed({
						"ts": client["ts-nickname"],
						"wot": client["wot-nickname"]
					}, talking)
			self.get_client(client_id, on_get_client)

	def on_notifycliententerview_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		self._invalidate_client_id(client_id)

	def on_notifyclientupdated_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		self._invalidate_client_id(client_id)

	def on_notifyclientuidfromclid_ts3_event(self, line):
		client_id = int(clientquery.getParamValue(line, 'clid'))
		nickname = clientquery.getParamValue(line, "nickname")
		self._clientuidfromclid_cache[client_id] = nickname

	def _save_client_data(self, client_id, client_nick, wot_nick):
		self._clients[client_id] = {
			"ts-nickname": client_nick,
			"wot-nickname": wot_nick
		}
