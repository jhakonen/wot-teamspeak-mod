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

from gui.mods.tessumod import plugintypes, logutils
from gui.mods.tessumod.infrastructure.gameapi import Environment
from gui.mods.tessumod.models import g_player_model, g_user_model, g_pairing_model, PlayerItem, UserItem, Priority

from BattleReplay import BattleReplay

import os
import json
import uuid
import itertools

logger = logutils.logger.getChild("usercache")

class UserCachePlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin,
	plugintypes.SettingsUIProvider, plugintypes.SnapshotProvider):
	"""
	This plugin ...
	"""

	NS = "cache"

	def __init__(self):
		super(UserCachePlugin, self).__init__()
		g_player_model.add_namespace(self.NS, Priority.LOW)
		g_user_model.add_namespace(self.NS, Priority.LOW)
		self.__enabled_in_replays = False
		self.__in_replay = False
		self.__read_error = False
		self.__config_dirpath = os.path.join(Environment.find_res_mods_version_path(), "..", "configs", "tessumod")
		self.__cache_filepath = os.path.join(self.__config_dirpath, "usercache.json")
		self.__snapshots = {}
		BattleReplay.play = self.__hook_battlereplay_play(BattleReplay.play)

	@logutils.trace_call(logger)
	def initialize(self):
		g_pairing_model.on("added", self.__on_pairings_changed)
		g_pairing_model.on("modified", self.__on_pairings_changed)
		g_pairing_model.on("removed", self.__on_pairings_changed)
		# create cache directory if it doesn't exist yet
		if not os.path.isdir(self.__config_dirpath):
			os.makedirs(self.__config_dirpath)
		# read cache file if it exists
		if self.__has_cache_file():
			self.__import_cache_structure(self.__load_cache_file())

	@logutils.trace_call(logger)
	def deinitialize(self):
		# write to cache file
		self.__save_cache_file(self.__export_cache_structure())

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "General":
			if name == "update_cache_in_replays":
				self.__enabled_in_replays = value

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsMixin.
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
			del self.__snapshots[snapshot_name]

	def __hook_battlereplay_play(self, orig_method):
		def wrapper(battlereplay_self, fileName=None):
			self.on_battle_replay()
			return orig_method(battlereplay_self, fileName)
		return wrapper

	@logutils.trace_call(logger)
	def on_battle_replay(self):
		self.__in_replay = True

	def __on_pairings_changed(self, *args, **kwargs):
		for pairing in g_pairing_model.itervalues():
			self.__cache_user_id(pairing.id)
			for player_id in pairing.player_ids:
				self.__cache_player_id(player_id)

	def __cache_user_id(self, user_id):
		if user_id in g_user_model:
			g_user_model.set(self.NS, UserItem(
				id = user_id,
				names = g_user_model[user_id].names[:1]
			))

	def __cache_player_id(self, player_id):
		if player_id in g_player_model:
			g_player_model.set(self.NS, PlayerItem(
				id = player_id,
				name = g_player_model[player_id].name
			))

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
		users = [UserItem(id=pairing[0]["id"], names=[pairing[0]["name"]]) for pairing in cache_structure["pairings"]]
		g_user_model.set_all(self.NS, users)
		players = [PlayerItem(id=int(pairing[1]["id"]), name=pairing[1]["name"]) for pairing in cache_structure["pairings"]]
		g_player_model.set_all(self.NS, players)
		pairings = [(pairing[0]["id"], int(pairing[1]["id"])) for pairing in cache_structure["pairings"]]
		for plugin_info in self.plugin_manager.getPluginsOfCategory("UserCache"):
			plugin_info.plugin_object.reset_pairings(pairings)

	def __export_cache_structure(self):
		return {
			"version": 1,
			"pairings": list(itertools.chain(reduce(self.__reduce_pairing, g_pairing_model.itervalues(), [])))
		}

	def __reduce_pairing(self, pairings, pairing):
		result = []
		user_name = list(g_user_model.get(pairing.id, {}).get("names", [None]))[0]
		for player_id in pairing.player_ids:
			player_name = g_player_model.get(player_id, {}).get("name", None)
			result.append(({
				"id": pairing.id,
				"name": user_name
			}, {
				"id": player_id,
				"name": player_name
			}))
		return pairings + result
