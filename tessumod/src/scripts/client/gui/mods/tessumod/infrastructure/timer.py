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

def set_eventloop(eventloop):
	global g_eventloop
	g_eventloop = eventloop

class TimerMixin(object):
	'''Mixin class which provides ability to register functions for timed calls
	from event loop.
	'''

	def __init__(self):
		self.__function_map = {}
		super(TimerMixin, self).__init__()

	def on_timeout(self, secs, function, repeat=False):
		'''Registers "function" to be called after "secs" seconds from event
		loop.
		
		Setting "repeat" to True makes the call to repeat indefinately with
		interval of "secs" seconds.
		'''
		self.off_timeout(function)
		if repeat:
			repeater = g_eventloop.create_callback_repeater(function)
			repeater.start(secs)
			self.__function_map[function] = repeater
		else:
			self.__function_map[function] = g_eventloop.callback(secs, function)

	def off_timeout(self, function):
		'''Unregisters previously registered timed function call.'''
		if function in self.__function_map:
			value = self.__function_map[function]
			if hasattr(value, "stop"):
				value.stop()
			else:
				g_eventloop.cancel_callback(value)
			del self.__function_map[function]
