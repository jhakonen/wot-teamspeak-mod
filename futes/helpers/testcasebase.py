import unittest
import sys
import os
import time
import random
from functools import partial
import shutil
import mmap
import struct
import json

from event_loop import EventLoop
from ts_client_query import TSClientQueryService
import mod_settings

SCRIPT_DIRPATH           = os.path.dirname(os.path.realpath(__file__))
FAKES_DIRPATH            = os.path.join(SCRIPT_DIRPATH, "..", "fakes")
MOD_SRC_DIRPATH          = os.path.join(SCRIPT_DIRPATH, "..", "..", "tessumod", "src")
MOD_SCRIPTS_DIRPATH      = os.path.join(MOD_SRC_DIRPATH, "scripts", "client", "mods")
TMP_DIRPATH              = os.path.join(os.getcwd(), "tmp")
MODS_VERSION_DIRPATH     = os.path.join(TMP_DIRPATH, "res_mods", "version")
INI_DIRPATH              = os.path.join(MODS_VERSION_DIRPATH, "..", "configs", "tessu_mod")
TS_PLUGIN_INSTALLER_PATH = os.path.join(MODS_VERSION_DIRPATH, "tessumod.ts3_plugin")

class TestCaseBase(unittest.TestCase):

	def setUp(self):
		self.tessu_mod = None
		self.ts_client_query_server = None
		self.__ts_plugin_info = None
		self.event_loop = EventLoop()
		self.__verifiers = []
		self.__max_end_time = None
		self.__min_end_time = None

		shutil.rmtree(TMP_DIRPATH, ignore_errors=True)

		if FAKES_DIRPATH not in sys.path:
			sys.path.append(FAKES_DIRPATH)
		if MOD_SCRIPTS_DIRPATH not in sys.path:
			sys.path.append(MOD_SCRIPTS_DIRPATH)

		os.makedirs(MODS_VERSION_DIRPATH)

		shutil.copytree(os.path.join(MOD_SRC_DIRPATH, "gui"), os.path.join(MODS_VERSION_DIRPATH, "gui"))

		import ResMgr
		ResMgr.RES_MODS_VERSION_PATH = MODS_VERSION_DIRPATH

		mod_settings.INI_DIRPATH = INI_DIRPATH
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
		# create empty ts plugin installer file
		open(TS_PLUGIN_INSTALLER_PATH, "w").close()

	def tearDown(self):
		if self.__ts_plugin_info:
			self.__ts_plugin_info.close()
		if self.ts_client_query_server:
			self.ts_client_query_server.stop()
		sys.path.remove(FAKES_DIRPATH)
		sys.path.remove(MOD_SCRIPTS_DIRPATH)

	def start_ts_client(self, **state):
		assert self.ts_client_query_server == None, "Cannot start TS client if it is already running"
		self.ts_client_query_server = TSClientQueryService()
		self.ts_client_query_server.start()
		self.change_ts_client_state(**state)

	def enable_ts_client_tessumod_plugin(self, version=0):
		self.__ts_plugin_info = mmap.mmap(0, 1, "TessuModTSPluginInfo", mmap.ACCESS_WRITE)
		self.__ts_plugin_info.write(struct.pack("=B", version))

	def get_shared_memory_contents(self, memory):
		assert memory == "TessuModTSPlugin3dAudio" # currently this is only memory supported
		shmem = mmap.mmap(0, 1024, memory, mmap.ACCESS_READ)
		(
			timestamp,
			camera_pos_x,
			camera_pos_y,
			camera_pos_z,
			camera_dir_x,
			camera_dir_y,
			camera_dir_z,
			client_count
		) = struct.unpack("=I3f3fB", shmem.read(4+3*4+3*4+1))
		clients = {}
		for client_index in range(0, client_count):
			client_id, x, y, z = struct.unpack("=h3f", shmem.read(2+3*4))
			clients[self.ts_client_query_server.get_user(clid=client_id).name] = {
				"position": (x, y, z)
			}

		return {
			"timestamp": timestamp,
			"camera": {
				"position": (camera_pos_x, camera_pos_y, camera_pos_z),
				"direction": (camera_dir_x, camera_dir_y, camera_dir_z)
			},
			"clients": clients
		}

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

	def run_in_event_loop(self, timeout=20):
		self.event_loop.call(self.__on_loop, repeat=True, timeout=0.05)
		self.event_loop.call(self.__check_verify, repeat=True, timeout=1)
		self.__max_end_time = time.time() + timeout
		if self.__min_end_time is None:
			self.__min_end_time = time.time()
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
					if vehicle_id not in BigWorld.entities:
						BigWorld.entities[vehicle_id] = BigWorld.Entity()
					if "position" in player:
						BigWorld.player().arena.positions[vehicle_id] = player["position"]
						BigWorld.entities[vehicle_id].position = BigWorld.Vector(*player["position"])
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

	def change_mod_state_variables(self, **variables):
		states_dirpath = os.path.join(INI_DIRPATH, "states")
		if not os.path.exists(states_dirpath):
			os.makedirs(states_dirpath)
		for key, value in variables.iteritems():
			with open(os.path.join(states_dirpath, key), "w") as file:
				file.write(json.dumps(value))

	def get_mod_state_variable(self, key):
		states_dirpath = os.path.join(INI_DIRPATH, "states")
		key_path = os.path.join(states_dirpath, key)
		if os.path.exists(key_path):
			with open(key_path, "r") as file:
				return file.read()

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

	def assert_finally_equal(self, a, b):
		actual_getter = a if callable(a) else b
		expected = b if callable(a) else a
		self.__verifiers.append(lambda: actual_getter() == expected)

	def assert_finally_true(self, x):
		self.__verifiers.append(x)

	def assert_finally_false(self, x):
		self.__verifiers.append(lambda: not x())

	def wait_at_least(self, secs):
		self.__min_end_time = time.time() + secs
