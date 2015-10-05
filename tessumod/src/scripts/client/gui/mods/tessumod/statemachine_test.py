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

import sys
import os
base_path  = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.realpath(os.path.join(base_path, "..", "..", "..", "..", "..", "..", "..", "futes", "fakes"))
tmp_path   = os.path.realpath(os.path.join(base_path, "..", "..", "..", "..", "..", "..", "..", "tmp"))
sys.path.append(fakes_path)
from statemachine import StateMachine

def call_counter():
	def func():
		func.count += 1
	func.count = 0
	return func

class TestStateMachine(object):

	def setUp(self):
		self.sm = StateMachine()

	def test_can_transition_to_initial_state(self):
		on_state_enter = call_counter()
		self.sm.add_state("state1", on_enter=on_state_enter)
		self.sm.tick()
		assert on_state_enter.count == 1

	def test_can_transition_to_second_state(self):
		on_state2_enter = call_counter()
		state1 = self.sm.add_state("state1")
		state2 = self.sm.add_state("state2", on_enter=on_state2_enter)
		self.sm.add_transition(state1, state2, "gone foobar")
		self.sm.tick()
		assert on_state2_enter.count == 0
		self.sm.send_event("gone foobar")
		self.sm.tick()
		assert on_state2_enter.count == 1

	def test_can_transition_to_itself(self):
		on_state2_enter = call_counter()
		state1 = self.sm.add_state("state1", on_enter=on_state2_enter)
		self.sm.add_transition(state1, state1, "gone foobar")
		self.sm.tick()
		assert on_state2_enter.count == 1
		self.sm.send_event("gone foobar")
		self.sm.tick()
		assert on_state2_enter.count == 2

	def test_no_transition_until_state_done(self):
		def on_state_enter():
			return False
		state1 = self.sm.add_state("state1", on_enter=on_state_enter)
		state2 = self.sm.add_state("state2")
		self.sm.add_transition(state1, state2, "gone foobar")
		self.sm.tick()
		self.sm.send_event("gone foobar")
		self.sm.tick()
		assert self.sm.current_state() == state1
		self.sm.set_state_done()
		self.sm.tick()
		assert self.sm.current_state() == state2

	def test_transition_triggers_callback(self):
		on_transit = call_counter()
		state1 = self.sm.add_state("state1")
		state2 = self.sm.add_state("state2")
		self.sm.add_transition(state1, state2, "gone foobar", on_transit=on_transit)
		self.sm.tick()
		assert on_transit.count == 0
		self.sm.send_event("gone foobar")
		self.sm.tick()
		assert on_transit.count == 1
