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

import logutils

logger = logutils.logger.getChild("eventemitter")

class EventEmitterMixin(object):
	'''Mixin class which provides ability to emit and receive send events.'''

	def __init__(self):
		self.__listeners = {}
		super(EventEmitterMixin, self).__init__()

	def emit(self, event, *args, **kwargs):
		'''Emits given "event" name. Iterates through all event handlers
		registered for that event passing given arguments for each handler.

		Raising StopIteration exception from inside event handler prevents
		calling of any further event handlers.
		'''
		if event in self.__listeners:
			for priority, function in self.__listeners[event]:
				try:
					function(*args, **kwargs)
				except StopIteration:
					return
				except Exception:
					logger.exception("Exception caught in eventemitter")

	def on(self, event, function, priority=0):
		'''Registers an event handler "function" for "event".
		When event is emitted each registered event handler is called in the
		order of "priority".
		Calling order of event handlers with same "priority" is undefined.
		'''
		assert callable(function)
		if event not in self.__listeners:
			self.__listeners[event] = []
		self.__listeners[event].append((priority, function))
		self.__listeners[event].sort(reverse=True, key=lambda listener: listener[0])
		return self
