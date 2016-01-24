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
gameapi.EventLoop.callback().

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
import copy

from utils import noop,	with_args
from statemachine import StateMachine
import async
import gameapi
import log

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
		self.on_connected = gameapi.Event()
		self.on_disconnected = gameapi.Event()
		self.on_connected_to_server = gameapi.Event()
		self.on_disconnected_from_server = gameapi.Event()
		self.on_channel_changed = gameapi.Event()

		# public models
		self.users = UserModel()
		self.users_in_my_channel = UserFilterProxy(
			source      = self.users,
			filter_func = lambda user: user["channel_id"] == self._my_channel_id
		)
		self.users_in_my_channel.on_added += self.on_user_entered_my_channel

		self._socket_map = {}
		self._wot_nickname = None
		self._my_client_id = None
		self._my_channel_id = None
		self._schandler_id = None

		self._protocol = _ClientQueryProtocol(self, self._socket_map)
		self._protocol.on_ready += functools.partial(self._send_sm_event, "protocol_ready")
		self._protocol.on_closed += functools.partial(self._send_sm_event, "protocol_closed")

		self._sm = StateMachine()

		not_connected_state          = self._sm.add_state("Not Connected")
		connecting_to_ts_state       = self._sm.add_state("Connecting to TS", on_enter=self._on_connecting_to_ts_state)
		connecting_failed_state      = self._sm.add_state("Connecting Failed", on_enter=self._on_connect_failed_state)
		connected_to_ts_state        = self._sm.add_state("Connected to TS", on_enter=self._on_connected_to_ts_state)
		connected_to_ts_server_state = self._sm.add_state("Connected to TS Server", on_enter=self._on_connected_to_ts_server_state)

		self._sm.add_transition(not_connected_state,          connecting_to_ts_state,       "connect")
		self._sm.add_transition(connecting_to_ts_state,       connected_to_ts_state,        "protocol_ready", on_transit=self.on_connected)
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

	def get_current_channel_id(self):
		return self._my_channel_id

	def _on_connecting_to_ts_state(self):
		self._stop_pinging()
		self._protocol.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self._protocol.connect((self.HOST, self.PORT))

	def _on_connect_failed_state(self):
		gameapi.EventLoop.callback(_RETRY_TIMEOUT, self._send_sm_event, "connect_retry")

	def _send_command(self, command, callback=noop, timeout=_COMMAND_WAIT_TIMEOUT):
		def on_command_finish(err, lines):
			if err:
				log.LOG_DEBUG(type(err).__name__ + ": " + str(err))
				if isinstance(err, clientquery.APINotConnectedError) or isinstance(err, clientquery.APIInvalidSchandlerIDError):
					self._send_sm_event("not_connected_error")
				else:
					self._protocol.close()
			callback(err, lines)
		self._protocol.send_command(command, on_command_finish, timeout)

	def _on_connected_to_ts_state(self):
		self._my_client_id = None
		self._my_channel_id = None
		self._schandler_id = None
		self.users.clear()
		self.users_in_my_channel.invalidate()

		def unregister(callback):
			self._send_command("clientnotifyunregister", callback, timeout=_UNREGISTER_WAIT_TIMEOUT)
		def register_connection_change(callback):
			self._send_command("clientnotifyregister schandlerid=0 event=notifycurrentserverconnectionchanged", callback)
		def get_currentschandlerid(callback):
			def on_finish(err, lines):
				if not err:
					self._schandler_id = int(parse_client_query_parameter(lines[0], "schandlerid"))
				callback(err, lines)
			self._send_command("currentschandlerid", on_finish)
		def register_talk_status_change(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifytalkstatuschange".format(self._schandler_id), callback)
		def register_client_update(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifyclientupdated".format(self._schandler_id), callback)
		def register_client_enter_view(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifycliententerview".format(self._schandler_id), callback)
		def register_client_left_view(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifyclientleftview".format(self._schandler_id), callback)
		def register_client_moved(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifyclientmoved".format(self._schandler_id), callback)
		def register_connect_status_change(callback):
			self._send_command("clientnotifyregister schandlerid={0} event=notifyconnectstatuschange".format(self._schandler_id), callback)
		def use_schandler_id(callback):
			self._send_command("use schandlerid={0}".format(self._schandler_id), callback)
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
						self.users.add(
							client_id  = int(entry.get("clid")),
							nick       = entry.get("client_nickname"),
							unique_id  = entry.get("client_unique_identifier"),
							channel_id = int(entry.get("cid"))
						)
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
		if self._is_pinging:
			self._ping()
		else:
			self._is_pinging = True
			def loop():
				if self._is_pinging:
					self._ping()
					gameapi.EventLoop.callback(_RETRY_TIMEOUT, loop)
			loop()

	def _ping(self):
		def on_finish(err, ignored):
			if not err:
				self._send_sm_event("ping_ok")
		self._update_my_client_id(on_finish)

	def _stop_pinging(self):
		self._is_pinging = False

	def _update_my_client_id(self, callback=noop):
		def on_whoami(err, lines):
			if not err and lines:
				[entry] = parse_client_query_parameters(lines[0])
				self._my_client_id = int(entry.get("clid"))
				new_channel_id = int(entry.get("cid"))
				if new_channel_id != self._my_channel_id:
					self._my_channel_id = new_channel_id
					self.on_channel_changed()
					self.users_in_my_channel.invalidate()
			callback(err, None)
		self._send_command("whoami", on_whoami)

	def get_client_meta_data(self, client_id, callback=noop):
		def on_finish(err, lines):
			if err:
				callback(err, None)
			else:
				data = parse_client_query_parameter(lines[0], "client_meta_data")
				if data is None:
					log.LOG_WARNING("get_client_meta_data failed, value:", data)
					callback(None, "")
				else:
					callback(None, data)
		self._send_command("clientvariable clid={0} client_meta_data".format(client_id), on_finish)

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
				self._send_command("clientupdate client_meta_data={0}".format(data), callback)
		self.get_client_meta_data(self._my_client_id, on_get_client_meta_data)

	def get_clientlist(self, callback=noop):
		def on_clientlist(err, lines):
			if err:
				callback(err, None)
			else:
				callback(None, parse_client_query_parameters(lines[0]))
		self._send_command("clientlist -uid", on_clientlist)

	def _get_server_name(self, callback=noop):
		def on_finish(err, lines):
			if err:
				callback(err, None)
			else:
				callback(None, parse_client_query_parameter(lines[0], "virtualserver_name"))
		self._send_command("servervariable virtualserver_name", on_finish)

	def on_user_entered_my_channel(self, client_id):
		user = self.users[client_id]
		def on_get_wot_nickname(err, wot_nickname):
			if not err:
				user["wot_nick"] = wot_nickname
		self.get_wot_nickname(client_id, on_get_wot_nickname)

	def on_notifycurrentserverconnectionchanged_ts3_event(self, line):
		self._send_sm_event("tab_changed")

	def on_notifytalkstatuschange_ts3_event(self, line):
		[entry] = parse_client_query_parameters(line)
		client_id = int(entry.get("clid"))
		speaking = int(entry.get("status")) == 1
		if client_id not in self.users:
			return
		user = copy.copy(self.users[client_id])
		if user["speaking"] != speaking:
			user["speaking"] = speaking
			self.users.add(**user)

	def on_notifyclientupdated_ts3_event(self, line):
		[entry] = parse_client_query_parameters(line)
		client_id = int(entry.get("clid"))
		if client_id in self.users:
			user = self.users[client_id]
			nick = entry.get("client_nickname")
			if nick:
				user["nick"] = nick
			metadata = entry.get("client_meta_data")
			if metadata:
				user["wot_nick"] = self._get_wot_nick_from_metadata(metadata)

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
		self.on_connected = gameapi.Event()
		self.on_closed = gameapi.Event()
		self.on_ready = gameapi.Event()

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

		def connect_fix(address):
			self.addr = address
		self.connect = _would_block_windows_workaround(self.connect, connect_fix)
		self.send = _would_block_windows_workaround(self.send, lambda self, data: 0)

	def connect(self, address):
		self._opened = True
		asynchat.async_chat.connect(self, address)

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

	def collect_incoming_data(self, data):
		'''Hook method which is called by async_chat to provide incoming data.
		Data is provided just enough until terminator is found.
		'''
		log.LOG_DEBUG("<< " + data)
		self._in_line += data

	def found_terminator(self):
		'''Hook method which is called by async_chat to indicate end-of-line.
		Feeds collected line to data handling.
		'''
		try:
			self._data_in_handler(self._in_line)
		except:
			log.LOG_CURRENT_EXCEPTION()
			self.close()
		self._in_line = ""

	def push(self, data):
		log.LOG_DEBUG(">> " + data)
		asynchat.async_chat.push(self, data)

	def _handle_in_data_proto_test(self, line):
		'''Checks that we really contacted TeamSpeak client query interface and
		nothing something totally else.
		'''
		if "ts3 client" in line.lower():
			log.LOG_NOTE("TS client query protocol detected")
			self._data_in_handler = self._handle_in_data_welcome_message
		else:
			log.LOG_ERROR("Not TS client query protocol")
			self.close()

	def log_info(self, message, type="info"):
		'''Undocumented feature of asyncore. Called by asyncore to print log
		messages. Converts the log message to WOT logging.
		'''
		if type == "info":
			log.LOG_NOTE(message)
		elif type == "error":
			log.LOG_ERROR(message)
		elif type == "warning":
			log.LOG_WARNING(message)

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

class UserModel(object):

	def __init__(self):
		self._users = {}
		self.on_added = gameapi.Event()
		self.on_removed = gameapi.Event()
		self.on_modified = gameapi.Event()

	def add(self, client_id, **kwargs):
		if client_id is None:
			return
		if client_id in self._users:
			new_user = copy.copy(self._users[client_id])
			new_user.update(kwargs)
			is_new = False
		else:
			new_user = {
				"nick": None,
				"wot_nick": None,
				"client_id": client_id,
				"unique_id": None,
				"channel_id": None,
				"speaking": False
			}
			new_user.update(kwargs)
			is_new = True
		is_modified = not is_new and self._users[client_id] != new_user
		self._users[client_id] = new_user

		if is_new:
			self.on_added(client_id)
		elif is_modified:
			self.on_modified(client_id)

	def remove(self, client_id):
		del self._users[client_id]
		self.on_removed(client_id)

	def clear(self):
		client_ids = self._users.keys()
		self._users.clear()
		for client_id in client_ids:
			self.on_removed(client_id)

	def __getitem__(self, client_id):
		return self._users[client_id]

	def __iter__(self):
		for client_id in self._users:
			yield client_id

	def __len__(self):
		return len(self._users)

class UserFilterProxy(object):

	def __init__(self, source, filter_func):
		self.on_added = gameapi.Event()
		self.on_removed = gameapi.Event()
		self.on_modified = gameapi.Event()

		self._source = source
		self._filter_func = filter_func
		self._source.on_added += self._on_source_added
		self._source.on_removed += self._on_source_removed
		self._source.on_modified += self._on_source_modified

		self._client_ids = set()

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

	# see ESCAPING in http://media.teamspeak.com/ts3_literature/TeamSpeak%203%20Server%20Query%20Manual.pdf
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
