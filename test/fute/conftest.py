import asyncio
import asyncore
import json
import os
import random
import shutil
from unittest import mock

import pytest

import Account
import Avatar
import BigWorld
import fakes
from helpers import dependency
from notification import NotificationMVC
import ResMgr
from skeletons.gui.system_messages import ISystemMessages

import mod_tessumod
import tessumod.utils

from .test_helpers import constants, mod_settings
from .test_helpers.http_server import HTTPServer
from .test_helpers.ts_client_query import TSClientQueryService
from .test_helpers.v2_tools import mock_was_called_with, wait_until_true

TMP_DIRPATH          = os.path.join(os.getcwd(), "tmp")
MODS_VERSION_DIRPATH = os.path.join(TMP_DIRPATH, "mods", "version")
REPO_ROOT_DIRPATH    = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
RESOURCE_DIRPATH     = os.path.join(REPO_ROOT_DIRPATH, "data")
TESSUMOD_DIRPATH     = os.path.join(MODS_VERSION_DIRPATH, "tessumod")
INI_DIRPATH          = os.path.join(MODS_VERSION_DIRPATH, "..", "configs", "tessu_mod")


@pytest.fixture()
async def game():
	obj = GameFixture()
	shutil.rmtree(TMP_DIRPATH, ignore_errors=True)
	os.makedirs(TMP_DIRPATH)
	ResMgr.RES_MODS_VERSION_PATH = MODS_VERSION_DIRPATH.replace("mods", "res_mods")
	yield obj
	await obj.quit()

class GameFixture:

	def __init__(self):
		self._running = False
		self._tick_task = None
		self._mods = []

	def start(self, **state):
		assert not self._running, "Game has already been started"
		self._system_messages = dependency.instance(ISystemMessages)
		self._system_messages.pushMessage = mock.Mock()
		self._running = True
		self._tick_task = asyncio.get_event_loop().create_task(self._tick())
		[mod.load() for mod in self._mods]
		self.change_state(**state)

	async def quit(self):
		if self._running:
			self._running = False
			if self._tick_task:
				await self._tick_task
			BigWorld.fake_clear_player()
			NotificationMVC.g_instance.cleanUp()

	def add_mod(self, mod):
		self._mods.append(mod)

	def change_state(self, **state):
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
			if "camera" in state:
				if "position" in state["camera"]:
					BigWorld.camera().position = BigWorld.Vector(*state["camera"]["position"])
				if "direction" in state["camera"]:
					BigWorld.camera().direction = BigWorld.Vector(*state["camera"]["direction"])
		elif state["mode"] == "lobby":
			BigWorld.player(Account.PlayerAccount())
			if "players" in state:
				for id, player in enumerate(state["players"]):
					BigWorld.player().prebattle.rosters[0][id] = {
						"name": player["name"],
						"dbID": random.randint(0, 1000000)
					}

	async def wait_until_system_notification_sent(self, message, type):
		await wait_until_true(lambda: self.is_system_notification_sent(message, type))

	def is_system_notification_sent(self, message, type):
		import gui.SystemMessages
		if type == "info":
			sm_type = gui.SystemMessages.SM_TYPE.Information
		if type == "warning":
			sm_type = gui.SystemMessages.SM_TYPE.Warning
		if type == "error":
			sm_type = gui.SystemMessages.SM_TYPE.Error
		return mock_was_called_with(self._system_messages.pushMessage, message, sm_type)

	async def _tick(self):
		while self._running:
			BigWorld.tick()
			await asyncio.sleep(0.001)


@pytest.fixture(name="tessumod")
async def tessumod_fixture(game):
	obj = TessuModFixture()
	game.add_mod(obj)
	yield obj
	obj.unload()

class TessuModFixture:

	def __init__(self):
		self.mod_tessumod = None
		self._events = []

	def load(self):
		assert not self.mod_tessumod, "The mod has already been loaded"
		self.mod_tessumod = mod_tessumod
		tessumod.utils.get_ini_dir_path = lambda: INI_DIRPATH
		tessumod.utils.get_resource_data_path = lambda: RESOURCE_DIRPATH
		shutil.rmtree(TMP_DIRPATH, ignore_errors=True)
		os.makedirs(TESSUMOD_DIRPATH)
		mod_settings.INI_DIRPATH = INI_DIRPATH
		mod_settings.reset_cache_file()
		mod_settings.reset_settings_file()
		self.change_settings(
			General = {
				"log_level": os.environ.get("LOG_LEVEL", "1"),
				"speak_stop_delay": "0" # makes tests execute faster
			},
			TSClientQueryService = {
				"polling_interval": "0" # makes tests execute faster
			}
		)
		self.mod_tessumod.init()
		# hack to speed up testing
		tessumod.ts3._UNREGISTER_WAIT_TIMEOUT = 0.05

		del self._events[:]

		self.mod_tessumod.g_ts.on_connected_to_server += lambda *args, **kwargs: self._events.append("on_connected_to_ts_server")
		self.mod_tessumod.g_ts.on_connected += lambda: self._events.append("on_connected_to_ts_client")
		self.mod_tessumod.g_ts.on_disconnected += lambda: self._events.append("on_disconnected_from_ts_client")

	def unload(self):
		if self.mod_tessumod:
			self.mod_tessumod.fini()

	def change_settings(self, **groups):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		for group_name, variables in groups.items():
			for var_name, var_value in variables.items():
				mod_settings.set_setting(group_name, var_name, var_value)
		# File change detection seems to be pretty unreliable, often not
		# working at all, so command the mod to load the file by force
		if self.mod_tessumod.g_settings:
			self.mod_tessumod.g_settings.sync(force=True)

	def change_user_cache(self, **groups):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		for group_name, variables in groups.items():
			for var_name, var_value in variables.items():
				mod_settings.set_cache_entry(group_name, var_name, var_value)
		# File change detection seems to be pretty unreliable, often not
		# working at all, so command the mod to load the file by force
		if self.mod_tessumod.g_user_cache:
			self.mod_tessumod.g_user_cache.sync(force=True)

	async def wait_until_connected_to_ts_client(self, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_true(lambda: "on_connected_to_ts_client" in self._events, timeout)

	async def wait_until_disconnected_from_ts_client(self, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_true(lambda: "on_disconnected_from_ts_client" in self._events, timeout)


@pytest.fixture()
async def tsclient():
	obj = TSClientFixture()
	yield obj
	await obj.quit()

class TSClientFixture:

	def __init__(self):
		self._service = None
		self._sock_map = {}
		self._check_task = None

	def start(self, **state):
		assert self._service == None, "Cannot start TS client if it is already running"
		self._service = TSClientQueryService(self._sock_map)
		self._service.start()
		self.change_state(**state)
		self._check_task = asyncio.get_event_loop().create_task(self._service_check())

	def change_state(self, **state):
		assert self._service, "TS client must be running to change its state"
		if "connected_to_server" in state:
			self._service.set_connected_to_server(state["connected_to_server"])
		if "users" in state:
			for name, data in state["users"].items():
				self._service.set_user(name, **data)

	async def quit(self):
		if self._service:
			self._service.stop()
			self._service = None
		if self._check_task:
			await self._check_task

	async def _service_check(self):
		while self._service:
			asyncore.loop(0, map=self._sock_map, count=1)
			self._service.check()
			await asyncio.sleep(0.001)


@pytest.fixture()
async def httpserver():
	obj = HTTPServerFixture()
	obj.start()
	yield obj
	await obj.stop()
	fakes.reset()

class HTTPServerFixture:

	def __init__(self):
		self._service = None
		self._sock_map = {}
		self._check_task = None

	def start(self):
		assert self._service == None, "Cannot start HTTP server if it is already running"
		self._service = HTTPServer(self._sock_map)
		self.set_plugin_info(constants.PLUGIN_INFO)
		self._check_task = asyncio.get_event_loop().create_task(self._service_check())
		mod_tessumod.PLUGIN_INFO_URL = self._service.get_url()

	async def stop(self):
		if self._service:
			self._service.close()
			self._service = None
		if self._check_task:
			await self._check_task

	def set_plugin_info(self, obj):
		self._service.set_response(200, "OK", json.dumps(obj))

	async def _service_check(self):
		while self._service:
			asyncore.loop(0, map=self._sock_map, count=1)
			await asyncio.sleep(0.001)
