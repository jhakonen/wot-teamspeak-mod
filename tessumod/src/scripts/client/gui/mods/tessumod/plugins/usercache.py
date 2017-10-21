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

from gui.mods.tessumod import database, constants
from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.messages import PairingMessage
from gui.mods.tessumod.plugintypes import (Plugin, SettingsProvider, SettingsUIProvider,
										   SnapshotProvider)

import pydash as _

import itertools
import json
import os
import uuid
from copy import copy
from StringIO import StringIO

logger = logutils.logger.getChild("usercache")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return UserCachePlugin()

class UserCachePlugin(Plugin, SettingsProvider, SettingsUIProvider, SnapshotProvider):
	"""
	This plugin ...
	"""

	NS = "cache"

	def __init__(self):
		super(UserCachePlugin, self).__init__()
		self.__enabled_in_replays = False
		self.__in_replay = False
		self.__read_error = False
		self.__config_dirpath = os.path.join("./mods/configs/tessumod")
		self.__cache_files = {
			"users_file":    os.path.join(self.__config_dirpath, constants.USERS_CACHE_FILE),
			"players_file":  os.path.join(self.__config_dirpath, constants.PLAYERS_CACHE_FILE),
			"pairings_file": os.path.join(self.__config_dirpath, constants.PAIRINGS_CACHE_FILE)
		}
		self.__snapshots = {}

	@logutils.trace_call(logger)
	def initialize(self):
		gameapi.events.on("battle_replay_started", self.__on_battle_replay_started)
		# create cache directory if it doesn't exist yet
		if not os.path.isdir(self.__config_dirpath):
			os.makedirs(self.__config_dirpath)
		self.__import_cache_files(**self.__cache_files)

	@logutils.trace_call(logger)
	def deinitialize(self):
		gameapi.events.off("battle_replay_started", self.__on_battle_replay_started)
		# write to cache file
		self.__export_cache_files(**self.__cache_files)

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
		self.__snapshots[snapshot_name] = {
			"users_file":    StringIO(),
			"players_file":  StringIO(),
			"pairings_file": StringIO()
		}
		self.__export_cache_files(**self.__snapshots[snapshot_name])
		map(lambda file: file.seek(0), self.__snapshots[snapshot_name].itervalues())
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
			self.__import_cache_files(**self.__snapshots[snapshot_name])

	@logutils.trace_call(logger)
	def __on_battle_replay_started(self):
		self.__in_replay = True

	def __import_cache_files(self, users_file, players_file, pairings_file):
		try:
			database.import_caches(users_file, players_file, pairings_file)
		except:
			self.__read_error = True
			raise

	def __export_cache_files(self, users_file, players_file, pairings_file):
		if self.__read_error:
			return
		if self.__in_replay and self.__enabled_in_replays:
			return
		database.export_caches(users_file, players_file, pairings_file)
