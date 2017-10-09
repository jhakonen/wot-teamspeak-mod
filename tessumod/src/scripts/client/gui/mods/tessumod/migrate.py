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

from lib import pydash as _
from lib import logutils, gameapi
from lib.littletable.littletable import Table, DataObject

import os
import json
import ConfigParser
import csv
import shutil

logger = logutils.logger.getChild("migrate")
res_mods_dirpath = os.path.normpath(os.path.join(gameapi.find_res_mods_version_path(), ".."))

def migrate():
	source_dirpath = os.path.join(res_mods_dirpath, "configs", "tessu_mod")
	dest_dirpath   = os.path.join(res_mods_dirpath, "configs", "tessumod")
	if not os.path.isdir(dest_dirpath):
		os.makedirs(dest_dirpath)
	# migrate that stuff
	migrate_user_cache_0_6_to_0_7(source_dirpath, dest_dirpath)
	migrate_settings_0_6_to_0_7(source_dirpath, dest_dirpath)
	# get rid of old config dir, if it has no files anymore
	if os.path.isdir(source_dirpath) and not _.flatten_deep([files for root,dirs,files in os.walk(source_dirpath)]):
		shutil.rmtree(source_dirpath)

def migrate_user_cache_0_6_to_0_7(source_dirpath, dest_dirpath):
	"""
	This function migrates tessu_mod_cache.ini to following files:
	 * users_cache.v1.json
	 * players_cache.v1.json
	 * pairings_cache.v1.json
	"""
	source_filepath   = os.path.join(source_dirpath, "tessu_mod_cache.ini")
	users_filepath    = os.path.join(dest_dirpath, "users_cache.v1.json")
	players_filepath  = os.path.join(dest_dirpath, "players_cache.v1.json")
	pairings_filepath = os.path.join(dest_dirpath, "pairings_cache.v1.json")
	backup_filepath   = os.path.join(dest_dirpath, "tessu_mod_cache.ini.old-0.6")

	source_exists = os.path.isfile(source_filepath)
	dest_exists = all(map(os.path.isfile, [users_filepath, players_filepath, pairings_filepath]))

	if source_exists and not dest_exists:
		logger.info("Migrating caches from version 0.6 to 0.7")

		# Schema for new caches
		users = Table()
		users.create_index('unique_id', unique=True)
		players = Table()
		players.create_index('id', unique=True)
		pairings = Table()
		pairings.create_index('player_id')
		pairings.create_index('user_unique_id')

		# Load old 0.6.x cache file
		parser = ConfigParser.ConfigParser()
		with open(source_filepath, "rb") as file:
			parser.readfp(file)

		# Build new cache structures
		users.insert_many(DataObject(unique_id=id, name=name) for name, id in parser.items("TeamSpeakUsers"))
		players.insert_many(DataObject(id=id, name=name) for name, id in parser.items("GamePlayers"))
		for user_name, player_names in parser.items("UserPlayerPairings"):
			userid = _.head(users.where(name=user_name)).unique_id
			for player_name in list(csv.reader([player_names]))[0]:
				playerid = _.head(players.where(name=player_name)).id
				pairings.insert(DataObject(player_id=playerid, user_unique_id=userid))

		# create destination directory if it doesn't exist yet
		if not os.path.isdir(dest_dirpath):
			os.makedirs(dest_dirpath)

		# write out the new cache files
		users.json_export(users_filepath)
		players.json_export(players_filepath)
		pairings.json_export(pairings_filepath)

		# backup and remove old cache file
		backup_filepath = os.path.join(dest_dirpath, os.path.basename(source_filepath)) + ".old-0.6"
		if os.path.isfile(backup_filepath):
			os.remove(backup_filepath)
		os.rename(source_filepath, backup_filepath)

def migrate_settings_0_6_to_0_7(source_dirpath, dest_dirpath):
	"""
	This function migrates following files into settings.v1.json:
	 * tessu_mod.ini
	 * ignored_plugin_version
	"""
	source_settings_path  = os.path.join(source_dirpath, "tessu_mod.ini")
	source_states_dirpath = os.path.join(source_dirpath, "states")
	source_states_path    = os.path.join(source_states_dirpath, "ignored_plugin_version")
	dest_filepath         = os.path.join(dest_dirpath, "settings.v1.json")

	dest_structure = { "version": 1 }
	# If destination already exists, load it so we can override values in it
	# with values from the old settings file
	if os.path.isfile(dest_filepath):
		with open(dest_filepath, "rb") as file:
			dest_structure = json.loads(file.read())

	if os.path.isfile(source_settings_path) and dest_structure["version"] == 1:
		logger.info("Migrating settings from version 0.6 to 0.7")

		parser = ConfigParser.ConfigParser()
		with open(source_settings_path, "rb") as file:
			parser.readfp(file)
		for section in parser.sections():
			for option in parser.options(section):
				if section == "General":
					if option == "speak_stop_delay":
						dest_structure.setdefault("General", {})["speak_stop_delay"] = parser.getint(section, option)
					elif option == "get_wot_nick_from_ts_metadata":
						dest_structure.setdefault("General", {})["get_wot_nick_from_ts_metadata"] = parser.getboolean(section, option)
					elif option == "update_cache_in_replays":
						dest_structure.setdefault("General", {})["update_cache_in_replays"] = parser.getboolean(section, option)
					elif option == "ts_nick_search_enabled":
						dest_structure.setdefault("General", {})["ts_nick_search_enabled"] = parser.getboolean(section, option)
					elif option == "nick_extract_patterns":
						dest_structure.setdefault("General", {})["nick_extract_patterns"] = parser.get(section, option).split(",")
				elif section == "NameMappings":
					dest_structure.setdefault("NameMappings", {})[option] = parser.get(section, option)
				elif section == "TSClientQueryService":
					if option == "api_key":
						dest_structure.setdefault("TSClientQueryService", {})["api_key"] = parser.get(section, option)
					if option == "host":
						dest_structure.setdefault("TSClientQueryService", {})["host"] = parser.get(section, option)
					elif option == "port":
						dest_structure.setdefault("TSClientQueryService", {})["port"] = parser.getint(section, option)
					elif option == "polling_interval":
						dest_structure.setdefault("TSClientQueryService", {})["polling_interval"] = parser.getfloat(section, option)
				elif section == "VoiceChatNotifications":
					if option == "enabled":
						dest_structure.setdefault("VoiceChatNotifications", {})["enabled"] = parser.getboolean(section, option)
					elif option == "self_enabled":
						dest_structure.setdefault("VoiceChatNotifications", {})["self_enabled"] = parser.getboolean(section, option)
				elif section == "MinimapNotifications":
					if option == "enabled":
						dest_structure.setdefault("VoiceChatNotifications", {})["enabled"] = parser.getboolean(section, option)
					elif option == "self_enabled":
						dest_structure.setdefault("VoiceChatNotifications", {})["self_enabled"] = parser.getboolean(section, option)
					elif option == "action":
						dest_structure.setdefault("VoiceChatNotifications", {})["action"] = parser.get(section, option)
					elif option == "repeat_interval":
						dest_structure.setdefault("VoiceChatNotifications", {})["repeat_interval"] = parser.getfloat(section, option)

	if os.path.isfile(source_states_path) and dest_structure["version"] == 1:
		logger.info("Migrating plugin install opt-out from version 0.6 to 0.7")
		dest_structure.setdefault("General", {})["tsplugin_opt_out"] = True

	# create destination directory if it doesn't exist yet
	dest_dirpath = os.path.dirname(dest_filepath)
	if not os.path.isdir(dest_dirpath):
		os.makedirs(dest_dirpath)

	# write out the settings file
	with open(dest_filepath, "wb") as out_file:
		out_file.write(json.dumps(dest_structure, indent=4))

	# backup and remove old settings file
	if os.path.isfile(source_settings_path):
		backup_filepath = os.path.join(dest_dirpath, os.path.basename(source_settings_path)) + ".old-0.6"
		if os.path.isfile(backup_filepath):
			os.remove(backup_filepath)
		os.rename(source_settings_path, backup_filepath)

	# remove old plugin opt-out dir
	if os.path.isdir(source_states_dirpath):
		shutil.rmtree(source_states_dirpath)
