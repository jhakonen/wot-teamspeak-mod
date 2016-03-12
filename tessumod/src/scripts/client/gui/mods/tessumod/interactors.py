# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2015  Janne Hakonen
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

import sys
import os
import copy
from functools import partial

from infrastructure import log, timer
from constants import SettingConstants

class Initialize(object):

	INJECT = (
		"settings",
		"datastorage",
		"notifications",
		"usercache",
		"chatclient",
		"environment"
	)

	def execute(self):
		mods_dirpath = self.environment.get_mods_dirpath()
		settings_dirpath = os.path.join(mods_dirpath, "..", "configs", "tessu_mod")

		self.settings.init(os.path.join(settings_dirpath, "tessu_mod.ini"))
		self.usercache.init(os.path.join(settings_dirpath, "tessu_mod_cache.ini"))
		self.datastorage.init(os.path.join(settings_dirpath, "states"))
		self.chatclient.init(os.path.join(mods_dirpath, "tessumod.ts3_plugin"))
		self.notifications.init()

class LoadSettings(object):

	INJECT = ("chatclient", "minimap", "settings", "usercache")

	def execute(self, variables):
		variables = copy.copy(variables)
		value = variables.pop(SettingConstants.LOG_LEVEL)
		log.CURRENT_LOG_LEVEL = value
		value = variables.pop(SettingConstants.FILE_CHECK_INTERVAL)
		self.settings.set_file_check_interval(value)
		self.usercache.set_file_check_interval(value)
		value = variables.pop(SettingConstants.SPEAK_STOP_DELAY)
		value = variables.pop(SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT)
		value = variables.pop(SettingConstants.UPDATE_CACHE_IN_REPLAYS)
		value = variables.pop(SettingConstants.CHAT_NICK_SEARCH_ENABLED)
		value = variables.pop(SettingConstants.NICK_EXTRACT_PATTERNS)
		value = variables.pop(SettingConstants.NICK_MAPPINGS)
		value = variables.pop(SettingConstants.CHAT_CLIENT_HOST)
		self.chatclient.set_host(value)
		value = variables.pop(SettingConstants.CHAT_CLIENT_PORT)
		self.chatclient.set_port(value)
		value = variables.pop(SettingConstants.CHAT_CLIENT_POLLING_INTERVAL)
		self.chatclient.set_polling_interval(value)
		value = variables.pop(SettingConstants.VOICE_CHAT_NOTIFY_ENABLED)
		value = variables.pop(SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED)
		value = variables.pop(SettingConstants.MINIMAP_NOTIFY_ENABLED)
		value = variables.pop(SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED)
		value = variables.pop(SettingConstants.MINIMAP_NOTIFY_ACTION)
		self.minimap.set_action(value)
		value = variables.pop(SettingConstants.MINIMAP_NOTIFY_REPEAT_INTERVAL)
		self.minimap.set_action_interval(value)
		assert not variables, "Not all variables have been handled"

class CacheChatUser(object):

	INJECT = ("usercache", "chatclient")

	def execute(self, client_id):
		if self.chatclient.has_user(client_id):
			user = self.chatclient.get_user(client_id)
			if user["in_my_channel"]:
				self.usercache.add_chat_user(user["unique_id"], user["nick"])

class PairChatUserToPlayer(object):

	INJECT = ("usercache", "chatclient", "players", "settings")

	def execute(self, client_id):
		if not self.chatclient.has_user(client_id):
			return

		user = self.chatclient.get_user(client_id)
		if not user["in_my_channel"]:
			return

		players = list(self.players.get_players(in_battle=True, in_prebattle=True))
		mappings = self.settings.get(SettingConstants.NICK_MAPPINGS)
		extract_patterns = self.settings.get(SettingConstants.NICK_EXTRACT_PATTERNS)
		use_ts_nick_search = self.settings.get(SettingConstants.CHAT_NICK_SEARCH_ENABLED)
		use_metadata = self.settings.get(SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT)

		def find_player(nick, comparator=lambda a, b: a == b):
			if hasattr(nick, "lower"):
				for player in players:
					if comparator(player["name"].lower(), nick.lower()):
						return player

		def map_nick(nick):
			if hasattr(nick, "lower"):
				try:
					return mappings[nick.lower()]
				except:
					pass

		def match_using_metadata():
			# find player using TS user's WOT nickname in metadata (available if user
			# has TessuMod installed)
			if user["game_nick"]:
				player = find_player(user["game_nick"])
				if player:
					log.LOG_DEBUG("Matched TS user to player with TS metadata", user["nick"], user["game_nick"], player)
				return player

		def match_using_extract_patterns():
			# no metadata, try find player by using WOT nickname extracted from TS
			# user's nickname using nick_extract_patterns
			for pattern in extract_patterns:
				matches = pattern.match(user["nick"])
				if matches is not None and matches.groups():
					extracted_nick = matches.group(1).strip()
					player = find_player(extracted_nick)
					if player:
						log.LOG_DEBUG("Matched TS user to player with pattern", user["nick"], player, pattern.pattern)
						return player
					# extracted nickname didn't match any player, try find player by
					# mapping the extracted nickname to WOT nickname (if available)
					player = find_player(map_nick(extracted_nick))
					if player:
						log.LOG_DEBUG("Matched TS user to player with pattern and mapping", user["nick"], player, pattern.pattern)
						return player

		def match_using_mappings():
			# extract patterns didn't help, try find player by mapping TS nickname to
			# WOT nickname (if available)
			player = find_player(map_nick(user["nick"]))
			if player:
				log.LOG_DEBUG("Matched TS user to player via mapping", user["nick"], player)
				return player

		def match_using_name_comparison():
			# still no match, as a last straw, try find player by searching each known
			# WOT nickname from the TS nickname
			if use_ts_nick_search:
				player = find_player(user["nick"], comparator=lambda a, b: a in b)
				if player:
					log.LOG_DEBUG("Matched TS user to player with TS nick search", user["nick"], player)
					return player
			# or alternatively, try find player by just comparing that TS nickname and
			# WOT nicknames are same
			else:
				player = find_player(user["nick"])
				if player:
					log.LOG_DEBUG("Matched TS user to player by comparing names", user["nick"], player)
					return player

		matchers = []
		if use_metadata:
			matchers.append(match_using_metadata)
		if extract_patterns:
			matchers.append(match_using_extract_patterns)
		if mappings:
			matchers.append(match_using_mappings)
		matchers.append(match_using_name_comparison)

		for matcher in matchers:
			player = matcher()
			if player is not None:
				break

		if player:
			self.usercache.add_player(id=player["id"], name=player["name"])
			self.usercache.pair(player["id"], user["unique_id"])
		else:
			log.LOG_DEBUG("Failed to match TS user", user["nick"])

class UpdateChatUserSpeakState(timer.TimerMixin):

	INJECT = (
		"usercache",
		"chatclient",
		"minimap",
		"chatindicator",
		"players",
		"settings"
	)

	def execute(self, client_id):
		if not self.chatclient.has_user(client_id):
			return

		user = self.chatclient.get_user(client_id)
		if not user["in_my_channel"]:
			return

		if user["speaking"]:
			# set speaking state immediately
			self.__update_chat_user_speak_status(client_id)
		else:
			# keep speaking state for a little longer
			secs = self.settings.get(SettingConstants.SPEAK_STOP_DELAY)
			self.on_timeout(secs, partial(self.__update_chat_user_speak_status, client_id))

	def __update_chat_user_speak_status(self, client_id):
		if not self.chatclient.has_user(client_id):
			return
		user = self.chatclient.get_user(client_id)
		for player_id in self.usercache.get_paired_player_ids(user["unique_id"]):
			player = self.players.get_player_by_dbid(player_id)
			if player:
				try:
					self.chatindicator.set_player_speaking(
						player=player,
						speaking=user["speaking"] and self.__is_voice_chat_speak_allowed(player["id"])
					)
				except:
					log.LOG_CURRENT_EXCEPTION()

				try:
					self.minimap.set_player_speaking(
						player=player,
						speaking=user["speaking"] and player["is_alive"] and self.__is_minimap_speak_allowed(player["id"])
					)
				except:
					log.LOG_CURRENT_EXCEPTION()

	def __is_minimap_speak_allowed(self, player_id):
		if not self.settings.get(SettingConstants.MINIMAP_NOTIFY_ENABLED):
			return False
		if not self.settings.get(SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED) and self.players.get_my_dbid() == player_id:
			return False
		return True

	def __is_voice_chat_speak_allowed(self, player_id):
		if not self.settings.get(SettingConstants.VOICE_CHAT_NOTIFY_ENABLED):
			return False
		if not self.settings.get(SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED) and self.players.get_my_dbid() == player_id:
			return False
		return True

class RemoveChatUser(object):

	INJECT = ("chatclient", "chatindicator", "minimap", "usercache", "players")

	def execute(self, client_id):
		if not self.chatclient.has_user(client_id):
			return
		user = self.chatclient.get_user(client_id)
		if user["speaking"]:
			self.__stop_user_feedback(user)

	def __stop_user_feedback(self, user):
		for player_id in self.usercache.get_paired_player_ids(user["unique_id"]):
			player = self.players.get_player_by_dbid(player_id)
			if player:
				self.__update_player_speak_status(player)

	def __update_player_speak_status(self, player):
		try:
			self.chatindicator.set_player_speaking(player=player, speaking=False)
		except:
			log.LOG_CURRENT_EXCEPTION()

		try:
			self.minimap.set_player_speaking(player=player, speaking=False)
		except:
			log.LOG_CURRENT_EXCEPTION()

class ClearSpeakStatuses(object):

	INJECT = ("minimap", "chatindicator")

	def execute(self):
		'''Clears speak status of all players.'''
		self.minimap.clear_all_players_speaking()
		self.chatindicator.clear_all_players_speaking()

class NotifyChatClientDisconnected(object):

	INJECT = ("notifications",)

	def execute(self):
		self.notifications.show_warning_message("Disconnected from TeamSpeak client")

class ShowChatClientPluginInstallMessage(object):

	INJECT = ("notifications", "chatclient", "datastorage")

	AVAILABLE_PLUGIN_VERSION = 1

	def execute(self):
		installer_path = self.chatclient.get_plugin_filepath()
		# plugin doesn't work in WinXP so check that we are running on
		# sufficiently recent Windows OS
		if not self.__is_vista_or_newer():
			return
		if not os.path.isfile(installer_path):
			return
		if self.__is_newest_plugin_version(self.chatclient.get_installed_plugin_version()):
			return
		if self.__is_newest_plugin_version(self.__get_ignored_plugin_version()):
			return
		self.notifications.show_plugin_install_message()

	def __is_vista_or_newer(self):
		'''Returns True if the game is running on Windows Vista or newer OS.'''
		try:
			return sys.getwindowsversion()[0] >= 6
		except:
			log.LOG_ERROR("Failed to get current Windows OS version")
			return True

	def __is_newest_plugin_version(self, plugin_version):
		return plugin_version >= self.AVAILABLE_PLUGIN_VERSION

	def __get_ignored_plugin_version(self):
		version = self.datastorage.get("ignored_plugin_version")
		if version is not None:
			return int(version)
		return 0

class InstallChatClientPlugin(object):

	INJECT = ("chatclient",)

	def execute(self):
		self.chatclient.install_plugin()

class IgnoreChatClientPluginInstallMessage(object):

	INJECT = ("datastorage",)

	AVAILABLE_PLUGIN_VERSION = ShowChatClientPluginInstallMessage.AVAILABLE_PLUGIN_VERSION

	def execute(self, ignored):
		self.datastorage.set("ignored_plugin_version", self.AVAILABLE_PLUGIN_VERSION if ignored else 0)

class ShowChatClientPluginInfoUrl(object):

	INJECT = ("chatclient",)

	def execute(self, url):
		self.chatclient.show_plugin_info_url(url)

class NotifyConnectedToChatServer(object):

	INJECT = ("notifications",)

	def execute(self, server_name):
		self.notifications.show_info_message("Connected to TeamSpeak server '{0}'".format(server_name))

class PublishGameNickToChatServer(object):

	INJECT = ("chatclient", "players")

	def execute(self):
		self.chatclient.set_game_nickname(self.players.get_my_name())

class ShowCacheErrorMessage(object):

	INJECT = ("notifications", "usercache")

	def execute(self, error_message):
		self.notifications.show_error_message("Failed to read file '{0}':\n   {1}"
			.format(self.usercache.get_config_filepath(), error_message))

class EnablePositionalDataToChatClient(object):

	INJECT = ("chatclient",)

	def execute(self, enabled):
		self.chatclient.enable_positional_data(enabled)

class ProvidePositionalDataToChatClient(object):

	INJECT = ("battle", "chatclient", "usercache")

	def execute(self):
		camera_position = self.battle.get_camera_position()
		camera_direction = self.battle.get_camera_direction()
		positions = {}
		for user in self.chatclient.get_users():
			for player_id in self.usercache.get_paired_player_ids(user["unique_id"]):
				vehicle = self.battle.get_vehicle(player_id=player_id)
				if vehicle and vehicle["is-alive"] and vehicle["position"]:
					positions[user["client_id"]] = vehicle["position"]
		if camera_position and camera_direction and positions:
			self.chatclient.update_positional_data(camera_position, camera_direction, positions)

class BattleReplayStart(object):

	INJECT = ("usercache", "settings")

	def execute(self):
		self.usercache.set_write_enabled(self.settings.get(SettingConstants.UPDATE_CACHE_IN_REPLAYS))

class PopulateUserCacheWithPlayers(object):

	INJECT = ("usercache", "players")

	def execute(self):
		for player in self.players.get_players(clanmembers=True, friends=True):
			self.usercache.add_player(id=player["id"], name=player["name"])
