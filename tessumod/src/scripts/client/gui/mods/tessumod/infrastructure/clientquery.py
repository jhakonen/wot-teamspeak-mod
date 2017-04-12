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

import traceback
import asynchat
import asyncore
import socket
import sys
import log
import errno
import copy

from timer import TimerMixin
from eventemitter import EventEmitterMixin
from gui.mods.tessumod.thirdparty.promise import Promise

def noop(*args, **kwargs):
	pass

class Error(Exception):
	'''General exception class which wraps anything that might be thrown or
	returned as error callback argument back to caller.
	'''

	def __init__(self, message, id=None):
		self.__message = message
		self.__id = id
		etype, value, tb = sys.exc_info()
		if etype and value and tb:
			self.__stack_lines = traceback.format_exception(etype, value, tb, None)
		else:
			self.__stack_lines = traceback.format_list(traceback.extract_stack())[:-1]

	@property
	def id(self):
		return self.__id

	def __str__(self):
		stack_str = "".join(self.__stack_lines)
		if self.__id is None:
			return "{0}TeamSpeak Error: {1}".format(stack_str, self.__message)
		else:
			return "{0}TeamSpeak Error: {1} ({2})".format(stack_str, self.__message, self.__id)

	def __repr__(self):
		return "{}(\"{}\", id={})".format(self.__class__.__name__, self.__message, self.__id)

class ClientQueryConnectionMixin(object):
	'''Mixin class which provides basic TCP connection to TeamSpeak's
	ClientQuery plugin.

	Emits following events:
	 - connected        emitted when connected to ts client
	 - disconnected     emitted when connection to ts client is lost
	 - line-received    emitted when line is received from socket
	 - error            emitted when an error occurs
	'''

	def __init__(self):
		self.__address = None
		self.__connected = False
		self.__socket_map = {}
		self.__protocol = ClientQueryProtocol(self.__socket_map)
		super(ClientQueryConnectionMixin, self).__init__()
		self.on("check-events", self.__check_socket)
		self.__protocol.on("connected", self.__on_protocol_connected)
		self.__protocol.on("closed", self.__on_protocol_closed)
		self.__protocol.on("line-received", self.__on_protocol_line_received)
		self.__protocol.on("error", self.__on_protocol_error)

	def connect(self, host, port):
		self.__address = (host, port)
		self.__connect()

	def __connect(self):
		self.__protocol.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__protocol.connect(self.__address)

	def send(self, data):
		log.LOG_DEBUG("send: {0}".format(data))
		self.__protocol.send(data)

	def is_connected(self):
		return self.__connected

	def close(self):
		'''Closes connection.'''
		if self.__protocol.connected:
			self.__protocol.close()

	def __check_socket(self):
		asyncore.loop(timeout=0, count=1, map=self.__socket_map)

	def __keep_alive(self):
		'''Keeps the connection alive. Normally TeamSpeak client disconnects
		the connection after 10 mins if nothing was send to the socket.
		'''
		self.send("\n\r")

	def __on_protocol_connected(self):
		self.__connected = True
		self.on_timeout(60, self.__keep_alive, repeat=True)
		self.emit("connected")

	def __on_protocol_closed(self):
		if self.__connected:
			self.__connected = False
			self.off_timeout(self.__keep_alive)
			self.emit("disconnected")
		self.on_timeout(5, self.__connect)

	def __on_protocol_line_received(self, line):
		log.LOG_DEBUG("recv: {0}".format(line))
		self.emit("line-received", line)

	def __on_protocol_error(self, error):
		self.emit("error", error)

class ClientQueryProtocol(asynchat.async_chat, EventEmitterMixin):
	'''This class handles low level communication with the client query interface.'''

	def __init__(self, map):
		asynchat.async_chat.__init__(self, map=map)
		EventEmitterMixin.__init__(self)
		self.set_terminator("\n\r")

	def connect(self, address):
		try:
			asynchat.async_chat.connect(self, address)
		except socket.error as err:
			if err.args[0] == errno.WSAEWOULDBLOCK:
				self.addr = address

	def send(self, data):
		try:
			return asynchat.async_chat.send(self, data)
		except socket.error as err:
			if err.args[0] == errno.WSAEWOULDBLOCK:
				return 0
			else:
				raise

	def handle_connect(self):
		'''Hook method which is called by async_chat when connection is
		established. Initializes variables and prepares for protocol testing.
		'''
		self.__handle_line = self.__handle_proto_message
		self._in_line = ""

	def handle_close(self):
		'''Hook method which is called by async_chat when connection is closed
		or lost.
		'''
		asynchat.async_chat.handle_close(self)
		self.emit("closed")

	def collect_incoming_data(self, data):
		'''Hook method which is called by async_chat to provide incoming data.
		Data is provided just enough until terminator is found.
		'''
		self._in_line += data

	def found_terminator(self):
		'''Hook method which is called by async_chat to indicate end-of-line.
		Feeds collected line to data handling.
		'''
		self.__handle_line(self._in_line)
		self._in_line = ""

	def log_info(self, message, type="info"):
		'''Undocumented feature of asyncore. Called by asyncore to print log
		messages.
		'''
		if type == "info":
			log.LOG_NOTE(message)
		elif type == "warning":
			log.LOG_WARNING(message)
		else:
			log.LOG_ERROR(message)

	def __handle_proto_message(self, line):
		if line == "TS3 Client":
			self.__handle_line = self.__handle_instructions
		else:
			self.emit("error", Error("Not a Client Query Protocol"))
			self.close()

	def __handle_instructions(self, line):
		if "selected schandlerid" in line:
			self.__handle_line = self.__handle_data_message
			self.emit("connected")

	def __handle_data_message(self, line):
		self.emit("line-received", line)


class ClientQueryAuthenticationMixin(object):
	'''Mixin class which provides authentication key to ClientQuery plugin.

	Emits following events:
	 - authenticated            Connection was succesfully authenticated with an API key
	 - authentication-required  Authentication failed
	'''

	def __init__(self):
		self.__api_key = "";
		self.on("connected", self.__on_connected)
		super(ClientQueryAuthenticationMixin, self).__init__()

	@property
	def api_key(self):
		return self.__api_key

	@api_key.setter
	def api_key(self, api_key):
		if api_key != self.__api_key:
			self.__api_key = api_key
			self.close()

	def __on_connected(self):
		'''Called when connected to ClientQuery.'''
		self.__authenticate()

	def __authenticate(self):
		'''Sends authentication command.'''
		def on_error(err):
			if err.id == 256: # command not found
				# Support older TS clients (3.1.2 and older) which do not have 'auth' command
				# by acting as if authentication succeeded
				self.emit("authenticated")
			else:
				# In other error situations the authentication attempt likely failed because
				# provided API key was not set, or is wrong, or was renewed but not updated to
				# TessuMod's settings
				self.emit("authentication-required")
		(self.command_authenticate(self.__api_key)
			.then(lambda res: self.emit("authenticated"))
			.catch(on_error))


class ClientQuerySendCommandMixin(object):
	'''Mixin class which provides ability to send ClientQuery commands.'''

	def __init__(self):
		self.__command_queue = []
		self.__schandlerid = None
		self.__processing_command = None
		super(ClientQuerySendCommandMixin, self).__init__()
		self.on("line-received", self.__on_line_received)
		self.on("disconnected", self.__on_disconnected)

	def send_command(self, command, input, schandlerid=None):
		'''Method for sending ClientQuery commands.

		Parameters:
		    "command" should be name of the command to send.
		    "input" is a list of dicts. Each key/value in a dict is converted
		        to key=value pair, with proper escaping applied. Each pair is
		        separated from each other with space ( ). Each dict in the list
		        is separated from another with pipe (|).
		    "schandlerid" is server connection ID where to send the command.
		        Any other value than None sends "use" command to switch the
		        connection before the actual command is given.

		Returns ClientQueryCommand object which will emit "error" or "result"
		event on command completion.
		'''
		promise = (Promise.resolve(None)
			.then(lambda res: None if self.is_connected() else Promise.reject(Error("Not connected"))))

		if schandlerid is not None and schandlerid != self.__schandlerid:
			# Tell ClientQuery to use different schandlerid if desired schandlerid differs from
			# previously requested one
			self.__schandlerid = schandlerid
			promise = (promise
				.then(lambda res: self.__queue_command("use", [{"schandlerid": schandlerid}]))
				.then(lambda res: self.__set_schandlerid(schandlerid)))
		return (promise
			.then(lambda res: self.__queue_command(command, input)))

	def __set_schandlerid(self, schandlerid):
		self.__schandlerid = schandlerid

	def __queue_command(self, command, input):
		promise = Promise(lambda resolve, reject: self.__command_queue.append(
			ClientQueryCommand(command, input, resolve, reject)))
		promise.then(lambda res: self.__on_command_done(), lambda err: self.__on_command_done())
		self.__process_command_queue()
		return promise

	def __on_command_done(self):
		self.__processing_command = None
		self.__process_command_queue()

	def __process_command_queue(self):
		if not self.__processing_command and self.__command_queue:
			self.__processing_command = self.__command_queue.pop(0)
			self.send(self.__processing_command.serialize())

	def __on_line_received(self, line):
		if self.__processing_command:
			self.__processing_command.handle_line(line)

	def __on_disconnected(self):
		for command in self.__command_queue:
			command.reject(Error("Disconnected"))
		del self.__command_queue[:]
		self.__processing_command = None

class ClientQueryCommand(object):
	'''Container for a single command, handles receiving response lines and
	calling a callback provided by the caller with the response, or error.
	'''

	__ESCAPE_LOOKUP = {
		"\\": "\\\\",
		"/": "\\/",
		" ": "\\s",
		"|": "\\p",
		"\a": "\\a",
		"\b": "\\b",
		"\f": "\\f",
		"\n": "\\n",
		"\r": "\\r",
		"\t": "\\t",
		"\v": "\\v"
	}

	def __init__(self, command, input, resolve, reject):
		self.__command = command
		self.__input = input
		self.__received_lines = []
		self.__resolve = resolve
		self.__reject = reject

	def serialize(self):
		items = []
		for item_args in self.__input:
			item = []
			for name, value in item_args.iteritems():
				if value is None:
					item.append(name)
				else:
					item.append("=".join([str(name), "".join([self.__ESCAPE_LOOKUP.get(char, char) for char in str(value)])]))
			if item:
				items.append(" ".join(item))
		return " ".join([self.__command, "|".join(items)]) + "\n\r"

	def handle_line(self, line):
		'''Handles a single line received from client query.'''
		# last response line, if contains error status
		if line.startswith("error "):
			first_word, payload = line.split(None, 1)
			args = parse_arguments(payload)
			if args:
				id = int(args[0].get("id", "0"))
				if id != 0:
					self.reject(Error("Command \"{0}\" failed, reason: {1}".format(self.__command, args[0].get("msg", "")), id=id))
				else:
					args = []
					for line in self.__received_lines:
						args += parse_arguments(line)
					self.resolve(args)
		# collect lines before error status line
		else:
			self.__received_lines.append(line)

	def resolve(self, res):
		self.__resolve(res)

	def reject(self, err):
		self.__reject(err)

def parse_arguments(data):
	'''Parses given ClientQuery parameters, returning parameters as a
	list of dicts.
	'''
	return ParamsParser().parse(data)

class ParamsParser(object):

	# see ESCAPING in http://media.teamspeak.com/ts3_literature/TeamSpeak%203%20Server%20Query%20Manual.pdf
	__UNESCAPE_LOOKUP = {
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
		self.__entry = {}
		self.__entries = []
		self.__change_parse_state(self.__parse_key)
		for char in parameter_str:
			self.__char_parser(char)
		self.__char_parser(LineEnd)
		return self.__entries

	def __parse_common(self, char):
		if char == " ":
			self.__entry[self.__key_name] = self.__key_value
			self.__change_parse_state(self.__parse_key)
			return True
		if char == LineEnd:
			self.__entry[self.__key_name] = self.__key_value
			self.__entries.append(self.__entry)
			return True
		if char == "|":
			self.__entry[self.__key_name] = self.__key_value
			self.__entries.append(self.__entry)
			self.__entry = {}
			self.__change_parse_state(self.__parse_key)
			return True
		return False

	def __parse_key(self, char):
		if not self.__parse_common(char):
			if char == "=":
				self.__change_parse_state(self.__parse_value)
			else:
				self.__key_name += char

	def __parse_value(self, char):
		if not self.__parse_common(char):
			if char == "\\" and not self.__escaping:
				self.__escaping = True
			elif self.__escaping:
				self.__key_value += self.__UNESCAPE_LOOKUP[char]
				self.__escaping = False
			else:
				self.__key_value += char

	def __change_parse_state(self, parse_func):
		if parse_func == self.__parse_key:
			self.__key_name = ""
			self.__key_value = ""
			self.__escaping = False
		self.__char_parser = parse_func

class LineEnd(object):
	pass

def cast_parameters(entries, cast_map):
	for entry in entries:
		for key, value in entry.iteritems():
			entry[key] = cast_map.get(key, lambda x: x)(value)
	return entries

class ClientQueryEventsMixin(object):
	'''Mixin class which provides ability to send to register and listen for
	ClientQuery's clientnotify events.

	Can register and emit at least following events:
	 - notifytalkstatuschange
	 - notifymessage
	 - notifymessagelist
	 - notifycomplainlist
	 - notifybanlist
	 - notifyclientmoved
	 - notifyclientleftview
	 - notifycliententerview
	 - notifyclientpoke
	 - notifyclientchatclosed
	 - notifyclientchatcomposing
	 - notifyclientupdated
	 - notifyclientids
	 - notifyclientdbidfromuid
	 - notifyclientnamefromuid
	 - notifyclientnamefromdbid
	 - notifyclientuidfromclid
	 - notifyconnectioninfo
	 - notifychannelcreated
	 - notifychanneledited
	 - notifychanneldeleted
	 - notifychannelmoved
	 - notifyserveredited
	 - notifyserverupdated
	 - channellist
	 - channellistfinished
	 - notifytextmessage
	 - notifycurrentserverconnectionchanged
	 - notifyconnectstatuschange
	'''

	__EVENT_CASTS = {
		"notifytalkstatuschange": {
			"schandlerid": int,
			"status": lambda x: bool(int(x)),
			"clid": int,
			"isreceivedwhisper": lambda x: bool(int(x))
		},
		"notifyclientmoved": {
			"schandlerid": int,
			"ctid": int,
			"reasonid": int,
			"invokerid": int,
			"invokername": str,
			"clid": int
		},
		"notifyclientleftview": {
			"schandlerid": int,
			"clid": int,
			"cfid": int,
			"ctid": int,
			"reasonid": int,
			"reasonmsg": str
		},
		"notifycliententerview": {
			"schandlerid": int,
			"clid": int,
			"cfid": int,
			"ctid": int,
			"reasonid": int,
			"reasonmsg": str
		},
		"notifyclientupdated": {
			"schandlerid": int,
			"clid": int,
			"client_badges": str,
			"client_version": str,
			"client_platform": str,
			"client_login_name": str,
			"client_created": int,
			"client_lastconnected": int,
			"client_totalconnections": int,
			"client_month_bytes_uploaded": int,
			"client_month_bytes_downloaded": int,
			"client_total_bytes_uploaded": int,
			"client_total_bytes_downloaded": int
		},
		"notifycurrentserverconnectionchanged": {
			"schandlerid": int
		},
		"notifyconnectstatuschange": {
			"schandlerid": int,
			"status": str,
			"error": int
		}
	}

	def __init__(self):
		self.__registered_events = []
		super(ClientQueryEventsMixin, self).__init__()
		self.on("line-received", self.__on_line_received, priority=1)
		self.on("disconnected", self.__on_disconnected)

	def is_valid_event(self, event):
		return event in self.__registered_events

	def register_notify(self, name):
		assert name != "any"
		if name in self.__registered_events:
			return Promise.resolve(None)
		self.__registered_events.append(name)
		return self.command_clientnotifyregister(schandlerid=0, event=name)

	def __on_disconnected(self):
		del self.__registered_events[:]

	def __on_line_received(self, line):
		results = line.split(None, 1)
		if self.is_valid_event(results[0]):
			if len(results) == 1:
				self.emit(results[0])
			else:
				self.emit(results[0], self.__parse_parameters(results[0], results[1]))
			raise StopIteration()

	def __parse_parameters(self, event, parameters):
		return cast_parameters(parse_arguments(parameters), self.__EVENT_CASTS.get(event, {}))

class ClientQueryServerConnectionMixin(object):
	'''Mixin class which provides basic server connection info and events.

	Emits following events:
	 - connected-server       emitted when the ts client connects (or has already
	                          connected) to a ts server
	 - disconnected-server    emitted when the ts client disconnects from a ts server
	 - my-cid-changed         emitted when the ts client changes channel
	'''

	def __init__(self):
		super(ClientQueryServerConnectionMixin, self).__init__()
		self.__scdata = {}
		self.on("authenticated", self.__on_authenticated)
		self.on("notifyconnectstatuschange", self.__on_notifyconnectstatuschange)
		self.on("notifyclientmoved", self.__on_notifyclientmoved)

	def get_my_clid(self, schandlerid):
		'''Returns the ts client's client ID at ts server indicated by
		"schandlerid".
		'''
		data = self.__scdata.get(schandlerid, None)
		if data:
			return data["clid"]

	def get_my_cid(self, schandlerid):
		'''Returns the ts client's channel ID at ts server indicated by
		"schandlerid".
		'''
		data = self.__scdata.get(schandlerid, None)
		if data:
			return data["cid"]

	def get_connected_schandlerids(self):
		'''Returns list of server connection IDs which are currently connected
		to ts server.
		'''
		return self.__scdata.keys()

	def __on_authenticated(self):
		(Promise.resolve(None)
			.then(lambda res: self.register_notify("notifyconnectstatuschange"))
			.then(lambda res: self.register_notify("notifyclientmoved"))
			.then(lambda res: self.command_serverconnectionhandlerlist())
			.then(lambda res: Promise.all([self.__execute_whoami(schandlerid) for schandlerid in res]))
			.catch(lambda err: log.LOG_ERROR("Server connection setup failed", err)))

	def __execute_whoami(self, schandlerid):
		return (self.command_whoami(schandlerid=schandlerid)
			.then(lambda res: self.__set_schandler_data(schandlerid, res["clid"], res["cid"]))
			.then(lambda res: self.emit("connected-server", schandlerid))
			# ignore error if not connected to ts server
			.catch(lambda err: None if err.id == 1794 else Promise.reject(err)))

	def __set_schandler_data(self, schandlerid, clid, cid):
		self.__scdata[schandlerid] = {
			"clid": clid,
			"cid": cid
		}

	def __on_disconnected(self):
		for schandlerid in self.__scdata:
			self.emit("disconnected-server", schandlerid)
		self.__scdata.clear()

	def __on_notifyconnectstatuschange(self, args):
		status = args[0]["status"]
		schandlerid = args[0]["schandlerid"]
		if status == "connection_established":
			(self.__execute_whoami(schandlerid)
				.catch(lambda err: log.LOG_ERROR("Whoami command failed", err)))
		elif status == "disconnected":
			if self.__scdata.pop(schandlerid, None):
				self.emit("disconnected-server", schandlerid)

	def __on_notifyclientmoved(self, args):
		entry = args[0]
		schandlerid = entry["schandlerid"]
		if schandlerid in self.__scdata:
			data = self.__scdata[schandlerid]
			if data["clid"] == entry["clid"]:
				data["cid"] = entry["ctid"]
				self.emit("my-cid-changed", schandlerid)

class ClientQueryServerUsersMixin(object):

	def __init__(self):
		super(ClientQueryServerUsersMixin, self).__init__()
		self.__scusers = {}
		self.on("notifycliententerview", self.__on_notifycliententerview)
		self.on("notifyclientleftview", self.__on_notifyclientleftview)
		self.on("notifytalkstatuschange", self.__on_notifytalkstatuschange)
		self.on("notifyclientmoved", self.__on_notifyclientmoved)
		self.on("notifyclientupdated", self.__on_notifyclientupdated)

		self.on("authenticated", self.__on_authenticated)
		self.on("connected-server", self.__on_connected_server)
		self.on("disconnected-server", self.__on_disconnected_server)
		self.on("my-cid-changed", self.__on_my_cid_changed)

	def has_user(self, schandlerid, clid):
		if schandlerid in self.__scusers:
			return clid in self.__scusers[schandlerid]
		return False

	def get_user_parameter(self, schandlerid, clid, parameter):
		user = self.__scusers.get(schandlerid, {}).get(clid, {})
		return user.get(parameter, None)

	def iter_user_ids(self):
		for schandlerid in self.__scusers:
			for clid in self.__scusers[schandlerid]:
				yield schandlerid, clid

	def __on_authenticated(self):
		(Promise.resolve(None)
			.then(lambda res: self.register_notify("notifycliententerview"))
			.then(lambda res: self.register_notify("notifyclientleftview"))
			.then(lambda res: self.register_notify("notifytalkstatuschange"))
			.then(lambda res: self.register_notify("notifyclientmoved"))
			.then(lambda res: self.register_notify("notifyclientupdated"))
			.catch(lambda err: log.LOG_ERROR("Registering notifies failed", err)))

	def __on_connected_server(self, schandlerid):
		self.__clear_server_connection_data(schandlerid)
		self.__scusers[schandlerid] = {}
		(Promise.resolve(None)
			.then(lambda res: self.command_clientlist(modifiers=["uid", "voice"], schandlerid=schandlerid))
			.then(lambda res: Promise.all([self.__add_new_user(schandlerid, user) for user in res]))
			.catch(lambda err: log.LOG_ERROR("Server users setup failed", err))
		)

	def __add_new_user(self, schandlerid, user):
		user["talking"] = user["client_flag_talking"]
		self.__set_server_user(schandlerid=schandlerid, **user)
		return (self.command_clientvariable(schandlerid=schandlerid,
			                         clid=user["clid"],
			                         variablename="client_meta_data")
			.then(lambda res: self.__set_server_user(schandlerid=schandlerid, clid=user["clid"],
				                                     client_meta_data=res)))

	def __on_disconnected_server(self, schandlerid):
		self.__clear_server_connection_data(schandlerid)

	def __on_my_cid_changed(self, schandlerid):
		user = self.__scusers[schandlerid]
		for clid in user:
			self.__set_server_user(schandlerid=schandlerid,	clid=clid)

	def __clear_server_connection_data(self, schandlerid):
		if schandlerid in self.__scusers:
			for clid in self.__scusers[schandlerid].keys():
				self.__remove_server_user(schandlerid=schandlerid, clid=clid)
		self.__scusers.pop(schandlerid, None)

	def __on_notifycliententerview(self, args):
		input = args[0]
		input["cid"] = input.pop("ctid")
		self.__set_server_user(**input)

	def __on_notifyclientleftview(self, args):
		self.__remove_server_user(**args[0])

	def __on_notifytalkstatuschange(self, args):
		args[0]["talking"] = args[0]["status"]
		self.__set_server_user(**args[0])

	def __on_notifyclientmoved(self, args):
		input = copy.copy(args[0])
		input["cid"] = input.pop("ctid")
		self.__set_server_user(**input)

	def __on_notifyclientupdated(self, args):
		self.__set_server_user(**args[0])

	def __set_server_user(self, schandlerid, clid, **kwargs):
		if schandlerid not in self.__scusers:
			return
		users = self.__scusers[schandlerid]
		exists = clid in users
		if exists:
			user = users[clid]
		else:
			user = users[clid] = {
				"schandlerid": schandlerid,
				"clid": clid,
				"cid": None,
				"client-nickname": None,
				"client-unique-identifier": None,
				"client-meta-data": None,
				"talking": False,
				"my-channel": None,
				"is-me": None
			}

		for key, value in kwargs.iteritems():
			self.__set_user_value(user, key, value, user_exists=exists)
		self.__set_user_value(user, "my-channel", user["cid"] == self.get_my_cid(schandlerid), user_exists=exists)
		self.__set_user_value(user, "is-me", user["clid"] == self.get_my_clid(schandlerid), user_exists=exists)

		if not exists:
			self.emit("user-added", schandlerid=schandlerid, clid=clid)

	def __set_user_value(self, user, key, value, user_exists):
		key = key.replace("_", "-")
		old_value = user.get(key, None)
		if value != old_value:
			user[key] = value
			if user_exists:
				self.emit("user-changed-"+key, schandlerid=user["schandlerid"], clid=user["clid"], old_value=old_value, new_value=value)

	def __remove_server_user(self, schandlerid, clid, **kwargs):
		del self.__scusers[schandlerid][clid]
		self.emit("user-removed", schandlerid=schandlerid, clid=clid)

class ClientQueryCommandsImplMixin(object):

	__COMMAND_CASTS = {
		"currentschandlerid": {
			"schandlerid": int
		},
		"clientvariable": {
			"client_meta_data": str
		},
		"servervariable": {
			"virtualserver_name": str
		},
		"serverconnectionhandlerlist": {
			"schandlerid": int
		},
		"whoami": {
			"clid": int,
			"cid": int
		},
		"clientlist": {
			"schandlerid": int,
			"clid": int,
			"cid": int,
			"client_flag_talking": lambda x: bool(int(x))
		}
	}

	def __init__(self):
		super(ClientQueryCommandsImplMixin, self).__init__()

	def __send_command(self, command, input, schandlerid=None):
		return (self.send_command(command, input, schandlerid=schandlerid)
			.then(lambda res: cast_parameters(res, self.__COMMAND_CASTS.get(command, {}))))

	def command_authenticate(self, api_key):
		"""Authenticates the ClientQuery connection.

		This and 'help' commands are the only ones that are accepted when connection is first made.
		The connection must be authenticated before other commands can be executed. Required API
		key is available at TeamSpeak client's options > Addons > Plugins > ClientQuery > Settings.

		Command was added in TeamSpeak 3.1.3. Older versions didn't have this command nor required
		authentication.

		:param api_key: API key from ClientQuery's settings
		:returns: :py:class:`Promise` that resolves with no result, or rejects if command failed
		"""
		return (self.__send_command("auth", [{"apikey": api_key}])
			.then(lambda res: None))

	def command_clientnotifyregister(self, event, schandlerid=0):
		"""Subscribes to an event.

		When done ClientQuery will notify listeners whenever the given event occurs within
		TeamSpeak. Use :py:meth:`EventEmitter.on` method to listen for the events. For list of
		accepted events see documentation of :py:class:`ClientQueryEventsMixin`.

		:param event:       name of the event to subscribe
		:param schandlerid: server connection ID (use 0 to listen events from any server)
		:returns: :py:class:`Promise` that resolves with no result, or rejects if command failed
		"""
		assert self.is_valid_event(event) or event == "any"
		return (self.__send_command("clientnotifyregister", [{"schandlerid": schandlerid, "event": event}])
			.then(lambda res: None))

	def command_currentschandlerid(self):
		"""Returns current server connection ID.

		The current server connection ID is ID of the server window tab which has currently
		selected in the TeamSpeak client.

		:returns :py:class:`Promise` that resolves with server connection ID as result, or
		         rejects if command failed
		"""
		return (self.__send_command("currentschandlerid", [])
			.then(lambda res: res[0]["schandlerid"]))

	def command_clientvariable(self, clid, variablename, schandlerid):
		"""Returns value of a client variable from TeamSpeak.

		Accepted variables include:
		 - client_unique_identifier
		 - client_nickname
		 - client_input_muted
		 - client_output_muted
		 - client_outputonly_muted
		 - client_input_hardware
		 - client_output_hardware
		 - client_meta_data
		 - client_is_recording
		 - client_database_id
		 - client_channel_group_id
		 - client_servergroups
		 - client_away
		 - client_away_message
		 - client_type
		 - client_flag_avatar
		 - client_talk_power
		 - client_talk_request
		 - client_talk_request_msg
		 - client_description
		 - client_is_talker
		 - client_is_priority_speaker
		 - client_unread_messages
		 - client_nickname_phonetic
		 - client_needed_serverquery_view_power
		 - client_icon_id
		 - client_is_channel_commander
		 - client_country
		 - client_channel_group_inherited_channel_id
		 - client_flag_talking
		 - client_is_muted
		 - client_volume_modificator

		:param clid:         client ID
		:param variablename: name of the variable
		:param schandlerid:  server connection ID
		:returns: :py:class:`Promise` that resolves with variable's value as result, or
		          rejects if command failed
		"""
		return (self.__send_command("clientvariable", [{"clid": clid, variablename: None}], schandlerid=schandlerid)
			.then(lambda res: res[0][variablename]))

	def command_clientupdate(self, variablename, variablevalue, schandlerid):
		"""Sets own client's variable to given value.

		Accepted variables include:
		 - client_nickname:             set a new nickname
		 - client_away:                 0 or 1, set us away or back available
		 - client_away_message:         what away message to display when away
		 - client_input_muted:          0 or 1, mutes or unmutes microphone
		 - client_output_muted:         0 or 1, mutes or unmutes speakers/headphones
		 - client_input_deactivated:    0 or 1, same as input_muted, but invisible to other clients
		 - client_is_channel_commander: 0 or 1, sets or removes channel commander
		 - client_nickname_phonetic:    set your phonetic nickname
		 - client_flag_avatar:          set your avatar
		 - client_meta_data:            any string that is passed to all clients that have vision
		                                of you.
		 - client_default_token:        privilege key to be used for the next server connect

		:param variablename:  name of the variable
		:param variablevalue: value of the variable
		:param schandlerid:   server connection ID
		:returns: :py:class:`Promise` that resolves with no result, or rejects if command failed
		"""
		return (self.__send_command("clientupdate", [{variablename: variablevalue}], schandlerid=schandlerid)
			.then(lambda res: None))

	def command_servervariable(self, variablename, schandlerid):
		"""Returns information about TeamSpeak server.

		Accepted variables include:
		 - virtualserver_name
		 - virtualserver_platform
		 - virtualserver_version
		 - virtualserver_created
		 - virtualserver_codec_encryption_mode
		 - virtualserver_default_server_group
		 - virtualserver_default_channel_group
		 - virtualserver_hostbanner_url
		 - virtualserver_hostbanner_gfx_url
		 - virtualserver_hostbanner_gfx_interval
		 - virtualserver_priority_speaker_dimm_modificator
		 - virtualserver_id
		 - virtualserver_hostbutton_tooltip
		 - virtualserver_hostbutton_url
		 - virtualserver_hostbutton_gfx_url
		 - virtualserver_name_phonetic
		 - virtualserver_icon_id
		 - virtualserver_ip
		 - virtualserver_ask_for_privilegekey
		 - virtualserver_hostbanner_mode

		:param variablename: name of the variable
		:param schandlerid:  server connection ID
		:returns: :py:class:`Promise` that resolves with variable's value as result, or
		          rejects if command failed
		"""
		return (self.__send_command("servervariable", [{variablename: None}], schandlerid=schandlerid)
			.then(lambda res: res[0][variablename]))

	def command_serverconnectionhandlerlist(self):
		"""Returns list of active server connection IDs.

		:returns: :py:class:`Promise` that resolves with list of server connection IDs as result,
		          or rejects if command failed
		"""
		return (self.__send_command("serverconnectionhandlerlist", [])
			.then(lambda res: [item["schandlerid"] for item in res]))

	def command_whoami(self, schandlerid):
		"""Returns own client's client ID and channel ID.

		Returned value is dict of following properties:
		 - clid: client ID
		 - cid:  channel ID

		:param schandlerid:  server connection ID
		:returns: :py:class:`Promise` that resolves with a dict of client ID and channel ID as
		          result, or rejects if command failed
		"""
		return (self.__send_command("whoami", [], schandlerid=schandlerid)
			.then(lambda res: res[0]))

	def command_clientlist(self, modifiers, schandlerid):
		"""Returns list of visible clients in the server.

		Each client in the list has following properties:
		 - clid:               client ID
		 - cid:                channel ID
		 - client_database_id: client database id
		 - client_nickname:    nickname
		 - client_type:        client type

        Additional properties can be requested with following modifiers:
		 - uid:
		    - client_unique_identifier
		 - away:
		    - client_away
		    - client_away_message
		 - voice:
		    - client_flag_talking
		    - client_input_muted
		    - client_output_muted
		    - client_input_hardware
		    - client_output_hardware
		    - client_talk_power
		    - client_is_talker
		    - client_is_priority_speaker
		    - client_is_recording
		    - client_is_channel_commander
		    - client_is_muted
		 - groups:
		    - client_servergroups
		    - client_channel_group_id
		 - icon:
		    - client_icon_id
		 - country:
		    - client_country

		:param modifiers:    list of modifiers
		:param schandlerid:  server connection ID
		:returns: :py:class:`Promise` that resolves with a list of client dicts as result, or
		          rejects if command failed
		"""
		args = [{"-" + modifier: None} for modifier in modifiers]
		return self.__send_command("clientlist", args, schandlerid=schandlerid)

class ClientQuery(ClientQueryConnectionMixin, EventEmitterMixin, TimerMixin, ClientQuerySendCommandMixin,
	ClientQueryCommandsImplMixin, ClientQueryEventsMixin, ClientQueryServerConnectionMixin,
	ClientQueryServerUsersMixin, ClientQueryAuthenticationMixin):

	def __init__(self):
		super(ClientQuery, self).__init__()

	def start_event_checking(self, interval):
		self.off_timeout(self.__check_events)
		self.on_timeout(interval, self.__check_events, repeat=True)

	def __check_events(self):
		self.emit("check-events")
