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

from ..infrastructure import utils, gameapi
from ..constants import SettingConstants
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
		utils.CURRENT_LOG_LEVEL = value
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
	minimap_api = None
	chat_indicator_api = None
	settings_repository = None
	chat_user_repository = None
	speak_state_repository = None

	def execute(self, client_id, nick, game_nick, unique_id, channel_id, speaking):
		old_user = self.chat_user_repository.get(client_id)
		if old_user:
			speak_update = old_user.speaking != speaking
		else:
			speak_update = speaking
		new_user = self.chat_user_repository.set(entities.TeamSpeakUser(
			nick = nick,
			game_nick = game_nick,
			client_id = client_id,
			unique_id = unique_id,
			channel_id = channel_id,
			speaking = speaking
		))
		if new_user.channel_id == self.chat_client_api.get_current_channel_id():
			self.user_cache_api.add_chat_user(new_user.unique_id, new_user.nick)
			if speak_update:
				self.__find_and_pair_chat_user_to_player(new_user.client_id)
				self.__set_chat_user_speaking(new_user.client_id)

	def __find_and_pair_chat_user_to_player(self, user_id):
		user = self.chat_user_repository.get(user_id)
		player = utils.ts_user_to_player(
			user_nick = user.nick,
			user_game_nick = user.game_nick,
			use_metadata = self.settings_repository.get(SettingConstants.GET_GAME_NICK_FROM_CHAT_CLIENT),
			use_ts_nick_search = self.settings_repository.get(SettingConstants.CHAT_NICK_SEARCH_ENABLED),
			extract_patterns = self.settings_repository.get(SettingConstants.NICK_EXTRACT_PATTERNS),
			mappings = self.settings_repository.get(SettingConstants.NICK_MAPPINGS),
			# TODO: should we use clanmembers=True, friends=True here too??
			players = utils.get_players(in_battle=True, in_prebattle=True)
		)
		if player:
			self.user_cache_api.add_player(id=player["id"], name=player["name"])
			self.user_cache_api.pair(player["id"], user.unique_id)

	def __set_chat_user_speaking(self, user_id):
		user = self.chat_user_repository.get(user_id)
		if not user:
			return
		for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
			player = utils.get_player_by_dbid(player_id)
			self.speak_state_repository[player["id"]] = user.speaking
			if user.speaking:
				# set speaking state immediately
				self.__update_player_speak_status(player)
			else:
				# keep speaking state for a little longer
				gameapi.EventLoop.callback(self.settings_repository.get(SettingConstants.SPEAK_STOP_DELAY), self.__update_player_speak_status, player)

	def __update_player_speak_status(self, player):
		try:
			self.chat_indicator_api.set_player_speaking(
				player=player,
				speaking=(
					self.__is_voice_chat_speak_allowed(player["id"]) and
					self.speak_state_repository.get(player["id"])
				)
			)
		except:
			utils.LOG_CURRENT_EXCEPTION()

		try:
			self.minimap_api.set_player_speaking(
				player=player,
				speaking=(
					self.speak_state_repository.get(player["id"]) and
					self.__is_minimap_speak_allowed(player["id"]) and
					player["is_alive"]
				)
			)
		except:
			utils.LOG_CURRENT_EXCEPTION()

	def __is_minimap_speak_allowed(self, player_id):
		if not self.settings_repository.get(SettingConstants.MINIMAP_NOTIFY_ENABLED):
			return False
		if not self.settings_repository.get(SettingConstants.MINIMAP_NOTIFY_SELF_ENABLED) and utils.get_my_dbid() == player_id:
			return False
		return True

	def __is_voice_chat_speak_allowed(self, player_id):
		if not self.settings_repository.get(SettingConstants.VOICE_CHAT_NOTIFY_ENABLED):
			return False
		if not self.settings_repository.get(SettingConstants.VOICE_CHAT_NOTIFY_SELF_ENABLED) and utils.get_my_dbid() == player_id:
			return False
		return True

class RemoveChatUser(object):

	chat_indicator_api = None
	minimap_api = None
	user_cache_api = None
	chat_user_repository = None
	speak_state_repository = None

	def execute(self, client_id):
		user = self.chat_user_repository.get(client_id)
		if user.speaking:
			self.__stop_user_feedback(user)
		self.chat_user_repository.remove(client_id)

	def __stop_user_feedback(self, user):
		for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
			player = utils.get_player_by_dbid(player_id)
			self.speak_state_repository[player["id"]] = False
			self.__update_player_speak_status(player)

	def __update_player_speak_status(self, player):
		try:
			self.chat_indicator_api.set_player_speaking(player=player, speaking=False)
		except:
			utils.LOG_CURRENT_EXCEPTION()

		try:
			self.minimap_api.set_player_speaking(player=player, speaking=False)
		except:
			utils.LOG_CURRENT_EXCEPTION()

class ChangeChatChannel(object):

	user_cache_api = None
	chat_user_repository = None

	def execute(self, channel_id):
		for user in self.chat_user_repository:
			self.__add_to_cache(user, channel_id)

	def __add_to_cache(self, user, current_channel_id):
		if user.channel_id == current_channel_id:
			self.user_cache_api.add_chat_user(user.unique_id, user.nick)

class ClearSpeakStatuses(object):

	minimap_api = None
	chat_indicator_api = None
	speak_state_repository = None

	def execute(self):
		'''Clears speak status of all players.'''
		self.speak_state_repository.clear()
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
			LOG_ERROR("Failed to get current Windows OS version")
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

	def execute(self):
		self.chat_client_api.set_game_nickname(utils.get_my_name())

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

	game_api = None
	chat_client_api = None
	user_cache_api = None
	chat_user_repository = None
	vehicle_repository = None

	def execute(self):
		camera_position = self.game_api.get_camera_position()
		camera_direction = self.game_api.get_camera_direction()
		positions = {}
		for user in self.chat_user_repository:
			for player_id in self.user_cache_api.get_paired_player_ids(user.unique_id):
				vehicle = self.vehicle_repository.get(player_id=player_id)
				if vehicle.is_alive:
					positions[user.client_id] = vehicle.position
		if camera_position and camera_direction and positions:
			self.chat_client_api.update_positional_data(camera_position, camera_direction, positions)

class BattleReplayStart(object):

	user_cache_api = None
	settings_repository = None

	def execute(self):
		self.user_cache_api.set_write_enabled(self.settings_repository.get(SettingConstants.UPDATE_CACHE_IN_REPLAYS))
