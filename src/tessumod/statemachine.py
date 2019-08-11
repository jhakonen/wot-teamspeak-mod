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

'''This module defines a generic state machine implementation.
The StateMachine class allows you define states and transitions between them.
'''

from .utils import LOG_DEBUG

def noop(*args, **kwargs):
	pass

class State(object):
	def __init__(self, name, on_enter):
		self._name = name
		self._on_enter = on_enter

	def name(self):
		return self._name

	def enter(self):
		LOG_DEBUG("Entering state '{0}'".format(self._name))
		return self._on_enter()

class Transition(object):
	def __init__(self, event_name, on_transit):
		self._event_name = event_name
		self._on_transit = on_transit

	def check_event(self, event_name):
		return self._event_name == event_name

	def transit(self):
		LOG_DEBUG("Transition by event '{0}'".format(self._event_name))
		self._on_transit()

class StateMachine(object):
	
	def __init__(self):
		self._state_id = None
		self._states = []
		self._transitions = {}
		self._events = []
		self._is_state_done = True

	def add_state(self, name, on_enter=noop):
		self._states.append(State(name, on_enter=on_enter))
		return len(self._states) - 1

	def add_transition(self, start_state, end_state, event_name, on_transit=noop):
		if start_state not in self._transitions:
			self._transitions[start_state] = []
		self._transitions[start_state].append((Transition(event_name, on_transit), end_state))

	def send_event(self, event_name):
		self._events.append(event_name)

	def tick(self):
		new_state_id = None

		if self._events and self._is_state_done:
			event_name = self._events.pop(0)
			LOG_DEBUG("Handling event '{0}'".format(event_name))
			try:
				for transition, next_state_id in self._transitions[self._state_id]:
					if transition.check_event(event_name):
						transition.transit()
						new_state_id = next_state_id
						break
			except IndexError:
				LOG_DEBUG("No transitions for event '{0}'".format(event_name))

		if self._state_id is None:
			new_state_id = 0
		if new_state_id is not None:
			self._state_id = new_state_id
			self._is_state_done = self._states[self._state_id].enter() is not False

	def current_state(self):
		return self._state_id

	def set_state_done(self):
		self._is_state_done = True
