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

import sys
import socket
import errno
import clientquery
import time
import re
import asyncore
import asynchat
import functools
import weakref
import Event
import BigWorld
from utils import (
	noop,
	with_args,
	LOG_CALL,
	LOG_DEBUG,
	LOG_NOTE,
	LOG_WARNING,
	LOG_ERROR,
	LOG_CURRENT_EXCEPTION,
	RepeatTimer
)
from statemachine import StateMachine
import async

_RETRY_TIMEOUT = 10
_COMMAND_WAIT_TIMEOUT = 30
_UNREGISTER_WAIT_TIMEOUT = 5
_API_NOT_CONNECTED_TO_SERVER = 1794
_API_INVALID_SCHANDLER_ID = 1799

class TS3Client(object):
	'''Main entry point for access to TeamSpeak's client query interface.'''

	HOST = "localhost"
	PORT = 25639
	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		# public events
		self.on_connected = Event.Event()
		self.on_disconnected = Event.Event()
		self.on_connected_to_server = Event.Event()
		self.on_disconnected_from_server = Event.Event()
		self.on_authenticate_error = Event.Event()

		# public models
		self.users = UserModel()
		self.users_in_my_channel = UserFilterProxy(
			source      = self.users,
			filter_func = lambda user: user.channel_id == self._my_channel_id
		)
		self.users_in_my_channel.on_added += self.on_user_entered_my_channel

		self._ping_timer = RepeatTimer(_RETRY_TIMEOUT)
		self._ping_timer.on_timeout += self._ping

		self._socket_map = {}
		self._wot_nickname = None
		self._my_client_id = None
		self._my_channel_id = None
		self._schandler_id = None
		self.__apikey = None

		self._protocol = _ClientQueryProtocol(self, self._socket_map)
		self._protocol.on_ready += functools.partial(self._send_sm_event, "protocol_ready")
		self._protocol.on_closed += functools.partial(self._send_sm_event, "protocol_closed")

		self._sm = StateMachine()

		not_connected_state          = self._sm.add_state("Not Connected")
		connecting_to_ts_state       = self._sm.add_state("Connecting to TS", on_enter=self._on_connecting_to_ts_state)
		authenticate_state           = self._sm.add_state("Authenticate", on_enter=self._on_authenticate_state)
		connecting_failed_state      = self._sm.add_state("Connecting Failed", on_enter=self._on_connect_failed_state)
		connected_to_ts_state        = self._sm.add_state("Connected to TS", on_enter=self._on_connected_to_ts_state)
		connected_to_ts_server_state = self._sm.add_state("Connected to TS Server", on_enter=self._on_connected_to_ts_server_state)

		self._sm.add_transition(not_connected_state,          connecting_to_ts_state,       "connect")
		self._sm.add_transition(connecting_to_ts_state,       authenticate_state,           "protocol_ready")
		self._sm.add_transition(authenticate_state,           connected_to_ts_state,        "authenticated", on_transit=self.on_connected)
		self._sm.add_transition(authenticate_state,           connecting_failed_state,      "protocol_closed")
		self._sm.add_transition(connecting_to_ts_state,       connecting_failed_state,      "protocol_closed")
		self._sm.add_transition(connected_to_ts_state,        connected_to_ts_server_state, "ping_ok")
		self._sm.add_transition(connected_to_ts_state,        connecting_to_ts_state,       "protocol_closed", on_transit=self.on_disconnected)
		self._sm.add_transition(connected_to_ts_state,        connected_to_ts_state,        "tab_changed")
		self._sm.add_transition(connected_to_ts_state,        connected_to_ts_state,        "server_disconnected")
		self._sm.add_transition(connected_to_ts_server_state, connected_to_ts_state,        "tab_changed", on_transit=self.on_disconnected_from_server)
		self._sm.add_transition(connected_to_ts_server_state, connected_to_ts_state,        "server_disconnected", on_transit=self.on_disconnected_from_server)
		self._sm.add_transition(connected_to_ts_server_state, connected_to_ts_state,        "not_connected_error", on_transit=self.on_disconnected_from_server)
		self._sm.add_transition(connected_to_ts_server_state, connecting_to_ts_state,       "protocol_closed", on_transit=self.on_disconnected)
		self._sm.add_transition(connecting_failed_state,      connecting_to_ts_state,       "connect_retry")

		self._sm.tick()

	def fini(self):
		self._protocol.close()
		self._protocol = None
		self._sm = None
		self.users.fini()
		self.users = None
		self.users_in_my_channel.fini()
		self.users_in_my_channel = None
		self._ping_timer.fini()
		self._ping_timer = None

	def set_apikey(self, apikey):
		'''Sets API key for ClientQuery.'''
		self.__apikey = apikey

	def connect(self):
		'''Starts connect attempt and continues to try until succesfully
		connected.
		'''
		self._send_sm_event("connect")

	def check_events(self):
		'''Event handler method. Call this periodically.'''
		asyncore.loop(timeout=0, count=1, map=self._socket_map)
		self._protocol.handle_out_commands()
		self._sm.tick()

	def _on_connecting_to_ts_state(self):
		self._stop_pinging()
		self._protocol.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self._protocol.connect((self.HOST, self.PORT))

	def _on_connect_failed_state(self):
		BigWorld.callback(_RETRY_TIMEOUT, functools.partial(self._send_sm_event, "connect_retry"))

	def _send_command(self, command, args=[], kwargs={}, callback=noop, timeout=_COMMAND_WAIT_TIMEOUT):
		def on_command_finish(err, lines):
			if err:
				LOG_DEBUG(type(err).__name__ + ": " + str(err))
				if isinstance(err, clientquery.APINotConnectedError) or isinstance(err, clientquery.APIInvalidSchandlerIDError):
					self._send_sm_event("not_connected_error")
				else:
					self._protocol.close()
			callback(err, lines)

		assert " " not in command, "Spaces are not allowed in the command, use args or kwargs instead"
		self._protocol.send_command(build_command_string(command, args, kwargs), on_command_finish, timeout)

	def _on_authenticate_state(self):
		'''Authenticates to client query, required with TeamSpeak 3.1.3 or newer.'''
		def on_finish(err, lines):
			if not err:
				self._send_sm_event("authenticated")
			elif err[0] == 256:
				# Command not found, TeamSpeak is version 3.1.2 or older
				self._send_sm_event("authenticated")
			else:
				# In other error cases the API key is likely not set or is wrong
				self.on_authenticate_error()
				self._protocol.close()
		self._send_command("auth", kwargs={"apikey": self.__apikey}, callback=on_finish)

	def _on_connected_to_ts_state(self):
		self._my_client_id = None
		self._my_channel_id = None
		self._schandler_id = None
		self.users.clear()
		self.users_in_my_channel.invalidate()

		def unregister(callback):
			self._send_command("clientnotifyunregister", callback=callback, timeout=_UNREGISTER_WAIT_TIMEOUT)
		def register_connection_change(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": 0, "event": "notifycurrentserverconnectionchanged"}, callback=callback)
		def get_currentschandlerid(callback):
			def on_finish(err, lines):
				if not err:
					self._schandler_id = int(parse_client_query_parameter(lines[0], "schandlerid"))
				callback(err, lines)
			self._send_command("currentschandlerid", callback=on_finish)
		def register_talk_status_change(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifytalkstatuschange"}, callback=callback)
		def register_client_update(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifyclientupdated"}, callback=callback)
		def register_client_enter_view(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifycliententerview"}, callback=callback)
		def register_client_left_view(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifyclientleftview"}, callback=callback)
		def register_client_moved(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifyclientmoved"}, callback=callback)
		def register_connect_status_change(callback):
			self._send_command("clientnotifyregister", kwargs={"schandlerid": self._schandler_id, "event": "notifyconnectstatuschange"}, callback=callback)
		def use_schandler_id(callback):
			self._send_command("use", kwargs={"schandlerid": self._schandler_id}, callback=callback)
		def start_pinging(callback):
			self._start_pinging()
			callback(None, None)
		def on_finish(err, results):
			self._sm.set_state_done()

		async.series([
			unregister,
			register_connection_change,
			get_currentschandlerid,
			register_talk_status_change,
			register_client_update,
			register_client_enter_view,
			register_client_left_view,
			register_client_moved,
			register_connect_status_change,
			use_schandler_id,
			start_pinging
		], on_finish)

		return False

	def _on_connected_to_ts_server_state(self):
		def retrieve_clientlist(callback):
			def on_clientlist(err, entries):
				if not err:
					for entry in entries:
						client_id = int(entry.get("clid"))
						self.users.add(
							client_id  = client_id,
							nick       = entry.get("client_nickname"),
							unique_id  = entry.get("client_unique_identifier"),
							channel_id = int(entry.get("cid"))
						)
						self.users[client_id].speaking = bool(int(entry.get("client_flag_talking")))
				callback(err, entries)
			self.get_clientlist(on_clientlist)
		def update_wot_nickname(callback):
			self.set_wot_nickname(self._wot_nickname, callback)
		def notify_connected_to_server(callback):
			def on_name_received(err, name):
				self.on_connected_to_server("unknown" if err else name)
				callback(err, name)
			self._get_server_name(on_name_received)

		def on_finish(err, results):
			self._sm.set_state_done()

		async.series([
			retrieve_clientlist,
			update_wot_nickname,
			notify_connected_to_server
		], on_finish)

		return False

	def _send_sm_event(self, event_name):
		self._sm.send_event(event_name)

	def _start_pinging(self):
		self._ping_timer.start()
		self._ping()

	def _ping(self):
		def on_finish(err, ignored):
			if not err:
				self._send_sm_event("ping_ok")
		self._update_my_client_id(on_finish)

	def _stop_pinging(self):
		self._ping_timer.stop()

	def _update_my_client_id(self, callback=noop):
		def on_whoami(err, lines):
			if not err and lines:
				[entry] = parse_client_query_parameters(lines[0])
				self._my_client_id = int(entry.get("clid"))
				new_channel_id = int(entry.get("cid"))
				if new_channel_id != self._my_channel_id:
					self._my_channel_id = new_channel_id
					self.users_in_my_channel.invalidate()
			callback(err, None)
		self._send_command("whoami", callback=on_whoami)

	def get_client_meta_data(self, client_id, callback=noop):
		def on_finish(err, lines):
			if err:
				callback(err, None)
			else:
				data = parse_client_query_parameter(lines[0], "client_meta_data")
				if data is None:
					LOG_WARNING("get_client_meta_data failed, value:", data)
					callback(None, "")
				else:
					callback(None, data)
		self._send_command("clientvariable", args=["client_meta_data"], kwargs={"clid": client_id}, callback=on_finish)

	def get_wot_nickname(self, client_id, callback=noop):
		def on_finish(err, data):
			if err:
				callback(err, None)
			else:
				callback(None, self._get_wot_nick_from_metadata(data))
		self.get_client_meta_data(client_id, on_finish)

	def _get_wot_nick_from_metadata(self, data):
		matches = re.search(self.NICK_META_PATTERN, data)
		if matches:
			return matches.group(1)
		return ""

	def set_wot_nickname(self, name, callback=noop):
		self._wot_nickname = name

		if name is None or self._my_client_id is None:
			callback(None, None)
			return

		def on_get_client_meta_data(err, data):
			if err:
				callback(err, data)
			else:
				data = data if data else ""
				new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(name)
				if re.search(self.NICK_META_PATTERN, data):
					data = re.sub(self.NICK_META_PATTERN, new_tag, data)
				else:
					data += new_tag
				self._send_command("clientupdate", kwargs={"client_meta_data": data}, callback=callback)
		self.get_client_meta_data(self._my_client_id, on_get_client_meta_data)

	def get_clientlist(self, callback=noop):
		def on_clientlist(err, lines):
			if err:
				callback(err, None)
			else:
				callback(None, parse_client_query_parameters(lines[0]))
		self._send_command("clientlist", args=["-uid", "-voice"], callback=on_clientlist)

	def _get_server_name(self, callback=noop):
		def on_finish(err, lines):
			if err:
				callback(err, None)
			else:
				callback(None, parse_client_query_parameter(lines[0], "virtualserver_name"))
		self._send_command("servervariable", args=["virtualserver_name"], callback=on_finish)

	def on_user_entered_my_channel(self, client_id):
		user = self.users[client_id]
		def on_get_wot_nickname(err, wot_nickname):
			if not err:
				user.wot_nick = wot_nickname
		self.get_wot_nickname(client_id, on_get_wot_nickname)

	def on_notifycurrentserverconnectionchanged_ts3_event(self, line):
		self._send_sm_event("tab_changed")

	def on_notifytalkstatuschange_ts3_event(self, line):
		[entry] = parse_client_query_parameters(line)
		client_id = int(entry.get("clid"))
		speaking = int(entry.get("status")) == 1
		if client_id not in self.users:
			return
		user = self.users[client_id]
		if user.speaking != speaking:
			user.speaking = speaking

	def on_notifyclientupdated_ts3_event(self, line):
		[entry] = parse_client_query_parameters(line)
		client_id = int(entry.get("clid"))
		if client_id in self.users:
			user = self.users[client_id]
			nick = entry.get("client_nickname")
			if nick:
				user.nick = nick
			metadata = entry.get("client_meta_data")
			if metadata:
				new_wot_nick = self._get_wot_nick_from_metadata(metadata)
				# Check if our wot nickname has changed without our consent
				# (e.g. some other TS plugin has overwritten our metadata)
				# --> if so, set the metadata again
				if client_id == self._my_client_id and self._wot_nickname != new_wot_nick:
					self.set_wot_nickname(self._wot_nickname) 
				else:
					user.wot_nick = new_wot_nick

	def on_notifycliententerview_ts3_event(self, line):
		'''This event handler is called when a TS user enters to the TS server.'''
		for entry in parse_client_query_parameters(line):
			# only first entry has channel id
			if "ctid" in entry:
				channel_id = int(entry.get("ctid"))
			self.users.add(
				nick       = entry.get("client_nickname"),
				wot_nick   = self._get_wot_nick_from_metadata(entry.get("client_meta_data")),
				client_id  = int(entry.get("clid")),
				unique_id  = entry.get("client_unique_identifier"),
				channel_id = channel_id
			)

	def on_notifyclientleftview_ts3_event(self, line):
		'''This event handler is called when a TS user leaves from the TS server.'''
		for entry in parse_client_query_parameters(line):
			client_id = int(entry.get("clid"))
			if client_id in self.users:
				self.users.remove(client_id)

	def on_notifyclientmoved_ts3_event(self, line):
		'''This event handler is called when a TS user moves from one channel to another.'''
		[entry] = parse_client_query_parameters(line)
		client_id = int(entry.get("clid"))
		channel_id = int(entry.get("ctid"))
		if client_id not in self.users:
			return
		self.users.add(
			client_id  = client_id,
			channel_id = channel_id
		)

	def on_notifyconnectstatuschange_ts3_event(self, line):
		status = parse_client_query_parameter(line, "status")
		if status == "disconnected":
			self._send_sm_event("server_disconnected")


class _ClientQueryProtocol(asynchat.async_chat):
	'''This class handles low level communication with the client query interface.'''

	def __init__(self, event_receiver, map):
		asynchat.async_chat.__init__(self, map=map)

		# public events
		self.on_connected = Event.Event()
		self.on_closed = Event.Event()
		self.on_ready = Event.Event()

		self._data_in_handler = noop
		self._event_handlers = {}
		for attr in dir(event_receiver):
			matches = re.match("on_(.+)_ts3_event", attr)
			if matches:
				name = matches.group(1)
				self._event_handlers[name] = getattr(event_receiver, attr)
		self.set_terminator("\n\r")
		self._commands = []
		self._opened = False

	def send(self, data):
		try:
			return asynchat.async_chat.send(self, data)
		except socket.error as err:
			if err.args[0] == errno.WSAEWOULDBLOCK:
				return 0
			raise

	def connect(self, address):
		try:
			self._opened = True
			return asynchat.async_chat.connect(self, address)
		except socket.error as err:
			if err.args[0] == errno.WSAEWOULDBLOCK:
				self.addr = address
				return
			raise

	def close(self):
		'''Closes connection.'''
		asynchat.async_chat.close(self)
		if self._opened:
			self._opened = False
			self._data_in_handler = noop
			self.on_closed()
			for command in self._commands:
				command.closed()
			del self._commands[:]

	def handle_connect(self):
		'''Hook method which is called by async_chat when connection is
		established. Initializes variables and prepares for protocol testing.
		'''
		del self._commands[:]
		self._in_line = ""
		self._data_in_handler = self._handle_in_data_proto_test
		self.on_connected()

	def handle_close(self):
		'''Hook method which is called by async_chat when connection is closed
		or lost.
		'''
		self.close()

	def handle_error(self):
		'''Hook method which is called by aync_chat when an error happens which
		is not otherwise handled.
		'''
		LOG_WARNING(sys.exc_info()[1])

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
		try:
			self._data_in_handler(self._in_line)
		except:
			LOG_CURRENT_EXCEPTION()
			self.close()
		self._in_line = ""

	@LOG_CALL(msg=">> {data}")
	def push(self, data):
		asynchat.async_chat.push(self, data)

	def _handle_in_data_proto_test(self, line):
		'''Checks that we really contacted TeamSpeak client query interface and
		nothing something totally else.
		'''
		if "ts3 client" in line.lower():
			self._data_in_handler = self._handle_in_data_welcome_message
		else:
			LOG_ERROR("Not TS client query protocol")
			self.close()

	def log_info(self, message, type="info"):
		'''Undocumented feature of asyncore. Called by asyncore to print log
		messages. Converts the log message to WOT logging.
		'''
		if type == "info":
			LOG_NOTE(message)
		elif type == "error":
			LOG_ERROR(message)
		elif type == "warning":
			LOG_WARNING(message)

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
					cmd.finish()
			except IndexError:
				pass

	def send_command(self, command, callback, timeout):
		'''Queues command for sending to client query.'''
		if self._data_in_handler == self._handle_in_data_actions:
			self._commands.append(_ClientQueryCommand(command, callback, timeout))
		else:
			callback(CommandIgnoredError("Cannot send command '{0}', wrong state".format(command)), None)

class _ClientQueryCommand(object):
	'''Container for a single command, handles receiving response lines and
	calling a callback provided by the caller with the response, or error.
	'''

	def __init__(self, command, callback, timeout):
		self.command = command
		self.is_sent = False
		self._is_done = False
		self._callback = callback
		self._response_lines = []
		self._start_time = time.time()
		self._err = None
		self._timeout = timeout

	@property
	def is_done(self):
		return self._is_done or (time.time() - self._start_time) >= self._timeout

	def handle_line(self, line):
		'''Handles a single line received from client query.'''
		# last response line, if contains error status
		if line.startswith("error "):
			self._err = clientquery.checkError([line])
			self._is_done = True
		# collect lines before error status line
		else:
			self._response_lines.append(line)

	def finish(self):
		self._callback(self._err, self._response_lines)

	def closed(self):
		self._callback(ProtocolClosed("Command discarded: {0}".format(self.command)), None)

class ProtocolClosed(Exception):
	pass

class CommandIgnoredError(Exception):
	pass

class User(object):

	def __init__(self, model):
		self.__model = weakref.proxy(model)
		self.__nick = None
		self.__wot_nick = None
		self.__client_id = None
		self.__unique_id = None
		self.__channel_id = None
		self.__speaking = False

	@property
	def nick(self):
		return self.__nick
	@nick.setter
	def nick(self, nick):
		if nick is not None and self.__nick != nick:
			self.__nick = nick
			self.__notify_modified()

	@property
	def wot_nick(self):
		return self.__wot_nick
	@wot_nick.setter
	def wot_nick(self, wot_nick):
		if wot_nick is not None and self.__wot_nick != wot_nick:
			self.__wot_nick = wot_nick
			self.__notify_modified()

	@property
	def client_id(self):
		return self.__client_id
	@client_id.setter
	def client_id(self, client_id):
		if client_id is not None and self.__client_id != client_id:
			self.__client_id = client_id
			self.__notify_modified()

	@property
	def unique_id(self):
		return self.__unique_id
	@unique_id.setter
	def unique_id(self, unique_id):
		if unique_id is not None and self.__unique_id != unique_id:
			self.__unique_id = unique_id
			self.__notify_modified()

	@property
	def channel_id(self):
		return self.__channel_id
	@channel_id.setter
	def channel_id(self, channel_id):
		if channel_id is not None and self.__channel_id != channel_id:
			self.__channel_id = channel_id
			self.__notify_modified()

	@property
	def speaking(self):
		return self.__speaking
	@speaking.setter
	def speaking(self, speaking):
		if speaking is not None and self.__speaking != speaking:
			self.__speaking = speaking
			self.__notify_modified()

	def __notify_modified(self):
		if self.__client_id is not None and self.__client_id in self.__model:
			self.__model.on_modified(self.__client_id)

	def __hash__(self):
		return (
			hash(self.__client_id) ^
			hash(self.__nick) ^
			hash(self.__wot_nick) ^
			hash(self.__unique_id) ^
			hash(self.__channel_id)
		)

	def __eq__(self, other):
		return hash(self) == hash(other)

	def __repr__(self):
		return "User (client_id={0}, nick={1}, wot_nick={2}, unique_id={3}, channel_id={4}, speaking={5})".format(
			repr(self.__client_id),
			repr(self.__nick),
			repr(self.__wot_nick),
			repr(self.__unique_id),
			repr(self.__channel_id),
			repr(self.__speaking)
		)

class UserModel(object):

	def __init__(self):
		self._users = {}
		self.on_added = Event.Event()
		self.on_removed = Event.Event()
		self.on_modified = Event.Event()

	def fini(self):
		self.on_added.clear()
		self.on_removed.clear()
		self.on_modified.clear()

	def add(self, client_id, nick=None, wot_nick=None, unique_id=None, channel_id=None):
		if client_id is None:
			return

		user = self._users.get(client_id, User(self))
		user.client_id = client_id
		user.nick = nick
		user.wot_nick = wot_nick
		user.unique_id = unique_id
		user.channel_id = channel_id

		if client_id not in self._users:
			self._users[client_id] = user
			self.on_added(client_id)

	def remove(self, client_id):
		self._users[client_id].speaking = False
		del self._users[client_id]
		self.on_removed(client_id)

	def clear(self):
		client_ids = self._users.keys()
		self._users.clear()
		for client_id in client_ids:
			self.on_removed(client_id)

	def __contains__(self, client_id):
		return client_id in self._users

	def __getitem__(self, client_id):
		return self._users[client_id]

	def __iter__(self):
		for client_id in self._users:
			yield client_id

	def __len__(self):
		return len(self._users)

class UserFilterProxy(object):

	def __init__(self, source, filter_func):
		self.on_added = Event.Event()
		self.on_removed = Event.Event()
		self.on_modified = Event.Event()

		self._source = source
		self._filter_func = filter_func
		self._source.on_added += self._on_source_added
		self._source.on_removed += self._on_source_removed
		self._source.on_modified += self._on_source_modified

		self._client_ids = set()

	def fini(self):
		self.on_added.clear()
		self.on_removed.clear()
		self.on_modified.clear()

	def invalidate(self):
		for client_id in self._client_ids:
			self.on_removed(client_id)
		self._client_ids.clear()
		for client_id in self._source:
			self._on_source_added(client_id)

	def itervalues(self):
		for client_id in self._client_ids:
			yield self._source[client_id]

	def __getitem__(self, client_id):
		return self._source[client_id]

	def __iter__(self):
		for client_id in self._client_ids:
			yield client_id

	def __len__(self):
		return len(self._client_ids)

	def _on_source_added(self, client_id):
		if self.__is_client_included(client_id):
			self.__add_client(client_id)

	def _on_source_removed(self, client_id):
		self.__remove_client(client_id)

	def _on_source_modified(self, client_id):
		if self.__is_client_included(client_id):
			if client_id in self._client_ids:
				self.on_modified(client_id)
			else:
				self.__add_client(client_id)
		else:
			self.__remove_client(client_id)

	def __is_client_included(self, client_id):
		return self._filter_func(self._source[client_id])

	def __add_client(self, client_id):
		if client_id not in self._client_ids:
			self._client_ids.add(client_id)
			self.on_added(client_id)

	def __remove_client(self, client_id):
		if client_id in self._client_ids:
			self._client_ids.remove(client_id)
			self.on_removed(client_id)

def parse_client_query_parameter(parameters_str, parameter):
	# NOTE: this can raise error (too many values to unpack) if 'parameters_str'
	# contains a list (separated with '|'), in such case the
	# parse_client_query_parameters() function should be used
	[entry] = parse_client_query_parameters(parameters_str)
	return entry.get(parameter)

def parse_client_query_parameters(parameters_str):
	return ParamsParser().parse(parameters_str)

class LineEnd(object):
	pass

class ParamsParser(object):

	# Notes on escaping. Excerpt from Server Query Manual (part of TeamSpeak
	# Server installation):
	#
	#   You cannot use whitespaces or any special characters in parameters.
	#   Instead, the TeamSpeak 3 Server supports the use of escape patterns
	#   which can be used to insert newlines, tabs or other special characters
	#   into a parameter string. The same escape patterns are used to clean up
	#   the servers output and prevent parsing issues.
	#
	#   Here's an example on how to escape a parameter string correctly.
	#
	#   Right:
	#   serveredit virtualserver_name=TeamSpeak\s]\p[\sServer
	#
	#   Wrong:
	#   serveredit virtualserver_name=TeamSpeak ]|[ Server
	#
	#   The following characters need to be escaped if they are to be used:
	#   name            char  ascii  replace char  replace ascii
	#   Backslash        \    92     \\            92 92
	#   Slash            /    47     \/            92 47
	#   Whitespace       " "  32     \s            92 115
	#   Pipe             |    124    \p            92 112
	#   Bell             \a   7      \a            92 97
	#   Backspace        \b   8      \b            92 98
	#   Formfeed         \f   12     \f            92 102
	#   Newline          \n   10     \n            92 110
	#   Carriage Return  \r   13     \r            92 114
	#   Horizontal Tab   \t   9      \t            92 116
	#   Vertical Tab     \v   11     \v            92 118
	#
	_ESCAPE_LOOKUP = {
		"\\": "\\",
		"/": "/",
		"s": " ",
		"p": "|",
		"a": "\a",
		"b": "\b",
		"f": "\f",
		"n": "\n",
		"r": "\r",
		"t": "\t",
		"v": "\v"
	}

	def parse(self, parameter_str):
		self._entry = {}
		self._entries = []
		self._change_parse_state(self._parse_key)
		for char in parameter_str:
			self._char_parser(char)
		self._char_parser(LineEnd)
		# Remove reference to itself to allow ParamsParser to delete
		self._char_parser = None
		return self._entries

	def _parse_common(self, char):
		if char == " ":
			self._entry[self._key_name] = self._key_value
			self._change_parse_state(self._parse_key)
			return True
		if char == LineEnd:
			self._entry[self._key_name] = self._key_value
			self._entries.append(self._entry)
			return True
		if char == "|":
			self._entry[self._key_name] = self._key_value
			self._entries.append(self._entry)
			self._entry = {}
			self._change_parse_state(self._parse_key)
			return True
		return False

	def _parse_key(self, char):
		if not self._parse_common(char):
			if char == "=":
				self._change_parse_state(self._parse_value)
			else:
				self._key_name += char

	def _parse_value(self, char):
		if not self._parse_common(char):
			if char == "\\" and not self._escaping:
				self._escaping = True
			elif self._escaping:
				self._key_value += self._ESCAPE_LOOKUP[char]
				self._escaping = False
			else:
				self._key_value += char

	def _change_parse_state(self, parse_func):
		if parse_func == self._parse_key:
			self._key_name = ""
			self._key_value = ""
			self._escaping = False
		self._char_parser = parse_func

def build_command_string(command, args, kwargs):
	fragments = [command]
	args_str = " ".join(arg for arg in args)
	kwargs_str = " ".join("=".join([key, escape_client_query_value(value)]) for key, value in kwargs.items())
	if args_str:
		fragments.append(args_str)
	if kwargs_str:
		fragments.append(kwargs_str)
	return " ".join(fragments)

def escape_client_query_value(value):
	return (str(value)
		.replace("\\", "\\\\")
		.replace("/", "\\/")
		.replace(" ", "\\s")
		.replace("|", "\\p")
		.replace("\a", "\\a")
		.replace("\b", "\\b")
		.replace("\f", "\\f")
		.replace("\n", "\\n")
		.replace("\r", "\\r")
		.replace("\t", "\\t")
		.replace("\v", "\\v")
	)
