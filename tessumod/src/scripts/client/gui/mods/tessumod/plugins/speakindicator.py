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

from gui.mods.tessumod import plugintypes, logutils, models, pluginutils
from VOIP.VOIPManager import VOIPManager
from messenger.proto.events import g_messengerEvents
from PlayerEvents import g_playerEvents
from constants import ARENA_PERIOD

logger = logutils.logger.getChild("speakindicator")

class SpeakIndicatorPlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin):
	"""
	This plugin renders speech indicator notifications in game when a user
	matched a player speaks. The indicator is shown as a green ripple effect
	under player's name. There is also a speaker icon shown over tanks in battle.
	"""

	singleton = None

	def __init__(self):
		super(SpeakIndicatorPlugin, self).__init__()
		SpeakIndicatorPlugin.singleton = self
		self.__filter_model = None
		self.__enabled = None
		self.__self_enabled = None

	@logutils.trace_call(logger)
	def initialize(self):
		self.__filter_model = models.FilterModel(pluginutils.get_player_model(self.plugin_manager, ["battle", "prebattle", "voice"]))
		self.__filter_model.add_filter(lambda item: self.__enabled)
		self.__filter_model.add_filter(lambda item: "speaking" in item)
		self.__filter_model.add_filter(lambda item: self.__self_enabled or not item["is_me"])

		self.__filter_model.on("added", self.__on_filter_model_added)
		self.__filter_model.on("modified", self.__on_filter_model_modified)
		self.__filter_model.on("removed", self.__on_filter_model_removed)

		g_playerEvents.onArenaPeriodChange += self.__on_arena_period_change

	@logutils.trace_call(logger)
	def deinitialize(self):
		g_playerEvents.onArenaPeriodChange -= self.__on_arena_period_change
		self.__filter_model = None

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "VoiceChatNotifications":
			if name == "enabled":
				self.__enabled = value
				self.__filter_model.invalidate()
			if name == "self_enabled":
				self.__self_enabled = value
				self.__filter_model.invalidate()

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsMixin.
		"""
		return {
			"VoiceChatNotifications": {
				"help": "",
				"variables": [
					{
						"name": "enabled",
						"default": True,
						"help": "Enable or disable speak notifications in player panels and showing of speaker icons above tanks"
					},
					{
						"name": "self_enabled",
						"default": True,
						"help": "Enable or disable notifications when you're speaking"
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def is_player_id_speaking(self, id):
		player = self.__filter_model.get(int(id), {})
		if player:
			logger.debug("is_player_id_speaking: User %s is %s", player["name"], "speaking" if player["speaking"] else "not speaking")
			return player["speaking"]
		return None

	@logutils.trace_call(logger)
	def __on_filter_model_added(self, new_player):
		if new_player["speaking"]:
			g_messengerEvents.voip.onPlayerSpeaking(new_player["id"], True)

	@logutils.trace_call(logger)
	def __on_filter_model_modified(self, old_player, new_player):
		if new_player["speaking"] != old_player["speaking"]:
			g_messengerEvents.voip.onPlayerSpeaking(new_player["id"], new_player["speaking"])

	@logutils.trace_call(logger)
	def __on_filter_model_removed(self, old_player):
		if old_player["speaking"]:
			g_messengerEvents.voip.onPlayerSpeaking(old_player["id"], False)

	@logutils.trace_call(logger)
	def __on_arena_period_change(self, period, *args, **kwargs):
		# WoT 0.9.15.1.1 has a bug where speech indicator is not shown in
		# player panel at battle's start. Vehicles do have speaker icon in OTM,
		# it is just the panels which don't update. As such try to overcome
		# that by explictly notifying current speak state as soon as possible.
		if period == ARENA_PERIOD.PREBATTLE:
			for player in self.__filter_model.itervalues():
				g_messengerEvents.voip.onPlayerSpeaking(player["id"], player["speaking"])

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		speaking = SpeakIndicatorPlugin.singleton.is_player_id_speaking(dbid)
		if speaking is None:
			return orig_method(self, dbid)
		return speaking
	return wrapper
VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIPManager.isParticipantTalking)
