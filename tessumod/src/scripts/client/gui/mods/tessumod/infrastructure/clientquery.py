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

from timer import TimerMixin
from eventemitter import EventEmitterMixin

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
		self.__protocol.on("disconnected", self.__on_protocol_disconnected)
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

	def __on_protocol_disconnected(self):
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
		self.emit("disconnected")

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
		self.__handle_line = self.__handle_welcome_message
		if line != "TS3 Client":
			self.emit("error", Error("Not a Client Query Protocol"))
			self.close()

	def __handle_welcome_message(self, line):
		self.__handle_line = self.__handle_schandlerid_message

	def __handle_schandlerid_message(self, line):
		self.__handle_line = self.__handle_data_message
		self.emit("connected")

	def __handle_data_message(self, line):
		self.emit("line-received", line)


class ClientQuerySendCommandMixin(object):
	'''Mixin class which provides ability to send ClientQuery commands.'''

	def __init__(self):
		self.__actions = []
		self.__schandlerid = None
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
		assert self.is_connected()
		action = {"command": ClientQueryCommand(command, input)}
		action["command"].on("result", self.__on_command_done)
		action["command"].on("error", self.__on_command_done)
		if schandlerid is not None:
			action["schandlerid"] = int(schandlerid)
			action["use-command"] = ClientQueryCommand("use", [{"schandlerid": schandlerid}])
			action["use-command"].on("result", self.__on_use_command_finish)
			action["use-command"].on("error", self.__on_use_command_failed)
		self.__actions.append(action)
		# send action right away if no other actions are waiting
		if len(self.__actions) == 1:
			self.__send_action(action)
		return action["command"]

	def __on_use_command_finish(self, result):
		self.__schandlerid = int(result["args"][0]["schandlerid"])
		if self.__actions:
			del self.__actions[0]["use-command"]
			self.__send_action(self.__actions[0])

	def __on_use_command_failed(self, error):
		if self.__actions:
			self.__actions[0]["command"].emit("error", error)
			del self.__actions[0]
		if self.__actions:
			self.__send_action(self.__actions[0])

	def __on_command_done(self, *args, **kwargs):
		if self.__actions:
			del self.__actions[0]
		if self.__actions:
			self.__send_action(self.__actions[0])

	def __send_action(self, action):
		if "use-command" in action:
			if self.__schandlerid != action["schandlerid"]:
				self.send(action["use-command"].serialize())
			else:
				del action["use-command"]
				self.send(action["command"].serialize())
		else:
			self.send(action["command"].serialize())

	def __on_line_received(self, line):
		if self.__actions:
			action = self.__actions[0]
			if "use-command" in action:
				action["use-command"].handle_line(line)
			else:
				action["command"].handle_line(line)

	def __on_disconnected(self):
		for action in self.__actions:
			action["command"].emit("error", Error("Disconnected"))
		del self.__actions[:]

class ClientQueryCommand(EventEmitterMixin):
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

	def __init__(self, command, input):
		self.__command = command
		self.__input = input
		self.__received_lines = []
		super(ClientQueryCommand, self).__init__()

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
					self.emit("error", Error("Command \"{0}\" failed, reason: {1}".format(self.__command, args[0].get("msg", "")), id=id))
				else:
					args = []
					for line in self.__received_lines:
						args += parse_arguments(line)
					self.emit("result", {"data": "\n".join(self.__received_lines), "args": args})
		# collect lines before error status line
		else:
			self.__received_lines.append(line)

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

	def __init__(self):
		self.__registered_events = []
		super(ClientQueryEventsMixin, self).__init__()
		self.on("line-received", self.__on_line_received, priority=1)
		self.on("disconnected", self.__on_disconnected)

	def is_valid_event(self, event):
		return event in self.__registered_events

	def register_notify(self, name):
		assert name != "any"
		if name not in self.__registered_events:
			self.__registered_events.append(name)
			self.command_clientnotifyregister(schandlerid=0, event=name)

	def __on_disconnected(self):
		del self.__registered_events[:]

	def __on_line_received(self, line):
		results = line.split(None, 1)
		if self.is_valid_event(results[0]):
			if len(results) == 1:
				self.emit(results[0])
			else:
				self.emit(results[0], parse_arguments(results[1]))
			raise StopIteration()

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
		self.on("connected", self.__on_connected)
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

	def __on_connected(self):
		self.register_notify("notifyconnectstatuschange")
		self.register_notify("notifyclientmoved")
		def on_serverconnectionhandlerlist_finish(error, result):
			if error:
				log.LOG_ERROR("serverconnectionhandlerlist command failed", error)
			else:
				for schandlerid in result:
					self.__execute_whoami(schandlerid)
		self.command_serverconnectionhandlerlist(callback=on_serverconnectionhandlerlist_finish)

	def __execute_whoami(self, schandlerid):
		def on_whoami_finish(error, result):
			if error:
				if error.id == 1794: # not connected to ts server
					pass
				else:
					log.LOG_ERROR("whoami command failed", error)
			else:
				self.__scdata[result["schandlerid"]] = {
					"clid": result["clid"],
					"cid": result["cid"]
				}
				self.emit("connected-server", result["schandlerid"])
		self.command_whoami(schandlerid=schandlerid, callback=on_whoami_finish)

	def __on_disconnected(self):
		for schandlerid in self.__scdata:
			self.emit("disconnected-server", schandlerid)
		self.__scdata.clear()

	def __on_notifyconnectstatuschange(self, args):
		status = args[0]["status"]
		schandlerid = int(args[0]["schandlerid"])
		if status == "connection_established":
			self.__execute_whoami(schandlerid)
		elif status == "disconnected":
			if self.__scdata.pop(schandlerid, None):
				self.emit("disconnected-server", schandlerid)

	def __on_notifyclientmoved(self, args):
		schandlerid = int(args[0]["schandlerid"])
		if schandlerid in self.__scdata:
			data = self.__scdata[schandlerid]
			if data["clid"] == int(args[0]["clid"]):
				data["cid"] = int(args[0]["ctid"])
				self.emit("my-cid-changed", schandlerid)

class ClientQueryServerUsersMixin(object):

	__USER_VALUE_CONVERTERS = {
		"cid": lambda x: int(x),
		"talking": lambda x: bool(int(x))
	}

	def __init__(self):
		super(ClientQueryServerUsersMixin, self).__init__()
		self.__scusers = {}
		self.on("notifycliententerview", self.__on_notifycliententerview)
		self.on("notifyclientleftview", self.__on_notifyclientleftview)
		self.on("notifytalkstatuschange", self.__on_notifytalkstatuschange)
		self.on("notifyclientmoved", self.__on_notifyclientmoved)
		self.on("notifyclientupdated", self.__on_notifyclientupdated)

		self.on("connected", self.__on_connected)
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

	def __on_connected(self):
		self.register_notify("notifycliententerview")
		self.register_notify("notifyclientleftview")
		self.register_notify("notifytalkstatuschange")
		self.register_notify("notifyclientmoved")
		self.register_notify("notifyclientupdated")

	def __on_connected_server(self, schandlerid):
		self.__clear_server_connection_data(schandlerid)
		self.__scusers[schandlerid] = {}
		self.command_clientlist(schandlerid=schandlerid, callback=self.__on_clientlist_finish)

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

	def __on_clientlist_finish(self, error, result):
		if error:
			log.LOG_ERROR("clientlist command failed", error)
		else:
			for client in result["clients"]:
				client["talking"] = client["client_flag_talking"]
				self.__set_server_user(schandlerid=result["schandlerid"], **client)
				self.command_clientvariable(
					schandlerid=result["schandlerid"],
					clid=client["clid"],
					variablename="client_meta_data",
					callback=self.__on_get_client_metadata_finish
				)

	def __on_get_client_metadata_finish(self, error, result):
		if error:
			log.LOG_ERROR("Failed to get client's metadata", error)
		else:
			self.__set_server_user(**result)

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
		input = args[0]
		input["cid"] = input.pop("ctid")
		self.__set_server_user(**input)

	def __on_notifyclientupdated(self, args):
		self.__set_server_user(**args[0])

	def __set_server_user(self, schandlerid, clid, **kwargs):
		schandlerid = int(schandlerid)
		clid = int(clid)
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
		new_value = self.__USER_VALUE_CONVERTERS.get(key, lambda x: x)(value)
		if new_value != old_value:
			user[key] = new_value
			if user_exists:
				self.emit("user-changed-"+key, schandlerid=user["schandlerid"], clid=user["clid"], old_value=old_value, new_value=new_value)

	def __remove_server_user(self, schandlerid, clid, **kwargs):
		schandlerid = int(schandlerid)
		clid = int(clid)
		del self.__scusers[schandlerid][clid]
		self.emit("user-removed", schandlerid=schandlerid, clid=clid)

class ClientQueryCommandsImplMixin(object):

	def __init__(self):
		super(ClientQueryCommandsImplMixin, self).__init__()

	def command_clientnotifyregister(self, event, schandlerid=0, callback=noop):
		assert self.is_valid_event(event) or event == "any"
		def on_success(result):
			callback(None, None)
		def on_error(error):
			callback(error, None)
		self.send_command("clientnotifyregister", [{"schandlerid": schandlerid, "event": event}]).on("result", on_success).on("error", on_error)

	def command_currentschandlerid(self, callback=noop):
		def on_success(result):
			callback(None, {"schandlerid": result["args"][0]["schandlerid"]})
		def on_error(error):
			callback(error, None)
		self.send_command("currentschandlerid", []).on("result", on_success).on("error", on_error)

	def command_clientvariable(self, clid, variablename, schandlerid=None, callback=noop):
		def on_success(result):
			ret = {"schandlerid": schandlerid}
			ret.update(result["args"][0])
			callback(None, ret)
		def on_error(error):
			callback(error, None)
		self.send_command("clientvariable", [{"clid": clid, variablename: None}], schandlerid=schandlerid).on("result", on_success).on("error", on_error)

	def command_clientupdate(self, variablename, variablevalue, schandlerid=None, callback=noop):
		def on_success(result):
			callback(None, {"schandlerid": schandlerid})
		def on_error(error):
			callback(error, None)
		self.send_command("clientupdate", [{variablename: variablevalue}], schandlerid=schandlerid).on("result", on_success).on("error", on_error)

	def command_servervariable(self, variablename, schandlerid=None, callback=noop):
		def on_success(result):
			ret = {"schandlerid": schandlerid}
			ret.update(result["args"][0])
			callback(None, ret)
		def on_error(error):
			callback(error, None)
		self.send_command("servervariable", [{variablename: None}], schandlerid=schandlerid).on("result", on_success).on("error", on_error)

	def command_serverconnectionhandlerlist(self, callback=noop):
		def on_success(result):
			callback(None, [int(item["schandlerid"]) for item in result["args"]])
		def on_error(error):
			callback(error, None)
		self.send_command("serverconnectionhandlerlist", []).on("result", on_success).on("error", on_error)

	def command_whoami(self, schandlerid=None, callback=noop):
		def on_success(result):
			callback(None, {
				"clid": int(result["args"][0]["clid"]),
				"cid": int(result["args"][0]["cid"]),
				"schandlerid": schandlerid
			})
		def on_error(error):
			callback(error, None)
		self.send_command("whoami", [], schandlerid=schandlerid).on("result", on_success).on("error", on_error)

	def command_clientlist(self, schandlerid=None, callback=noop):
		def on_success(result):
			clients = []
			for item in result["args"]:
				item["clid"] = int(item["clid"])
				item["cid"] = int(item["cid"])
				clients.append(item)
			callback(None, {
				"schandlerid": schandlerid,
				"clients": clients
			})
		def on_error(error):
			callback(error, None)
		self.send_command("clientlist", [{"-uid": None}, {"-voice": None}], schandlerid=schandlerid).on("result", on_success).on("error", on_error)

class ClientQuery(ClientQueryConnectionMixin, EventEmitterMixin, TimerMixin, ClientQuerySendCommandMixin,
	ClientQueryCommandsImplMixin, ClientQueryEventsMixin, ClientQueryServerConnectionMixin,
	ClientQueryServerUsersMixin):

	def __init__(self):
		super(ClientQuery, self).__init__()

	def start_event_checking(self, interval):
		self.off_timeout(self.__check_events)
		self.on_timeout(interval, self.__check_events, repeat=True)

	def __check_events(self):
		self.emit("check-events")
