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

import logutils
from infrastructure.gameapi import Environment

import os
import json
import ConfigParser
import csv

logger = logutils.logger.getChild("migrate")
res_mods_dirpath = os.path.join(Environment.find_res_mods_version_path(), "..")

def migrate():
	migrate_user_cache_0_6_to_0_7()
	migrate_settings_0_6_to_0_7()

def migrate_user_cache_0_6_to_0_7():
	"""
	This function migrates configs/tessu_mod/tessu_mod_cache.ini to configs/tessumod/usercache.json.
	"""

	source_filepath = os.path.join(res_mods_dirpath, "configs", "tessu_mod", "tessu_mod_cache.ini")
	dest_filepath = os.path.join(res_mods_dirpath, "configs", "tessumod", "usercache.json")

	# create destination contents, basing it to an existing file if one exists
	dest_structure = { "version": 1, "pairings": [] }
	if os.path.isfile(dest_filepath):
		with open(dest_filepath, "rb") as file:
			dest_structure = json.loads(file.read())

	if os.path.isfile(source_filepath) and dest_structure["version"] == 1:
		logger.info("Migrating user cache from 0.6 to 0.7")

		parser = ConfigParser.ConfigParser()
		with open(source_filepath, "rb") as file:
			parser.readfp(file)

		usernames_by_id = {}
		userids_by_name = {}
		for name, id in parser.items("TeamSpeakUsers"):
			usernames_by_id[id] = name
			userids_by_name[name] = id

		playernames_by_id = {}
		playerids_by_name = {}
		for name, id in parser.items("GamePlayers"):
			playernames_by_id[int(id)] = name
			playerids_by_name[name] = int(id)

		# collect and append pairings
		for user_name, player_names in parser.items("UserPlayerPairings"):
			userid = userids_by_name[user_name]
			for player_name in list(csv.reader([player_names]))[0]:
				playerid = playerids_by_name[player_name]
				dest_structure["pairings"].append([
					{ "id": userid, "name": user_name },
					{ "id": playerid, "name": player_name }
				])

		# remove duplicates, compare only id values as name values might be
		# same, but with different case
		id_pairings = []
		unique_pairings = []
		for pairing in dest_structure["pairings"]:
			id_pairing = (pairing[0]["id"], pairing[1]["id"])
			if id_pairing not in id_pairings:
				id_pairings.append(id_pairing)
				unique_pairings.append(pairing)
		dest_structure["pairings"] = unique_pairings

		# create destination directory if it doesn't exist yet
		dest_dirpath = os.path.dirname(dest_filepath)
		if not os.path.isdir(dest_dirpath):
			os.makedirs(dest_dirpath)

		# write out the new cache file
		with open(dest_filepath, "wb") as out_file:
			out_file.write(json.dumps(dest_structure, indent=4))

		# backup and remove old cache file
		backup_filepath = os.path.join(dest_dirpath, os.path.basename(source_filepath)) + ".old-0.6"
		if os.path.isfile(backup_filepath):
			os.remove(backup_filepath)
		os.rename(source_filepath, backup_filepath)

def migrate_settings_0_6_to_0_7():
	# TODO: migrate settings ini file
	# TODO: migrate states-folder
	pass
