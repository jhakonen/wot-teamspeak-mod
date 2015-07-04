import unittest
import sys
import os
import time
import random
from functools import partial
import shutil

from event_loop import EventLoop
from ts_client_query import TSClientQueryService
import mod_settings

SCRIPT_DIRPATH = os.path.dirname(os.path.realpath(__file__))
FAKES_DIRPATH  = os.path.join(SCRIPT_DIRPATH, "..", "fakes")
MOD_DIRPATH    = os.path.join(SCRIPT_DIRPATH, "..", "..", "tessumod", "src", "scripts", "client", "mods")
TMP_DIRPATH    = os.path.join(os.getcwd(), "tmp")

class TestCaseBase(unittest.TestCase):

	def setUp(self):
		self.tessu_mod = None
		self.ts_client_query_server = None
		self.event_loop = EventLoop()

		shutil.rmtree(TMP_DIRPATH, ignore_errors=True)

		if FAKES_DIRPATH not in sys.path:
			sys.path.append(FAKES_DIRPATH)
		if MOD_DIRPATH not in sys.path:
			sys.path.append(MOD_DIRPATH)

		res_mods_version_dirpath = os.path.join(TMP_DIRPATH, "res_mods", "version")

		import ResMgr
		ResMgr.RES_MODS_VERSION_PATH = res_mods_version_dirpath
		mod_settings.INI_DIRPATH = os.path.join(res_mods_version_dirpath, "..", "configs", "tessu_mod")
		mod_settings.reset_cache_file()
		mod_settings.reset_settings_file()
		self.change_mod_settings(
			General = {
				# "log_level": "0", # enable for debug logging
				"speak_stop_delay": "0" # makes tests execute faster
			},
			TSClientQueryService = {
				"polling_interval": "0" # makes tests execute faster
			}
		)

	def tearDown(self):
		if self.ts_client_query_server:
			self.ts_client_query_server.stop()
		sys.path.remove(FAKES_DIRPATH)
		sys.path.remove(MOD_DIRPATH)

	def start_ts_client(self, **state):
		assert self.ts_client_query_server == None, "Cannot start TS client if it is already running"
		self.ts_client_query_server = TSClientQueryService()
		self.ts_client_query_server.start()
		self.change_ts_client_state(**state)

	def start_game(self, on_events={}, **game_state):
		import tessu_mod
		self.tessu_mod = tessu_mod

		def call_wrapper(callback, *args, **kwargs):
			callback()

		for name, callbacks in on_events.iteritems():
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
		self.change_game_state(**game_state)

	def run_in_event_loop(self, verifiers, timeout=20, min_wait=0):
		self.__verifiers = verifiers
		self.event_loop.call(self.__on_loop, repeat=True, timeout=0.05)
		self.event_loop.call(self.__check_verify, repeat=True, timeout=1)
		self.__max_end_time = time.time() + timeout
		self.__min_end_time = time.time() + min_wait
		self.event_loop.execute()

	def change_ts_client_state(self, **state):
		assert self.ts_client_query_server, "TS client must be running to change its state"
		if "running" in state:
			if not state["running"]:
				self.ts_client_query_server.stop()
				self.ts_client_query_server = None
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

	def change_mod_settings(self, **groups):
		for group_name, variables in groups.iteritems():
			for var_name, var_value in variables.iteritems():
				mod_settings.set_setting(group_name, var_name, var_value)

	def change_mod_user_cache(self, **groups):
		for group_name, variables in groups.iteritems():
			for var_name, var_value in variables.iteritems():
				mod_settings.set_cache_entry(group_name, var_name, var_value)

	def call_later(self, callback, timeout=0):
		self.event_loop.call(callback, timeout=timeout)

	def __on_loop(self):
		import BigWorld
		BigWorld.tick()
		if self.ts_client_query_server:
			self.ts_client_query_server.check()
		self.assertLess(time.time(), self.__max_end_time, "Execution took too long")

	def __check_verify(self):
		try:
			if time.time() >= self.__min_end_time and all(verifier() for verifier in self.__verifiers):
				self.event_loop.exit()
		except Exception as error:
			print error
