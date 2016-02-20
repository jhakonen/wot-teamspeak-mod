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

from infrastructure import utils, gameapi, log
from constants import SettingConstants
import entities

class LoadSettings(object):

	chat_client_api = None
	minimap_api = None
	settings_api = None
	user_cache_api = None
	settings_repository = None

	def execute(self, variables):
		def take_and_store(key):
			value = variables[key]
			del variables[key]
			self.settings_repository.set(key, value)
			return value
		value = take_and_store(SettingConstants.LOG_LEVEL)
		log.CURRENT_LOG_LEVEL = value
		value = take_and_store(SettingConstants.FILE_CHECK_INTERVAL)
		self.settings_api.set_file_check_interval(value)
		self.user_cache_api.set_file_check_interval(value)
		value = take_and_store(SettingConstants.SPEAK_STOP_DELAY)
		value = take_and_store(SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT)
		value = take_and_store(SettingConstants.UPDATE_CACHE_IN_REPLAYS)
		value = take_and_store(SettingConstants.CHAT_NICK_SEARCH_ENABLED)
		value = take_and_store(SettingConstants.NICK_EXTRACT_PATTERNS)
		value = take_and_store(SettingConstants.NICK_MAPPINGS)
		value = take_and_store(SettingConstants.CHAT_CLIENT_HOST)
		self.chat_client_api.set_host(value)
		value = take_and_store(SettingConstants.CHAT_CLIENT_PORT)
		self.chat_client_api.set_port(value)
		value = take_and_store(SettingConstants.CHAT_CLIENT_POLLING_INTERVAL)
		self.chat_client_api.set_polling_interval(value)
		value = take_and_store(SettingConstants.VOICE_CHAT_NOTIFY_ENABLED)
		value = take_and_store(SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED)
		value = take_and_store(SettingConstants.MINIMAP_NOTIFY_ENABLED)
		value = take_and_store(SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED)
		value = take_and_store(SettingConstants.MINIMAP_NOTIFY_ACTION)
		self.minimap_api.set_action(value)
		value = take_and_store(SettingConstants.MINIMAP_NOTIFY_REPEAT_INTERVAL)
		self.minimap_api.set_action_interval(value)
		assert not variables, "Not all variables have been handled"

class InsertChatUser(object):

	user_cache_api = None
	chat_client_api = None
	chat_user_repository = None

	def execute(self, client_id, **client_data):
		if self.chat_user_repository.has(client_id):
			old_user = self.chat_user_repository.get(client_id)
			new_user = self.chat_user_repository.set(entities.ChatClientUser(
				client_id = client_id,
				nick = client_data["nick"] if "nick" in client_data else old_user.nick,
				game_nick = client_data["game_nick"] if "game_nick" in client_data else old_user.game_nick,
				unique_id = client_data["unique_id"] if "unique_id" in client_data else old_user.unique_id,
				channel_id = client_data["channel_id"] if "channel_id" in client_data else old_user.channel_id,
				speaking = client_data["speaking"] if "speaking" in client_data else old_user.speaking,
				is_me = client_data["is_me"] if "is_me" in client_data else old_user.is_me,
				in_my_channel = client_data["in_my_channel"] if "in_my_channel" in client_data else old_user.in_my_channel
			))
		else:
			new_user = self.chat_user_repository.set(entities.ChatClientUser(
				client_id = client_id,
				nick = client_data.get("nick", None),
				game_nick = client_data.get("game_nick", None),
				unique_id = client_data.get("unique_id", None),
				channel_id = client_data.get("channel_id", None),
				speaking = client_data.get("speaking", None),
				is_me = client_data.get("is_me", None),
				in_my_channel = client_data.get("in_my_channel", None)
			))
		if new_user.in_my_channel:
			self.user_cache_api.add_chat_user(new_user.unique_id, new_user.nick)

class PairChatUserToPlayer(object):

	user_cache_api = None
	chat_client_api = None
	player_api = None
	settings_repository = None
	chat_user_repository = None

	def execute(self, client_id):
		user = self.chat_user_repository.get(client_id)
		if user.in_my_channel:
			self.__find_and_pair_chat_user_to_player(client_id)

	def __find_and_pair_chat_user_to_player(self, client_id):
		user = self.chat_user_repository.get(client_id)
		players = list(self.player_api.get_players(in_battle=True, in_prebattle=True))
		mappings = self.settings_repository.get(SettingConstants.NICK_MAPPINGS)
		extract_patterns = self.settings_repository.get(SettingConstants.NICK_EXTRACT_PATTERNS)
		use_ts_nick_search = self.settings_repository.get(SettingConstants.CHAT_NICK_SEARCH_ENABLED)
		use_metadata = self.settings_repository.get(SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT)

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
			if user.game_nick:
				player = find_player(user.game_nick)
				if player:
					log.LOG_DEBUG("Matched TS user to player with TS metadata", user.nick, user.game_nick, player)
				return player

		def match_using_extract_patterns():
			# no metadata, try find player by using WOT nickname extracted from TS
			# user's nickname using nick_extract_patterns
			for pattern in extract_patterns:
				matches = pattern.match(user.nick)
				if matches is not None and matches.groups():
					extracted_nick = matches.group(1).strip()
					player = find_player(extracted_nick)
					if player:
						log.LOG_DEBUG("Matched TS user to player with pattern", user.nick, player, pattern.pattern)
						return player
					# extracted nickname didn't match any player, try find player by
					# mapping the extracted nickname to WOT nickname (if available)
					player = find_player(map_nick(extracted_nick))
					if player:
						log.LOG_DEBUG("Matched TS user to player with pattern and mapping", user.nick, player, pattern.pattern)
						return player

		def match_using_mappings():
			# extract patterns didn't help, try find player by mapping TS nickname to
			# WOT nickname (if available)
			player = find_player(map_nick(user.nick))
			if player:
				log.LOG_DEBUG("Matched TS user to player via mapping", user.nick, player)
				return player

		def match_using_name_comparison():
			# still no match, as a last straw, try find player by searching each known
			# WOT nickname from the TS nickname
			if use_ts_nick_search:
				player = find_player(user.nick, comparator=lambda a, b: a in b)
				if player:
					log.LOG_DEBUG("Matched TS user to player with TS nick search", user.nick, player)
					return player
			# or alternatively, try find player by just comparing that TS nickname and
			# WOT nicknames are same
			else:
				player = find_player(user.nick)
				if player:
					log.LOG_DEBUG("Matched TS user to player by comparing names", user.nick, player)
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
			self.user_cache_api.add_player(id=player["id"], name=player["name"])
			self.user_cache_api.pair(player["id"], user.unique_id)
		else:
			log.LOG_DEBUG("Failed to match TS user", user.nick)

class UpdateChatUserSpeakState(object):

	user_cache_api = None
	chat_client_api = None
	minimap_api = None
	chat_indicator_api = None
	player_api = None
	settings_repository = None
	chat_user_repository = None

	def execute(self, client_id):
		user = self.chat_user_repository.get(client_id)
		if user.in_my_channel:
			self.__set_chat_user_speaking(client_id)

	def __set_chat_user_speaking(self, client_id):
		if self.chat_user_repository.has(client_id):
			user = self.chat_user_repository.get(client_id)
			if user.speaking:
				# set speaking state immediately
				self.__update_chat_user_speak_status(client_id)
			else:
				# keep speaking state for a little longer
				gameapi.EventLoop.callback(self.settings_repository.get(SettingConstants.SPEAK_STOP_DELAY), self.__update_chat_user_speak_status, client_id)

	def __update_chat_user_speak_status(self, client_id):
		if self.chat_user_repository.has(client_id):
			user = self.chat_user_repository.get(client_id)
			for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
				player = self.player_api.get_player_by_dbid(player_id)
				if player:
					try:
						self.chat_indicator_api.set_player_speaking(
							player=player,
							speaking=user.speaking and self.__is_voice_chat_speak_allowed(player["id"])
						)
					except:
						log.LOG_CURRENT_EXCEPTION()

					try:
						self.minimap_api.set_player_speaking(
							player=player,
							speaking=user.speaking and player["is_alive"] and self.__is_minimap_speak_allowed(player["id"])
						)
					except:
						log.LOG_CURRENT_EXCEPTION()

	def __is_minimap_speak_allowed(self, player_id):
		if not self.settings_repository.get(SettingConstants.MINIMAP_NOTIFY_ENABLED):
			return False
		if not self.settings_repository.get(SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED) and self.player_api.get_my_dbid() == player_id:
			return False
		return True

	def __is_voice_chat_speak_allowed(self, player_id):
		if not self.settings_repository.get(SettingConstants.VOICE_CHAT_NOTIFY_ENABLED):
			return False
		if not self.settings_repository.get(SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED) and self.player_api.get_my_dbid() == player_id:
			return False
		return True

class RemoveChatUser(object):

	chat_indicator_api = None
	minimap_api = None
	user_cache_api = None
	player_api = None
	chat_user_repository = None

	def execute(self, client_id):
		user = self.chat_user_repository.get(client_id)
		if user.speaking:
			self.__stop_user_feedback(user)
		self.chat_user_repository.remove(client_id)

	def __stop_user_feedback(self, user):
		for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
			player = self.player_api.get_player_by_dbid(player_id)
			if player:
				self.__update_player_speak_status(player)

	def __update_player_speak_status(self, player):
		try:
			self.chat_indicator_api.set_player_speaking(player=player, speaking=False)
		except:
			log.LOG_CURRENT_EXCEPTION()

		try:
			self.minimap_api.set_player_speaking(player=player, speaking=False)
		except:
			log.LOG_CURRENT_EXCEPTION()

class ClearSpeakStatuses(object):

	minimap_api = None
	chat_indicator_api = None

	def execute(self):
		'''Clears speak status of all players.'''
		self.minimap_api.clear_all_players_speaking()
		self.chat_indicator_api.clear_all_players_speaking()

class NotifyChatClientDisconnected(object):

	notifications_api = None

	def execute(self):
		self.notifications_api.show_warning_message("Disconnected from TeamSpeak client")

class ShowChatClientPluginInstallMessage(object):

	AVAILABLE_PLUGIN_VERSION = 1

	notifications_api = None
	chat_client_api = None
	key_value_repository = None

	def execute(self):
		installer_path = utils.get_plugin_installer_path()
		# plugin doesn't work in WinXP so check that we are running on
		# sufficiently recent Windows OS
		if not self.__is_vista_or_newer():
			return
		if not os.path.isfile(installer_path):
			return
		if self.__is_newest_plugin_version(self.chat_client_api.get_installed_plugin_version()):
			return
		if self.__is_newest_plugin_version(self.__get_ignored_plugin_version()):
			return
		self.notifications_api.show_plugin_install_message()

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
		version = self.key_value_repository.get("ignored_plugin_version")
		if version is not None:
			return int(version)
		return 0

class InstallChatClientPlugin(object):

	chat_client_api = None

	def execute(self):
		self.chat_client_api.install_plugin()

class IgnoreChatClientPluginInstallMessage(object):

	AVAILABLE_PLUGIN_VERSION = ShowChatClientPluginInstallMessage.AVAILABLE_PLUGIN_VERSION
	key_value_repository = None

	def execute(self, ignored):
		self.key_value_repository.set("ignored_plugin_version", self.AVAILABLE_PLUGIN_VERSION if ignored else 0)

class ShowChatClientPluginInfoUrl(object):

	chat_client_api = None

	def execute(self, url):
		self.chat_client_api.show_plugin_info_url(url)

class NotifyConnectedToChatServer(object):

	notifications_api = None

	def execute(self, server_name):
		self.notifications_api.show_info_message("Connected to TeamSpeak server '{0}'".format(server_name))

class PublishGameNickToChatServer(object):

	chat_client_api = None
	player_api = None

	def execute(self):
		self.chat_client_api.set_game_nickname(self.player_api.get_my_name())

class ShowCacheErrorMessage(object):

	notifications_api = None
	user_cache_api = None

	def execute(self, error_message):
		self.notifications_api.show_error_message("Failed to read file '{0}':\n   {1}"
			.format(self.user_cache_api.get_config_filepath(), error_message))

class EnablePositionalDataToChatClient(object):

	chat_client_api = None

	def execute(self, enabled):
		self.chat_client_api.enable_positional_data(enabled)

class ProvidePositionalDataToChatClient(object):

	battle_api = None
	chat_client_api = None
	user_cache_api = None
	chat_user_repository = None
	vehicle_repository = None

	def execute(self):
		camera_position = self.battle_api.get_camera_position()
		camera_direction = self.battle_api.get_camera_direction()
		positions = {}
		for user in self.chat_user_repository:
			for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
				vehicle = self.vehicle_repository.get(player_id=player_id)
				if vehicle and vehicle.is_alive:
					positions[user.client_id] = vehicle.position
		if camera_position and camera_direction and positions:
			self.chat_client_api.update_positional_data(camera_position, camera_direction, positions)

class BattleReplayStart(object):

	user_cache_api = None
	settings_repository = None

	def execute(self):
		self.user_cache_api.set_write_enabled(self.settings_repository.get(SettingConstants.UPDATE_CACHE_IN_REPLAYS))

class PopulateUserCacheWithPlayers(object):

	user_cache_api = None
	player_api = None

	def execute(self):
		for player in self.player_api.get_players(clanmembers=True, friends=True):
			self.user_cache_api.add_player(id=player["id"], name=player["name"])
