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

from gui.mods.tessumod.items import get_items, match_id, match_unique_id
from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.lib import pydash as _
from gui.mods.tessumod.messages import PairingMessage
from gui.mods.tessumod.plugintypes import (Plugin, SettingsProvider, SettingsUIProvider,
	SnapshotProvider, EntityProvider)

import itertools
import json
import os
import uuid
from copy import copy

logger = logutils.logger.getChild("usercache")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return UserCachePlugin()

class UserCachePlugin(Plugin, SettingsProvider, SettingsUIProvider, SnapshotProvider, EntityProvider):
	"""
	This plugin ...
	"""

	NS = "cache"

	def __init__(self):
		super(UserCachePlugin, self).__init__()
		self.__enabled_in_replays = False
		self.__in_replay = False
		self.__read_error = False
		self.__config_dirpath = os.path.join(gameapi.find_res_mods_version_path(), "..", "configs", "tessumod")
		self.__cache_filepath = os.path.join(self.__config_dirpath, "usercache.json")
		self.__snapshots = {}
		self.__cached_players = {}
		self.__cached_users = {}

	@logutils.trace_call(logger)
	def initialize(self):
		gameapi.events.on("battle_replay_started", self.__on_battle_replay_started)
		self.messages.subscribe(PairingMessage, self.__on_pairing_event)
		# create cache directory if it doesn't exist yet
		if not os.path.isdir(self.__config_dirpath):
			os.makedirs(self.__config_dirpath)
		# read cache file if it exists
		if self.__has_cache_file():
			self.__import_cache_structure(self.__load_cache_file())

	@logutils.trace_call(logger)
	def deinitialize(self):
		gameapi.events.off("battle_replay_started", self.__on_battle_replay_started)
		self.messages.unsubscribe(PairingMessage, self.__on_pairing_event)
		# write to cache file
		self.__save_cache_file(self.__export_cache_structure())

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "General":
			if name == "update_cache_in_replays":
				self.__enabled_in_replays = value

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"General": {
				"help": "",
				"variables": [
					{
						"name": "update_cache_in_replays",
						"default": False,
						"help": """
							When turned on enables updating of tessu_mod_cache.ini when playing replays.
							Note that when playing someone else's replay your TS user will get paired
							with the replay's player name if this option is turned on.
							Useful for debugging purposes.
							Changing this value requires game restart.
						"""
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def get_settingsui_content(self):
		"""
		Implemented from SettingsUIProvider.
		"""
		return {
			"General Settings": [
				{
					"label": "Save paired users in replay",
					"help": """
						When turned on enables updating of tessu_mod_cache.ini when playing replays.
						Note that when playing someone else's replay your TS user will get paired
						with the replay's player name if this option is turned on.
						Useful for debugging purposes.
						Changing this value requires game restart.
					""",
					"type": "checkbox",
					"variable": ("General", "update_cache_in_replays")
				}
			]
		}

	@logutils.trace_call(logger)
	def create_snapshot(self):
		"""
		Implemented from SnapshotProvider.
		"""
		snapshot_name = uuid.uuid4()
		self.__snapshots[snapshot_name] = self.__export_cache_structure()
		return snapshot_name

	@logutils.trace_call(logger)
	def release_snaphot(self, snapshot_name):
		"""
		Implemented from SnapshotProvider.
		"""
		if snapshot_name in self.__snapshots:
			del self.__snapshots[snapshot_name]

	@logutils.trace_call(logger)
	def restore_snapshot(self, snapshot_name):
		"""
		Implemented from SnapshotProvider.
		"""
		if snapshot_name in self.__snapshots:
			self.__import_cache_structure(self.__snapshots[snapshot_name])

	def has_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		return name in ["cached-users", "cached-players"]

	def get_entity_source(self, name):
		"""
		Implemented from EntityProvider.
		"""
		if name == "cached-users":
			return self.__cached_users.values()
		if name == "cached-players":
			return self.__cached_players.values()

	@logutils.trace_call(logger)
	def __on_battle_replay_started(self):
		self.__in_replay = True

	def __on_pairing_event(self, action, data):
		if action == "added":
			user = _.find(self.__get_live_users(), match_unique_id(data["user-unique-id"]))
			if user:
				self.__cached_users[user["unique-id"]] = copy(user)
			player = _.find(self.__get_live_players(), match_id(data["player-id"]))
			if player:
				self.__cached_players[player["id"]] = copy(player)
		elif action == "removed":
			raise RuntimeError("Not implemented")

	def __get_pairings(self):
		return get_items(self.plugin_manager, ["pairings"], ["player-id", "user-unique-id"])

	def __get_live_users(self):
		return get_items(self.plugin_manager, ["users"], ["id"])

	def __get_all_users(self):
		return get_items(self.plugin_manager, ["users", "cached-users"], ["unique-id"])

	def __get_live_players(self):
		return get_items(self.plugin_manager, ["battle-players", "prebattle-players", "me-player"], ["id"])

	def __get_all_players(self):
		return get_items(self.plugin_manager, ["battle-players", "prebattle-players", "me-player", "cached-players"], ["id"])

	def __has_cache_file(self):
		return os.path.isfile(self.__cache_filepath)

	def __load_cache_file(self):
		"""
		Reads cache file if it exists, returns loaded contents as object.
		"""
		try:
			with open(self.__cache_filepath, "rb") as file:
				return json.loads(file.read())
		except:
			self.__read_error = True
			raise

	def __save_cache_file(self, contents_obj):
		"""
		Writes current cache configuration to a file. Returns True on success, False on failure.
		"""
		if not self.__read_error and (not self.__in_replay or self.__enabled_in_replays):
			with open(self.__cache_filepath, "wb") as file:
				file.write(json.dumps(contents_obj, indent=4))
				return True
		return False

	def __import_cache_structure(self, cache_structure):
		assert cache_structure, "Cache content invalid"
		assert cache_structure.get("version") == 1, "Cache contents version mismatch"
		cached_users = {}
		cached_players = {}
		cached_pairings = []
		for pairing in cache_structure["pairings"]:
			cached_users[pairing[0]["id"]] = {"unique-id": pairing[0]["id"], "name": pairing[0]["name"]}
			cached_players[pairing[1]["id"]] = {"id": int(pairing[1]["id"]), "name": pairing[1]["name"]}
			cached_pairings.append({"user-unique-id": pairing[0]["id"], "player-id": int(pairing[1]["id"])})
		self.__cached_users = cached_users
		self.__cached_players = cached_players
		for plugin_info in self.plugin_manager.getPluginsOfCategory("UserCache"):
			plugin_info.plugin_object.reset_pairings(cached_pairings)

	def __export_cache_structure(self):
		users = self.__get_all_users()
		players = self.__get_all_players()
		pairings = self.__get_pairings()
		pairing_results = []

		for pairing in pairings.itervalues():
			user_id = pairing["user-unique-id"]
			user_name = _.find(users, match_unique_id(user_id))["name"]
			player_id = pairing["player-id"]
			player_name = players[player_id]["name"]
			pairing_results.append(({
				"id": user_id,
				"name": user_name
			}, {
				"id": player_id,
				"name": player_name
			}))

		return {
			"version": 1,
			"pairings": pairing_results
		}
