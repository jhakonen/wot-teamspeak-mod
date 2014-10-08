import asynchat
import asyncore
import socket
import threading
import time

class TSClientQueryService(object):

	def __init__(self):
		self._thread = threading.Thread(target=self._run_in_thread)
		self._server = None
		self._data = Data()
		self.insert_connect_message(0, "TS3 Client")
		self.insert_connect_message(1, "Welcome to the TeamSpeak 3 "
			+ "ClientQuery interface, type \"help\" for a list of commands "
			+ "and \"help <command>\" for information on a specific command.")
		self.insert_connect_message(2, "selected schandlerid=1")

	def start(self):
		self._stop = False
		self._thread.start()
		while not self._server:
			time.sleep(0.1)

	def stop(self):
		self._stop = True
		self._thread.join()

	def insert_connect_message(self, index, message):
		self._data.connect_messages[index] = message

	def set_cmd_response(self, command, response=None, error=None):
		self._data.cmd_responses[command] = (response, error)

	def _run_in_thread(self):
		try:
			sock_map = {}
			self._server = TSClientQueryServer(
				"localhost", 25639, sock_map, self._data)
			while not self._stop:
				asyncore.loop(0.1, map=sock_map, count=1)
		finally:
			self._server = None

class Data(object):
	def __init__(self):
		self.connect_messages = ["", "", ""]
		self.cmd_responses = {}

class TSClientQueryServer(asyncore.dispatcher):
	def __init__(self, host, port, sock_map, data_source):
		asyncore.dispatcher.__init__(self, map=sock_map)
		self._sock_map = sock_map
		self._data_source = data_source
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.listen(5)

	def handle_accept(self):
		select_result = self.accept()
		if select_result is not None:
			socket, address = select_result
			print "Incoming connection from {0}".format(address)
			self.handler = TSClientQueryHandler(socket, self._sock_map, self._data_source)

class TSClientQueryHandler(asynchat.async_chat):
	def __init__(self, socket, socket_map, data_source):
		asynchat.async_chat.__init__(self, sock=socket, map=socket_map)
		self._data_source = data_source
 		self.set_terminator("\n\r")
		self._buffer = ""
		self._data_source = data_source
		for message in data_source.connect_messages:
			self.push(message + "\n\r")
 
	def collect_incoming_data(self, data):
		self._buffer += data
 
	def found_terminator(self):
		command = self._buffer
		self._buffer = ""

		if command in self._data_source.cmd_responses:
			response, error = self._data_source.cmd_responses[command]
			if response:
				self.push(response + "\n\r")
			code, message = error if error else (0, "ok")
			message = message.replace(" ", "\\s")
			self.push("error id={0} msg={1}\n\r".format(code, message))
		else:
			print "ERROR: Response missing for command:", message
