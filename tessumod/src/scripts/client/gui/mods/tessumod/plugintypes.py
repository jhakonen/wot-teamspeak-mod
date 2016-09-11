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

class PlayerModelProvider(object):
	"""
	This class is an interface for getting player models from other plugins.
	Each player is stored into the model with a key which is same as player's "id" value.

	Possible model names include:
	 * battle
	 * prebattle
	 * friends
	 * clanmembers
	 * voice

	Each player in the model is dict object which must have at least following key/values:
	 * "id": [int] <player id>
	 * "name": [string] <player name>
	 * "is_me": [bool] <is self player>

	With source 'battle' the dict must have following entries:
	 * "vehicle_id": [int] <vehicle id in battle>
	 * "is_alive": [bool] <is player alive in battle>

	With source 'voice' the dict must have entry:
	 * "speaking": [bool] <is player speaking>
	"""

	def __init__(self):
		super(PlayerModelProvider, self).__init__()

	def has_player_model(self, name):
		"""
		Returns true if this plugin has a player model matching given 'name'.
		False otherwise.
		"""
		pass

	def get_player_model(self, name):
		"""
		Returns player model object matching to given 'name'.
		"""
		pass

class UserModelProvider(object):
	"""
	This class is an interface for getting voice chat user models from other plugins.
	Each user is stored into the model with a key which is same as user's "id" value.

	Each user in the model is a dict object which must have following key/values:
	 * "id": [int] <user id, e.g server id + client id in case of teamspeak>
	 * "identity": [string] <id which identifies user, multiple users may have same identity>
	 * "name": [string] <user name>
	 * "game_name": [string] <name in game if available, empty string if not>
	 * "is_speaking": [bool] <is user speaking or not>
	 * "is_me": [bool] <is self user>
	"""

	def __init__(self):
		super(UserModelProvider, self).__init__()

	def has_user_model(self):
		"""
		Returns true if this plugin has a user model.
		False otherwise.
		"""
		pass

	def get_user_model(self):
		"""
		Returns user model object.
		"""
		pass

class SettingsMixin(object):

	def __init__(self):
		super(SettingsMixin, self).__init__()

	def on_settings_changed(self, section, name, value):
		pass

	def get_settings_content(self):
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

class VoiceClientListener(object):
	"""
	"""

	def __init__(self):
		super(VoiceClientListener, self).__init__()

	def on_voice_client_connected(self):
		pass

	def on_voice_client_disconnected(self):
		pass

	def on_voice_server_connected(self):
		pass

	def on_voice_server_disconnected(self):
		pass
