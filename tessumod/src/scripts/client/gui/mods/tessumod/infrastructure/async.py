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

'''This module contains helpers for making asyncronous calls easier.
Idea for API comes from Caolan McMahon's javascript library with same name:
https://github.com/caolan/async
'''

def series(actions, callback):
	Series(actions, callback).call_next()

class Series(object):

	def __init__(self, actions, callback):
		self._actions = actions
		self._callback = callback
		self._err = None
		self._datas = []

	def call_next(self):
		if len(self._actions) == 0:
			self._callback(self._err, self._datas if self._datas else None)
		else:
			self._actions.pop(0)(self._action_callback)

	def _action_callback(self, err, data):
		if err:
			self._err = err
			self._datas = data
			del self._actions[:]
		elif data:
			self._datas.append(data)
		self.call_next()
