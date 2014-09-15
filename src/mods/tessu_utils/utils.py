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

import BigWorld
import threading
from debug_utils import LOG_CURRENT_EXCEPTION

def call_in_loop(secs, func):
	def wrapper(*args, **kwargs):
		func(*args, **kwargs)
		BigWorld.callback(secs, wrapper)
	BigWorld.callback(secs, wrapper)

def with_args(func, *args, **kwargs):
	def wrapper():
		return func(*args, **kwargs)
	return wrapper

class ThreadCaller(object):

	def __init__(self):
		self.calls = []

	def call(self, func, callback):
		call = ThreadCall(func, callback)
		self.calls.append(call)
		call.start()

	def tick(self):
		for call in self.calls:
			done = call.check()
			if done:
				self.calls.remove(call)

class ThreadCall(object):
	def __init__(self, func, callback):
		self._finished = threading.Event()
		self._func = func
		self._result_callback = callback
		self._error = None
		self._result = None
		self._thread = threading.Thread(target=self._target)

	def start(self):
		self._thread.start()

	def check(self):
		if self._finished.is_set():
			try:
				self._result_callback(self._error, self._result)
			except:
				LOG_CURRENT_EXCEPTION()
			return True
		return False

	def _target(self):
		try:
			self._result = self._func()
		except Exception as e:
			self._error = e
		self._finished.set()
