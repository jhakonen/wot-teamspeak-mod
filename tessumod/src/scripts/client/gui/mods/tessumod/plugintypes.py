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

from thirdparty.yapsy import IPlugin

class ModPlugin(IPlugin.IPlugin):

	def __init__(self):
		super(ModPlugin, self).__init__()

	@property
	def plugin_manager(self):
		return self.__plugin_manager

	@plugin_manager.setter
	def plugin_manager(self, plugin_manager):
		self.__plugin_manager = plugin_manager

	def initialize(self):
		pass

	def deinitialize(self):
		pass

class PlayerNotificationsMixin(object):
	"""
	Has notification callbacks which are called when players are found, changed or lost.

	Arguments:
		source - can be one of following: voice, battle, prebattle, friends, clanmembers
		player - a dict object which must have at least following key/values:
			"id": [int] <player id>
			"name": [string] <player name>
			"is_me": [bool] <is self player>

			With source 'battle' the dict must have following entries:
				"vehicle_id": [int] <vehicle id in battle>
				"is_alive": [bool] <is player alive in battle>

			With source 'teamspeak' the dict must have entry:
				"speaking": [bool] <is player speaking>
	"""

	def __init__(self):
		super(PlayerNotificationsMixin, self).__init__()

	def on_player_added(self, source, player):
		"""
		Called when a 'player' is added to a 'source'.
		"""
		pass

	def on_player_modified(self, source, player):
		"""
		Called when a 'player' has changed in 'source'.
		"""
		pass

	def on_player_removed(self, source, player):
		"""
		Called when a 'player' has been removed from 'source'.
		"""
		pass

class SettingsMixin(object):

	def __init__(self):
		super(SettingsMixin, self).__init__()

	def on_settings_changed(self, section, name, value):
		pass

	def get_settings_content(self):
		pass

class VoiceUserNotificationsMixin(object):
	"""
	Has notification callbacks which are called when voice users are found, changed or lost.

	Arguments:
		user - a dict object which must have following key/values:
			"id": [int] <user id, e.g server id + client id in case of teamspeak>
			"identity": [string] <id which identifies user, multiple users may have same identity>
			"name": [string] <user name>
			"game_name": [string] <name in game if available, empty string if not>
			"is_speaking": [bool] <is user speaking or not>
			"is_me": [bool] <is self user>

	"""

	def __init__(self):
		super(PlayerNotificationsMixin, self).__init__()

	def on_voice_user_added(self, user):
		"""
		Called when a 'user' has been added.
		"""
		pass

	def on_voice_user_modified(self, user):
		"""
		Called when a 'user' has changed.
		"""
		pass

	def on_voice_user_removed(self, user):
		"""
		Called when a 'user' has been removed.
		"""
		pass

class UserMatchingMixin(object):
	"""
	"""

	def __init__(self):
		super(UserMatchingMixin, self).__init__()

	def on_user_matched(self, user_identity, player_id):
		"""
		"""
		pass
