# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2019  Janne Hakonen
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

import collections
import email.parser
import re
import socket
import sys
import traceback
try:
	# Python 2 (game)
	from urlparse import urlparse
except ImportError:
	# Python 3 (test suite)
	from urllib.parse import urlparse

import BigWorld

from .asyncore_utils import AsynchatExtended

READ_STATUS = 0
READ_HEADERS = 1
READ_BODY = 2

CONNECT_TIMEOUT = 30

STATUS_REGEXP = re.compile("^HTTP/[0-9.]+ ([0-9]+) (.+)$")
Result = collections.namedtuple("Result", ["status_code", "status_message", "headers", "body"])

class HTTPClient(object):
	def __init__(self, event_loop):
		self._event_loop = event_loop

	def get(self, url, callback):
		HTTPProtocol(self._event_loop, url, callback)

class HTTPProtocol(AsynchatExtended):
	def __init__(self, event_loop, url, callback):
		AsynchatExtended.__init__(self, event_loop)
		self._url = url
		result = urlparse(url)
		port = 80 if result.port is None else result.port
		host = result.netloc.split(':')[0]
		path = result.path
		assert result.scheme == "http"
		self.callback = callback
		self.reading_state = READ_STATUS
		self.message_parser = email.parser.Parser()
		self.in_buffer = []
		self.body = None
		self.status_code = None
		self.status_message = None
		self.headers = None
		self.out_buffer = "\r\n".join([
			"GET %s HTTP/1.0" % path,
			"Host: %s" % host,
		]) + "\r\n\r\n"
		self._timeout_handle = BigWorld.callback(CONNECT_TIMEOUT, self._connect_timeout)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((host, port))
		self.set_terminator(b"\r\n")

	def _connect_timeout(self):
		self.done(RuntimeError("HTTP GET timed out: %s" % self._url))

	def writable(self):
		return len(self.out_buffer) > 0

	def handle_connect(self):
		pass

	def handle_write(self):
		sent = self.send(self.out_buffer.encode('utf8'))
		self.out_buffer = self.out_buffer[sent:]

	def handle_error(self):
		traceback.print_exc()
		self.done(sys.exc_info()[1])

	def collect_incoming_data(self, data):
		self.in_buffer.append(data.decode('utf8'))

	def found_terminator(self):
		if self.reading_state == READ_STATUS:
			# e.g. HTTP/1.1 200 OK
			match = STATUS_REGEXP.match(self.take_received_data())
			if match:
				self.status_code = match.group(1)
				self.status_message = match.group(2)
				self.reading_state = READ_HEADERS
				self.set_terminator(b"\r\n\r\n")
			else:
				self.done(RuntimeError("Failed to parse response's status line"))
		elif self.reading_state == READ_HEADERS:
			self.headers = self.message_parser.parsestr(self.take_received_data(), headersonly=True)
			if "Content-Length" in self.headers:
				self.reading_state = READ_BODY
				self.set_terminator(int(self.headers["content-length"]))
			else:
				self.done(None, self.build_result())
		elif self.reading_state == READ_BODY:
			self.body = self.take_received_data()
			self.done(None, self.build_result())

	def take_received_data(self):
		data = "".join(self.in_buffer)
		del self.in_buffer[:]
		return data

	def done(self, error=None, result=None):
		try:
			BigWorld.cancelCallback(self._timeout_handle)
		except ValueError:
			# Ignore error:
			#     ValueError: py_cancelCallback: Incorrect callback ID.
			pass
		self.close()
		callback = self.callback
		# Set self.callback to None so that we don't accidentally call it more
		# than once
		self.callback = None
		if callback:
			callback(error, result)

	def build_result(self):
		return Result(self.status_code, self.status_message, self.headers.items(), self.body)
