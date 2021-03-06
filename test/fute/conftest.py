import asyncio
import json
import os
import random
import shutil
import struct
from unittest import mock

from aiohttp import web
from pydash import _
import pytest

import Account
import Avatar
import BigWorld
import fakes
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from helpers import dependency
from messenger.proto.events import g_messengerEvents
from notification import NotificationMVC
import ResMgr
from skeletons.gui.battle_session import IBattleSessionProvider
from skeletons.gui.system_messages import ISystemMessages
from VOIP.VOIPManager import getVOIPManager

import mod_tessumod
import tessumod.utils

from .test_helpers import constants, mod_settings
from .test_helpers.cq_tsplugin_fake import TSClientQueryService, TSClientQueryDataModel
from .test_helpers.tools import *

TMP_DIRPATH          = os.path.join(os.getcwd(), "tmp")
MODS_VERSION_DIRPATH = os.path.join(TMP_DIRPATH, "mods", "version")
REPO_ROOT_DIRPATH    = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
RESOURCE_DIRPATH     = os.path.join(REPO_ROOT_DIRPATH, "data")
TESSUMOD_DIRPATH     = os.path.join(MODS_VERSION_DIRPATH, "tessumod")
INI_DIRPATH          = os.path.join(MODS_VERSION_DIRPATH, "..", "configs", "tessu_mod")


@pytest.fixture(autouse=True)
async def game():
	obj = GameFixture()
	yield obj
	await obj.quit()

class GameFixture:

	def __init__(self):
		self._running = False
		self._tick_task = None
		self._mods = []
		self._voip_player_speaking_state = {}
		self._state = None

	def start(self, **state):
		assert not self._running, "Game has already been started"
		self._system_messages = dependency.instance(ISystemMessages)
		self._system_messages.pushMessage = mock.Mock()
		self._original_wg_openWebBrowser = BigWorld.wg_openWebBrowser
		self._add_notification_mock = mock.Mock()
		self._running = True
		self._tick_task = asyncio.get_event_loop().create_task(self._tick())

		ResMgr.RES_MODS_VERSION_PATH = MODS_VERSION_DIRPATH.replace("mods", "res_mods")
		BigWorld.wg_openWebBrowser = mock.Mock()
		NotificationMVC.g_instance.getModel().on_addNotification += self._add_notification_mock

		session_provider = dependency.instance(IBattleSessionProvider)
		session_provider.shared.feedback.onMinimapFeedbackReceived = mock.Mock()
		g_messengerEvents.voip.onPlayerSpeaking += self._on_voip_player_speaking

		[mod.load() for mod in self._mods]

		self.change_state(**state)

	async def quit(self):
		if self._running:
			BigWorld.fake_clear_player()
			self._running = False
			if self._tick_task:
				await self._tick_task
			fakes.reset()
			BigWorld.wg_openWebBrowser = self._original_wg_openWebBrowser
			NotificationMVC.g_instance.cleanUp()

	def add_mod(self, mod):
		self._mods.append(mod)

	def change_state(self, **state):
		if "mode" in state:
			if state["mode"] == "battle":
				BigWorld.player(Avatar.Avatar(state["player_name"] if "player_name" in state else "not set"))
			elif state["mode"] == "lobby":
				BigWorld.player(Account.PlayerAccount())
				assert "player_name" not in state, "Setting player name not implemented for lobby"
			else:
				assert False, "Unknown state"
			self._state = state["mode"]
		if self._state == "battle":
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
		elif self._state == "lobby":
			if "players" in state:
				for id, player in enumerate(state["players"]):
					BigWorld.player().prebattle.rosters[0][id] = {
						"name": player["name"],
						"dbID": random.randint(0, 1000000)
					}
		else:
			assert False, "State not defined"

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

	def is_complex_notification_sent(self, messages):
		return mock_was_called_with(self._add_notification_mock, message_decorator_matches_fragments(messages))

	def get_latest_complex_notification(self):
		return self._add_notification_mock.call_args[0][0]

	async def wait_until_url_opened_to_web_browser(self, url):
		await wait_until_true(lambda: mock_was_called_with(BigWorld.wg_openWebBrowser, url))

	def send_notification_action(self, msg, action):
		NotificationMVC.g_instance.handleAction(typeID=msg.getType(), entityID=msg.getID(), action=action)

	def get_player_id(self, name):
		assert hasattr(BigWorld.player(), "arena"), "Getting player id in lobby not implemented"
		for vehicle in BigWorld.player().arena.vehicles.values():
			if vehicle["name"] == name:
				return vehicle["accountDBID"]

	def get_vehicle_id(self, name):
		assert hasattr(BigWorld.player(), "arena"), "Getting vehicle id outside of battle makes no sense"
		for vehicle_id, vehicle in BigWorld.player().arena.vehicles.items():
			if vehicle["name"] == name:
				return vehicle_id

	def is_player_speaking(self, player_id):
		received = self._voip_player_speaking_state.get(player_id, None)
		queried = getVOIPManager().isParticipantTalking(player_id)
		if received != queried:
			return None
		return received

	def set_game_voice_chat_speaking(self, player_id, speaking):
		getVOIPManager().fake_talkers[player_id] = speaking
		g_messengerEvents.voip.onPlayerSpeaking(player_id, speaking)

	def has_minimap_feedback(self, vehicle_id, action):
		session_provider = dependency.instance(IBattleSessionProvider)
		return mock_was_called_with(
			session_provider.shared.feedback.onMinimapFeedbackReceived,
			FEEDBACK_EVENT_ID.MINIMAP_SHOW_MARKER,
			vehicle_id,
			action
		)

	def _on_voip_player_speaking(self, player_id, speaking):
		self._voip_player_speaking_state[player_id] = speaking

	async def _tick(self):
		while self._running:
			BigWorld.tick()
			await asyncio.sleep(0.001)


@pytest.fixture(name="tessumod", autouse=True)
async def tessumod_fixture(game):
	shutil.rmtree(TMP_DIRPATH, ignore_errors=True)
	os.makedirs(TESSUMOD_DIRPATH)
	tessumod.utils.get_ini_dir_path = lambda: INI_DIRPATH
	tessumod.utils.get_resource_data_path = lambda: RESOURCE_DIRPATH
	mod_settings.INI_DIRPATH = INI_DIRPATH
	mod_settings.reset_cache_file()
	mod_settings.reset_settings_file()
	# hack to speed up testing
	tessumod.ts3._UNREGISTER_WAIT_TIMEOUT = 0.05
	obj = TessuModFixture()
	game.add_mod(obj)
	yield obj
	obj.unload()

class TessuModFixture:

	def __init__(self):
		self.mod_tessumod = None
		self._events = []
		self._ts_speak_state = {}

	def load(self):
		assert not self.mod_tessumod, "The mod has already been loaded"
		self.mod_tessumod = mod_tessumod
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

		del self._events[:]

		self.mod_tessumod.on_player_speaking += self._on_player_speaking_in_ts
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

	def change_state_variables(self, **variables):
		states_dirpath = os.path.join(INI_DIRPATH, "states")
		if not os.path.exists(states_dirpath):
			os.makedirs(states_dirpath)
		for key, value in variables.items():
			with open(os.path.join(states_dirpath, key), "w") as file:
				file.write(json.dumps(value))

	def get_state_variable(self, key):
		states_dirpath = os.path.join(INI_DIRPATH, "states")
		key_path = os.path.join(states_dirpath, key)
		if os.path.exists(key_path):
			with open(key_path, "r") as file:
				return json.load(file)

	async def wait_until_connected_to_ts_client(self, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_true(lambda: "on_connected_to_ts_client" in self._events, timeout)

	async def wait_until_disconnected_from_ts_client(self, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_true(lambda: "on_disconnected_from_ts_client" in self._events, timeout)

	async def wait_until_connected_to_ts_server(self, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_true(lambda: "on_connected_to_ts_server" in self._events, timeout)

	async def wait_player_speaking_in_ts(self, id, speaking, timeout=5):
		assert self.mod_tessumod, "Mod has not been loaded, please start the game first!"
		await wait_until_equal(lambda: self._ts_speak_state.get(id, None), speaking, timeout)

	def _on_player_speaking_in_ts(self, id, speaking):
		self._ts_speak_state[id] = speaking

@pytest.fixture()
async def cq_tsplugin(autouse=True):
	obj = CQTSPluginFixture()
	yield obj
	await obj.unload()

class CQTSPluginFixture:

	def __init__(self):
		self._service = None

	async def load(self, **state):
		assert self._service == None, "Client query plugin is already loaded"
		self._model = TSClientQueryDataModel()
		self._service = TSClientQueryService(self._model)
		await self._service.start()
		self.change_state(**state)

	def change_state(self, **state):
		assert self._service, "Client query plugin must be already loaded to change its state"
		if "connected_to_server" in state:
			self._model.set_connected_to_server(state["connected_to_server"])
		if "users" in state:
			for name, data in state["users"].items():
				self._model.set_user(name, **data)

	async def unload(self):
		if self._service:
			await self._service.stop()
			self._service = None

	def get_user(self, **kwargs):
		assert self._service, "Client query plugin must be loaded first"
		return self._model.get_user(**kwargs)

	async def wait_until_user_metadata_equals(self, name, metadata, timeout=5):
		await wait_until_equal(lambda: self.get_user_metadata(name), metadata, timeout)

	def get_user_metadata(self, name):
		return getattr(self.get_user(name=name), 'metadata', None)

	def set_user_metadata(self, name, metadata):
		# TODO: Remove as change_state() can do this already
		self.get_user(name=name).metadata = metadata

@pytest.fixture(autouse=True)
async def my_tsplugin(cq_tsplugin):
	obj = MyTSPluginFixture(cq_tsplugin)
	yield obj
	obj.unload()

class MyTSPluginFixture:

	def __init__(self, cq_tsplugin):
		self._loaded = False
		self._cq_tsplugin = cq_tsplugin

	def load(self, version=1):
		assert not self._loaded, "My plugin is already loaded"
		self._info = create_mmap_fake("TessuModTSPluginInfo", 1)
		self._info.write(struct.pack("=B", version))
		self._loaded = True

	def unload(self):
		if self._loaded:
			cleanup_mmap_fake("TessuModTSPluginInfo")
			cleanup_mmap_fake("TessuModTSPlugin3dAudio")
			self._loaded = False

	async def wait_until_received_data_match(self, obj_path, expected, timeout=5):
		assert self._loaded, "My plugin has not been loaded"
		await wait_until_equal(lambda: _.get(self.get_received_data(), obj_path), expected, timeout)

	def get_received_data(self):
		shmem = create_mmap_fake("TessuModTSPlugin3dAudio", 1024)
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
			clients[self._cq_tsplugin.get_user(clid=client_id).name] = {
				"position": (x, y, z)
			}
		result = {
			"timestamp": timestamp,
			"camera": {
				"position": (camera_pos_x, camera_pos_y, camera_pos_z),
				"direction": (camera_dir_x, camera_dir_y, camera_dir_z)
			},
			"clients": clients
		}
		return result


@pytest.fixture(autouse=True)
async def httpserver():
	obj = HTTPServerFixture()
	await obj.start()
	yield obj
	await obj.stop()

class HTTPServerFixture:

	def __init__(self):
		self._plugin_info_data = constants.PLUGIN_INFO
		self._app = web.Application()
		self._app.add_routes([web.get("/", self._plugin_info_handler)])
		self._runner = web.AppRunner(self._app)

	async def start(self):
		await self._runner.setup()
		site = web.TCPSite(self._runner, "127.0.0.1", 0)
		await site.start()
		mod_tessumod.PLUGIN_INFO_URL = "http://%s:%d/" % self._runner.addresses[0]

	async def stop(self):
		await self._runner.cleanup()

	def set_plugin_info(self, obj):
		self._plugin_info_data = obj

	def _plugin_info_handler(self, request):
		return web.Response(text=json.dumps(self._plugin_info_data))


def create_mmap_fake(name, length):
	file_path = os.path.join("/tmp", name)
	if not os.path.exists(file_path):
		with open(file_path, "wb") as file:
			file.write(b"\x00" * length)
	obj = open(file_path, "r+b", 0)
	return obj

def cleanup_mmap_fake(name):
	path = os.path.join("/tmp", name)
	if os.path.exists(path):
		os.remove(path)
