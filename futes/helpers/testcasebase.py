import unittest
import sys
import os
import time
import random
from functools import partial

from event_loop import EventLoop
from ts_client_query import TSClientQueryService
import mod_settings

SCRIPT_DIRPATH = os.path.dirname(os.path.realpath(__file__))
FAKES_DIRPATH  = os.path.join(SCRIPT_DIRPATH, "..", "fakes")
MOD_DIRPATH    = os.path.join(SCRIPT_DIRPATH, "..", "..", "tessumod", "src", "scripts", "client", "mods")

class TestCaseBase(unittest.TestCase):

	def setUp(self):
		self.tessu_mod = None
		self.event_loop = EventLoop()

		if FAKES_DIRPATH not in sys.path:
			sys.path.append(FAKES_DIRPATH)
		if MOD_DIRPATH not in sys.path:
			sys.path.append(MOD_DIRPATH)

		self.ts_client_query_server = TSClientQueryService()
		self.ts_client_query_server.start()
		mod_settings.remove_cache_file()
		mod_settings.reset_settings_file()
		self.change_mod_settings_state(
			General = {
				# "log_level": "0", # enable for debug logging
				"speak_stop_delay": "0" # makes tests execute faster
			},
			TSClientQueryService = {
				"polling_interval": "0" # makes tests execute faster
			}
		)

	def tearDown(self):
		self.ts_client_query_server.stop()
		sys.path.remove(FAKES_DIRPATH)
		sys.path.remove(MOD_DIRPATH)

	def load_mod(self, events={}):
		import tessu_mod
		self.tessu_mod = tessu_mod

		def call_wrapper(callback, *args, **kwargs):
			callback()

		for name, callbacks in events.iteritems():
			for callback in callbacks:
				wrapped_callback = partial(call_wrapper, callback)
				if name == "on_connected_to_ts_server":
					tessu_mod.g_ts.on_connected_to_server += wrapped_callback
				elif name == "on_connected_to_ts_client":
					tessu_mod.g_ts.on_connected += wrapped_callback
				elif name == "on_disconnected_from_ts_client":
					tessu_mod.g_ts.on_disconnected += wrapped_callback
				else:
					raise RuntimeError("No such event: {0}".format(name))

		# hack to speed up testing
		import tessu_utils.ts3
		tessu_utils.ts3._UNREGISTER_WAIT_TIMEOUT = 0.5

	def verify(self):
		raise NotImplementedError()

	def run_in_event_loop(self, verifiers, timeout=20, min_wait=0):
		self.__verifiers = verifiers
		self.event_loop.call(self.__on_loop, repeat=True, timeout=0.05)
		self.event_loop.call(self.__check_verify, repeat=True, timeout=1)
		self.__max_end_time = time.time() + timeout
		self.__min_end_time = time.time() + min_wait
		self.event_loop.execute()

	def change_ts_client_state(self, **state):
		if "running" in state:
			if state["running"]:
				self.ts_client_query_server.start()
			else:
				self.ts_client_query_server.stop()
		if "connected_to_server" in state:
			self.ts_client_query_server.set_connected_to_server(state["connected_to_server"])
		if "users" in state:
			for name, data in state["users"].iteritems():
				self.ts_client_query_server.set_user(name, **data)

	def change_game_state(self, **state):
		import BigWorld, Avatar, Account
		assert self.tessu_mod, "Mod must be loaded first before changing game state"

		if state["mode"] == "battle":
			BigWorld.player(Avatar.Avatar())
			if "players" in state:
				for player in state["players"]:
					vehicle_id = random.randint(0, 1000000)
					dbid = random.randint(0, 1000000)
					BigWorld.player().arena.vehicles[vehicle_id] = {
						"accountDBID": dbid,
						"name":        player["name"],
						"isAlive":     True
					}
		elif state["mode"] == "lobby":
			BigWorld.player(Account.PlayerAccount())
			if "players" in state:
				for id, player in enumerate(state["players"]):
					BigWorld.player().prebattle.rosters[0][id] = {
						"name": player["name"],
						"dbID": random.randint(0, 1000000)
					}

	def get_player_id(self, name):
		import BigWorld
		if hasattr(BigWorld.player(), "arena"):
			for vehicle in BigWorld.player().arena.vehicles.itervalues():
				if vehicle["name"] == name:
					return vehicle["accountDBID"]

	def get_vehicle_id(self, name):
		import BigWorld
		if hasattr(BigWorld.player(), "arena"):
			for vehicle_id, vehicle in BigWorld.player().arena.vehicles.iteritems():
				if vehicle["name"] == name:
					return vehicle_id

	def change_mod_settings_state(self, **groups):
		for group_name, variables in groups.iteritems():
			for var_name, var_value in variables.iteritems():
				mod_settings.set_setting(group_name, var_name, var_value)

	def call_later(self, callback, timeout=0):
		self.event_loop.call(callback, timeout=timeout)

	def __on_loop(self):
		import BigWorld
		BigWorld.tick()
		self.ts_client_query_server.check()
		self.assertLess(time.time(), self.__max_end_time, "Execution took too long")

	def __check_verify(self):
		try:
			if time.time() >= self.__min_end_time and all(verifier() for verifier in self.__verifiers):
				self.event_loop.exit()
		except Exception as error:
			print error
