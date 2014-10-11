import asynchat
import asyncore
import socket
import threading
import time
import re
from test_events import process_events
from Queue import Queue, Empty

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

	def set_cmd_response(self, command, response=None, error=None):
		self._data.cmd_responses[command] = (response, error)

	def send_event(self, event):
		self._data.event_queue.put(event)

	def get_user_clid(self, ts_name):
		if ts_name not in self._clids:
			self._clids.append(ts_name)
		return self._clids.index(ts_name)

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
		self.cmd_responses = {}
		self.event_queue = Queue()

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
		for message in data_source.connect_messages:
			self.push(message + "\n\r")
 
	def collect_incoming_data(self, data):
		self._buffer += data
 
	def found_terminator(self):
		command = self._buffer.strip()
		self._buffer = ""
		self.handle_command(command)

	def handle_command(self, command):
		def send_status(code=0, message="ok"):
			message = message.replace(" ", "\\s")
			self.push("error id={0} msg={1}\n\r".format(code, message))

		if command in self._data_source.cmd_responses:
			response, error = self._data_source.cmd_responses[command]
			if response:
				self.push(response + "\n\r")
			if error:
				send_status(*error)
			else:
				send_status()
				# collect registered event types
				if "clientnotifyregister" in command:
					matches = re.search("event=([a-z]+)", command)
					self._registered_events.append(matches.group(1))
		else:
			send_status(256, "command not found")
			print "ERROR: Response missing for command:", repr(command)

	def tick(self):
		try:
			event = self._data_source.event_queue.get(block=False)
		except Empty:
			return
		if event.split(None, 1)[0] in self._registered_events:
			self.push(event + "\n\r")
		else:
			self._data_source.event_queue.put(event)
