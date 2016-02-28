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

from ..infrastructure.user_cache import UserCache
from ..infrastructure.timer import TimerMixin

class UserCacheAdapter(TimerMixin):

	def __init__(self, boundaries):
		super(UserCacheAdapter, self).__init__()
		self.__boundaries = boundaries
		self.__usercache = None
		self.on_timeout(1, self.__on_sync_timeout, repeat=True)

	def init(self, cache_filepath):
		self.__usercache = UserCache(cache_filepath)
		self.__usercache.on_read_error += self.__on_read_error
		self.__usercache.init()

	def set_file_check_interval(self, interval):
		self.on_timeout(interval, self.__on_sync_timeout, repeat=True)

	def set_write_enabled(self, enabled):
		self.__usercache.is_write_enabled = enabled

	def add_chat_user(self, unique_id, nick):
		self.__usercache.add_ts_user(nick, unique_id)

	def add_player(self, id, name):
		self.__usercache.add_player(name, id)

	def pair(self, player_id, user_unique_id):
		self.__usercache.pair(player_id=player_id, ts_user_id=user_unique_id)

	def get_paired_player_ids(self, user_unique_id):
		return self.__usercache.get_paired_player_ids(user_unique_id)

	def get_config_filepath(self):
		return self.__usercache.ini_path

	def __on_read_error(self, error_message):
		'''This function is called if user cache's reading fails.'''
		self.__boundaries.usecase_show_cache_error_message(error_message)

	def __on_sync_timeout(self):
		if self.__usercache:
			self.__usercache.sync()
