# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

class EventLoop(object):

	@classmethod
	def callback(cls, timeout, function, *args, **kwargs):
		if args or kwargs:
			function = partial(function, *args, **kwargs)
		return BigWorld.callback(timeout, function)

	@classmethod
	def cancel_callback(cls, id):
		BigWorld.cancelCallback(id)

	@classmethod
	def create_callback_repeater(cls, function):
		return _EventRepeater(function)

class _EventRepeater(object):

	def __init__(self, function):
		self.__id       = None
		self.__timeout  = None
		self.__started  = False
		self.__function = function

	def start(self, timeout):
		self.__timeout = timeout
		self.stop()
		self.__start_callback()
		self.__started  = True

	def __start_callback(self):
		if self.__id is None:
			self.__id = EventLoop.callback(self.__timeout, self.__on_timeout)

	def stop(self):
		if self.__id is not None:
			EventLoop.cancel_callback(self.__id)
			self.__id = None
		self.__started = False

	def is_active(self):
		return self.__started

	def __on_timeout(self):
		self.__id = None
		self.__function()
		if self.__started:
			self.__start_callback()
