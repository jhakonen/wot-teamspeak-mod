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

from gui.mods.tessumod import plugintypes, logutils, models
from gui.mods.tessumod.infrastructure.inifile import INIFile
from gui.mods.tessumod.infrastructure.gameapi import Environment
from BattleReplay import BattleReplay

logger = logutils.logger.getChild("usercache")

DEFAULT_INI = """
; This file stores paired TeamSpeak users and WOT players. When TessuMod
; manages to match a TeamSpeak user to a WOT player ingame it stores the match
; into this file. This allows TessuMod to match users in future even if the
; player's name changes in TeamSpeak or in game.
;
; This file can be modified and changes are automatically loaded even when game
; is running. The frequency of checks is determined by 'ini_check_interval'
; option in tessu_mod.ini.
;
; This file will not update with new users, players or pairings when playing
; replays. Although, if modified by user the done changes are still loaded
; automatically. To enable updates with replays toggle 'update_cache_in_replays'
; option in tessu_mod.ini to 'on'.
;
; All nick names in this cache are stored in lower case, no matter how they are
; written in WOT or in TeamSpeak. Also, any ini-syntax's reserved characters
; are replaced with '*'.


; TessuMod will populate this section with TeamSpeak users who are in the same
; TeamSpeak channel with you.
;
; The users are stored as key/value pairs where key is user's nick name and
; value is user's unique id. The nick doesn't have to be the real user nick
; name, it can be anything. If you modify the nick name, make sure you also
; update names used in UserPlayerPairings.
[TeamSpeakUsers]


; TessuMod will populate this section with players from your friend and clan
; member lists. Players are also added when someone speaks in your TeamSpeak
; channel and TessuMod manages to match the user to player which isn't yet in
; the cache.
;
; The players are stored as key/value pairs where key is player's nick name and
; value is player's id. The nick doesn't have to be the real player nick name,
; it can be anything. If you modify the nick name, make sure you also update
; names used in UserPlayerPairings.
[GamePlayers]


; This section is updated when TessuMod, using nick matching rules, manages to
; match TeamSpeak user to a WOT player.
;
; The pairings are stored as key/value pairs where key is TeamSpeak nick name
; and value is a list of WOT nick names that the TeamSpeak user will match
; against. The WOT nick list is a comma-separated-value.
[UserPlayerPairings]
"""

class UserCachePlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin,
	plugintypes.SettingsUIProvider, plugintypes.UserMatchingMixin):
	"""
	This plugin ...
	"""

	singleton = None

	def __init__(self):
		super(UserCachePlugin, self).__init__()
		UserCachePlugin.singleton = self
		self.__enabled_in_replays = False
		self.__in_replay = False
		self.__inifile = INIFile(DEFAULT_INI)
		self.__inifile.on("file-loaded", self.__on_file_loaded)
		self.__pairings = {}
		self.__reserved_player_ids = []

	@logutils.trace_call(logger)
	def initialize(self):
		self.__player_model = models.CompositeModel(
			pluginutils.get_player_models(self.plugin_manager, ["battle", "prebattle", "clanmembers", "friends"]))
		self.__player_model.on('added', self.__on_player_added)
		self.__player_model.on('removed', self.__on_player_removed)

		for plugin_info in self.plugin_manager.getPluginsOfCategory("UserModelProvider"):
			if plugin_info.plugin_object.has_user_model():
				self.__user_model = plugin_info.plugin_object.get_user_model()
		self.__user_model.on('added', self.__on_user_added)
		self.__user_model.on('removed', self.__on_user_removed)

		self.__inifile.set_filepath(os.path.join(Environment.find_res_mods_version_path(),
			"..", "configs", "tessu_mod", "tessu_mod_cache.ini"))
		self.__inifile.init()

	@logutils.trace_call(logger)
	def deinitialize(self):
		# TODO: clean non-paired players and users from ini-file
		pass

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "General":
			if name == "update_cache_in_replays":
				self.__enabled_in_replays = value
				self.__update_write_allowed()
			elif name == "ini_check_interval":
				self.__inifile.set_file_check_interval(value)

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
	def on_user_matched(self, user_identity, player_id):
		"""
		Implemented from UserMatchingMixin.
		"""
		self.__pairings.setdefault(str(user_identity), set()).add(str(player_id))
		self.__reserved_player_ids = reduce(lambda players, player_set: players + list(player_set), self.__pairings.values(), [])

	@logutils.trace_call(logger)
	def on_battle_replay(self):
		self.__in_replay = True
		self.__update_write_allowed()

	@logutils.trace_call(logger)
	def __on_player_added(self, player):
		self.__inifile.set("GamePlayers", player["name"].lower(), str(player["id"]))

	@logutils.trace_call(logger)
	def __on_player_removed(self, player):
		if str(player["id"]) not in self.__reserved_player_ids:
			self.__inifile.remove("GamePlayers", player["name"].lower())

	@logutils.trace_call(logger)
	def __on_user_added(self, user):
		self.__inifile.set("TeamSpeakUsers", user["name"].lower(), str(user["identity"]))

	@logutils.trace_call(logger)
	def __on_user_removed(self, user):
		if user["identity"] not in self.__pairings.keys():
			self.__inifile.remove("TeamSpeakUsers", user["name"].lower())

	@logutils.trace_call(logger)
	def __on_file_loaded(self):
		pass

	def __update_write_allowed(self):
		enabled = not self.__read_error
		if self.__in_replay:
			enabled = enabled and self.__enabled_in_replays
		self.__inifile.set_writing_enabled(enabled)

def BattleReplay_play(orig_method):
	def wrapper(self, fileName=None):
		UserCachePlugin.singleton.on_battle_replay()
		return orig_method(self, fileName)
	return wrapper
BattleReplay.play = BattleReplay_play(BattleReplay.play)
