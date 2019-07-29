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

from utils import RepeatTimer, LOG_NOTE, LOG_WARNING, LOG_ERROR

import asynchat
import asyncore
import collections

class EventLoopAdapter(object):

	def __init__(self):
		self.socket_map = SocketMapNotifier(self._on_socket_map_changed)
		self._timer = None

	def set_polling_interval(self, interval):
		self._timer = RepeatTimer(interval)
		self._timer.on_timeout += self._call_asyncore_loop

	def _on_socket_map_changed(self, count):
		if not self._timer:
			return
		if count:
			self._timer.start()
		else:
			self._timer.stop()

	def _call_asyncore_loop(self):
		asyncore.loop(timeout=0, count=1, map=self.socket_map)

class SocketMapNotifier(collections.MutableMapping):

	def __init__(self, listener):
		self._listener = listener
		self._map = {}

	def __getitem__(self, key):
		return self._map[key]

	def __setitem__(self, key, value):
		self._map[key] = value
		self._listener(len(self._map))

	def __delitem__(self, key):
		del self._map[key]
		self._listener(len(self._map))

	def __iter__(self):
		return iter(self._map)

	def __len__(self):
		return len(self._map)

class AsynchatExtended(asynchat.async_chat):

	def __init__(self, event_loop):
		asynchat.async_chat.__init__(self, map=event_loop.socket_map)

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

	def handle_close(self):
		self.close()

	def log_info(self, message, type="info"):
		'''Undocumented feature of asyncore. Called by asyncore to print log
		messages. Converts the log message to WOT logging.
		'''
		if type == "info":
			LOG_NOTE(message)
		elif type == "warning":
			LOG_WARNING(message)
		elif type == "error":
			LOG_ERROR(message)
