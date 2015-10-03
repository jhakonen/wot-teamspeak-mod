import asynchat
import asyncore
import socket
import threading
import time
import re
import copy
import random
from Queue import Queue, Empty

_SELF_USER_NAME = "Testinukke"
_NO_RESPONSE = (None, None)

class TSClientQueryService(object):

	def __init__(self):
		self.__sock_map = {}
		self._clids = []
		self._server = None
		self._data = Data()
		self.insert_connect_message(0, "TS3 Client")
		self.insert_connect_message(1, "Welcome to the TeamSpeak 3 "
			+ "ClientQuery interface, type \"help\" for a list of commands "
			+ "and \"help <command>\" for information on a specific command.")
		self.insert_connect_message(2, "selected schandlerid={0}".format(self._data.schandler_id))
		self.set_user(_SELF_USER_NAME)

	def start(self):
		if not self._server:
			try:
				self._server = TSClientQueryServer("localhost", 25639, self.__sock_map, self._data)
			except:
				self.stop()

	def stop(self):
		if self.__sock_map:
			for socket in self.__sock_map.values():
				socket.close()
			self.__sock_map.clear()

	def check(self):
		if self.__sock_map:
			asyncore.loop(0, map=self.__sock_map, count=1)
			if self._server and self._server.handler:
				self._server.handler.tick()

	def insert_connect_message(self, index, message):
		self._data.connect_messages[index] = message

	def send_event(self, event):
		self._data.event_queue.put(event)

	def set_connected_to_server(self, connected):
		self._data.connected_to_server = connected

	def set_user(self, name, **kwargs):
		if name not in self._clids:
			self._clids.append(name)
		clid = str(self._clids.index(name))
		if clid not in self._data.users:
			self._data.users[clid] = User(service=self, name=name, clid=clid)
		if "schandlerid" not in kwargs:
			kwargs["schandlerid"] = self._data.schandler_id
		self._data.users[clid].set(**kwargs)

	def get_user(self, name=None, clid=None):
		if clid is not None:
			return self._data.users[str(clid)]
		elif name is not None:
			for user_clid in self._data.users:
				user = self._data.users[user_clid]
				if user.name == name:
					return user
		else:
			raise RuntimeError("Parameter missing")

class User(object):

	def __init__(self, service, name, clid):
		self._service = service
		self._name = name
		self._clid = str(clid)
		self._cid = None
		self._cluid = None
		self._schandlerid = None
		self._metadata = None
		self._speaking = None
		self.set()

	def set(self, **kwargs):
		self.cid = str(kwargs["cid"] if "cid" in kwargs else 1)
		self.cluid = str(kwargs["cluid"] if "cluid" in kwargs else "BAADF00D" + self._clid)
		self.schandlerid = str(kwargs["schandlerid"] if "schandlerid" in kwargs else 1)
		self.metadata = str(kwargs["metadata"] if "metadata" in kwargs else "")
		self.speaking = kwargs["speaking"] if "speaking" in kwargs else False

	@property
	def name(self):
		return self._name

	@property
	def clid(self):
		return self._clid

	@property
	def cid(self):
		return self._cid
	@cid.setter
	def cid(self, value):
		self._cid = value

	@property
	def cluid(self):
		return self._cluid
	@cluid.setter
	def cluid(self, value):
		self._cluid = value

	@property
	def schandlerid(self):
		return self._schandlerid
	@schandlerid.setter
	def schandlerid(self, value):
		self._schandlerid = value

	@property
	def metadata(self):
		return self._metadata
	@metadata.setter
	def metadata(self, value):
		if self._metadata is not None and self._metadata != value:
			self._service.send_event("notifyclientupdated schandlerid={0} clid={1} client_meta_data={2}".format(
				self._schandlerid,
				self._clid,
				value
			))
		self._metadata = value

	@property
	def speaking(self):
		return self._speaking
	@speaking.setter
	def speaking(self, value):
		if self._speaking is not None and self._speaking != value:
			self._service.send_event("notifytalkstatuschange status={0} clid={1}".format(1 if value else 0, self._clid))
		self._speaking = value

class Data(object):
	def __init__(self):
		self.connect_messages = ["", "", ""]
		self.event_queue = Queue()
		self.responses = []
		self.connected_to_server = False
		self.users = {}
		self.schandler_id = int(random.uniform(1, 10))

class TSClientQueryServer(asyncore.dispatcher):
	def __init__(self, host, port, sock_map, data_source):
		asyncore.dispatcher.__init__(self, map=sock_map)
		self.handler = None
		self._sock_map = sock_map
		self._data_source = data_source
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.bind((host, port))
		self.listen(5)

	def handle_accept(self):
		select_result = self.accept()
		if select_result is not None:
			socket, address = select_result
			self.handler = TSClientQueryHandler(socket, self._sock_map, self._data_source)

class TSClientQueryHandler(asynchat.async_chat):
	def __init__(self, socket, socket_map, data_source):
		asynchat.async_chat.__init__(self, sock=socket, map=socket_map)
		self._data_source = data_source
 		self.set_terminator("\n")
		self._buffer = ""
		self._data_source = data_source
		self._registered_events = []
		self._prev_users = {}
		for message in data_source.connect_messages:
			self.push(message + "\n\r")
 
	def collect_incoming_data(self, data):
		self._buffer += data
 
	def found_terminator(self):
		command = self._buffer.strip()
		self._buffer = ""
		self.handle_command(command)

	def push(self, data):
		asynchat.async_chat.push(self, data.encode('ascii'))
		self._data_source.responses.append(data)

	def handle_command(self, command):
		command_type, params_str = re.match("^([\S]+)\s?(.*)", command).groups()
		param_str_list = params_str.split()

		params = {}
		options = []
		for param_str in param_str_list:
			if param_str.startswith("-"):
				options.append(param_str[1:])
			else:
				key, value = re.match("([^=]+)=?(.*)", param_str).groups()
				params[key] = value
		if options:
			params["options"] = options

		if hasattr(self, "handle_command_" + command_type):
			status = getattr(self, "handle_command_" + command_type)(**params)
			if status:
				self.send_status(*status)
			else:
				self.send_status()
		else:
			self.send_status(256, "command not found")
			print "ERROR: Response missing for command:", repr(command)

	def send_status(self, code=0, message="ok"):
		if code is None or message is None:
			return
		message = message.replace(" ", "\\s")
		self.push("error id={0} msg={1}\n\r".format(code, message))

	def handle_command_clientnotifyunregister(self):
		if not self._registered_events:
			return _NO_RESPONSE
		self._registered_events.clear()

	def handle_command_clientnotifyregister(self, event, **ignored):
		if event in self._registered_events:
			return _NO_RESPONSE
		self._registered_events.append(event)

	def handle_command_whoami(self):
		if self._data_source.connected_to_server:
			self.push("clid={0} cid={1}\n\r".format(
				self.get_my_user().clid, self.get_my_user().cid))
		else:
			return 1794, "not connected"

	def handle_command_clientgetuidfromclid(self, clid, **ignored):
		user = self._data_source.users[clid]
		self._data_source.event_queue.put("notifyclientuidfromclid schandlerid={0} clid={1} cluid={2} nickname={3}"
			.format(user.schandlerid, user.clid, user.cluid, escape(user.name)))

	def handle_command_clientvariable(self, clid, **requested_vars):
		user = self._data_source.users[clid]
		self.push("clid=" + clid)
		if "client_meta_data" in requested_vars:
			self.push(" client_meta_data=" + escape(user.metadata))
		self.push("\n\r")

	def handle_command_clientlist(self, options=[]):
		entries = []
		for clid in self._data_source.users:
			user = self._data_source.users[clid]
			params = [
				"clid=" + str(user.clid),
				"cid=" + str(user.cid),
				"client_database_id=DBID" + str(user.clid),
				"client_nickname=" + user.name,
				"client_type=0"
			]
			if "uid" in options:
				params.append("client_unique_identifier=" + user.cluid)
			entries.append(" ".join(escape(param) for param in params))
		self.push(("|".join(entries) + "\n\r"))

	def handle_command_clientupdate(self, client_meta_data, **ignored):
		pass

	def handle_command_currentschandlerid(self):
		self.push("schandlerid={0}\n\r".format(self._data_source.schandler_id))

	def handle_command_use(self, schandlerid):
		self._data_source.schandler_id = int(schandlerid)

	def handle_command_servervariable(self, virtualserver_name=None):
		if virtualserver_name is not None:
			self.push("virtualserver_name=Dummy\sServer\n\r")

	def user_value_changed(self, clid, name, value):
		if name == "speaking":
			self._data_source.event_queue.put("notifytalkstatuschange status={0} clid={1}".format(1 if value else 0, clid))

	def get_my_user(self):
		for clid in self._data_source.users:
			user = self._data_source.users[clid]
			if user.name == _SELF_USER_NAME:
				return user

	def tick(self):
		try:
			event = self._data_source.event_queue.get(block=False)
			if event.split(None, 1)[0] in self._registered_events:
				self.push(event + "\n\r")
			else:
				self._data_source.event_queue.put(event)
		except Empty:
			pass

def escape(value):
	return value.replace(" ", "\s")
