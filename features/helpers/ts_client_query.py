import asynchat
import asyncore
import socket
import threading
import time
import re
import copy
from test_events import process_events
from Queue import Queue, Empty

_SELF_USER_NAME = "Testinukke"

class TSClientQueryService(object):

	def __init__(self):
		self._error_in_thread = None
		self._clids = []
		self._thread = threading.Thread(target=self._run_in_thread)
		self._server = None
		self._data = Data()
		self.insert_connect_message(0, "TS3 Client")
		self.insert_connect_message(1, "Welcome to the TeamSpeak 3 "
			+ "ClientQuery interface, type \"help\" for a list of commands "
			+ "and \"help <command>\" for information on a specific command.")
		self.insert_connect_message(2, "selected schandlerid=1")
		self.add_user(_SELF_USER_NAME)

	def start(self):
		self._error_in_thread = None
		self._stop = False
		self._thread.start()
		while not self._server:
			process_events()

	def stop(self):
		self._error_in_thread = None
		if self._thread.is_alive():
			self._stop = True
			self._thread.join()

	def check(self):
		error = self._error_in_thread
		if error:
			self._error_in_thread = None
			raise error

	def insert_connect_message(self, index, message):
		self._data.connect_messages[index] = message

	def send_event(self, event):
		self._data.event_queue.put(event)

	def set_connected_to_server(self, connected):
		self._data.connected_to_server = connected

	def add_user(self, name, metadata=""):
		if name not in self._clids:
			self._clids.append(name)
		clid = self._clids.index(name)

		self._data.users[str(clid)] = dict(
			name=name,
			clid=str(clid),
			cid=str(1),
			cluid="BAADF00D" + str(clid),
			schandlerid="",
			metadata=metadata,
			speaking=False
		)

	def set_user_speaking(self, ts_name, speaking):
		for clid in self._data.users:
			user = self._data.users[clid]
			if user["name"] == ts_name:
				user["speaking"] = speaking

	def _run_in_thread(self):
		try:
			sock_map = {}
			self._server = TSClientQueryServer(
				"localhost", 25639, sock_map, self._data)
			while not self._stop:
				asyncore.loop(0.1, map=sock_map, count=1)
				if self._server.handler:
					self._server.handler.tick()
		except Exception as e:
			self._error_in_thread = e
		finally:
			self._server = None
			for socket in sock_map.values():
				socket.close()

class Data(object):
	def __init__(self):
		self.connect_messages = ["", "", ""]
		self.event_queue = Queue()
		self.connected_to_server = False
		self.users = {}

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
		message = message.replace(" ", "\\s")
		self.push("error id={0} msg={1}\n\r".format(code, message))

	def handle_command_clientnotifyregister(self, event, **ignored):
		self._registered_events.append(event)

	def handle_command_whoami(self):
		if self._data_source.connected_to_server:
			self.push("clid={0} cid={1}\n\r".format(
				self.get_my_user()["clid"], self.get_my_user()["cid"]))
		else:
			return 1794, "not connected"

	def handle_command_clientgetuidfromclid(self, clid, **ignored):
		user = self._data_source.users[clid]
		self._data_source.event_queue.put("notifyclientuidfromclid schandlerid={0} clid={1} cluid={2} nickname={3}"
			.format(user["schandlerid"], user["clid"], user["cluid"], escape(user["name"])))

	def handle_command_clientvariable(self, clid, **requested_vars):
		user = self._data_source.users[clid]
		self.push("clid=" + clid)
		if "client_meta_data" in requested_vars:
			self.push(" client_meta_data=" + user["metadata"].replace(" ", "\s"))
		self.push("\n\r")

	def handle_command_clientlist(self, options=[]):
		entries = []
		for clid in self._data_source.users:
			user = self._data_source.users[clid]
			params = [
				"clid=" + str(user["clid"]),
				"cid=" + str(user["cid"]),
				"client_database_id=DBID" + str(user["clid"]),
				"client_nickname=" + user["name"],
				"client_type=0"
			]
			if "uid" in options:
				params.append("client_unique_identifier=" + user["cluid"])
			entries.append(" ".join(escape(param) for param in params))
		self.push(("|".join(entries) + "\n\r"))

	def user_value_changed(self, clid, name, value):
		if name == "speaking":
			self._data_source.event_queue.put("notifytalkstatuschange status={0} clid={1}".format(1 if value else 0, clid))

	def get_my_user(self):
		for clid in self._data_source.users:
			user = self._data_source.users[clid]
			if user["name"] == _SELF_USER_NAME:
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

		for clid in self._prev_users:
			old_user = self._prev_users[clid]
			new_user = self._data_source.users[clid]
			for key in old_user:
				if old_user[key] != new_user[key]:
					self.user_value_changed(clid, key, new_user[key])
		self._prev_users = copy.deepcopy(self._data_source.users)

def escape(value):
	return value.replace(" ", "\s")
