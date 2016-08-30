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
from gui.mods.tessumod.infrastructure import gameapi
from PlayerEvents import g_playerEvents
import BigWorld

logger = logutils.logger.getChild("playersinbattle")

class PlayersInBattlePlugin(plugintypes.ModPlugin):
	"""
	This plugin sends player added/modified/removed events to other plugins
	while in battle.

	Calls following methods from "PlayerNotifications" category:
	 * on_player_added:    At start of battle, and when enemies pop out from
	                       fog of war (e.g. CW)
	 * on_player_modified: When someone dies
	 * on_player_removed:  At end of battle
	"""

	def __init__(self):
		super(PlayersInBattlePlugin, self).__init__()
		self.__battle_model = models.PlayerModel()
		self.__battle_model.on("added", self.__on_model_added)
		self.__battle_model.on("modified", self.__on_model_modified)
		self.__battle_model.on("removed", self.__on_model_removed)
		self.__players = {}

	@property
	def arena(self):
		arena = BigWorld.player().arena
		if not arena:
			raise RuntimeError("Arena does not exist")
		return arena

	@logutils.trace_call(logger)
	def initialize(self):
		g_playerEvents.onAvatarBecomePlayer += self.on_avatar_become_player
		g_playerEvents.onAvatarBecomeNonPlayer += self.on_avatar_become_non_player

	@logutils.trace_call(logger)
	def deinitialize(self):
		g_playerEvents.onAvatarBecomePlayer -= self.on_avatar_become_player
		g_playerEvents.onAvatarBecomeNonPlayer -= self.on_avatar_become_non_player

	def on_avatar_become_player(self):
		self.arena.onNewVehicleListReceived += self.on_new_vehicle_list_received
		self.arena.onVehicleAdded += self.on_vehicle_added
		self.arena.onVehicleKilled += self.on_vehicle_killed

	def on_avatar_become_non_player(self):
		for id in self.__battle_model.keys():
			self.__battle_model.remove(id)

	def on_new_vehicle_list_received(self):
		for id in self.__battle_model:
			self.__battle_model.remove(id)
		for vehicle_id, vehicle in self.arena.vehicles.iteritems():
			self.__battle_model.set(self.__vehicle_to_player(vehicle_id, vehicle))

	def on_vehicle_added(self, vehicle_id):
		self.__battle_model.set(self.__vehicle_to_player(vehicle_id, self.arena.vehicles[vehicle_id]))

	def on_vehicle_killed(self, vehicle_id, *args, **kwargs):
		id = int(self.arena.vehicles[vehicle_id]["accountDBID"])
		self.__battle_model.set(dict(self.__battle_model[id], is_alive=False))

	def __vehicle_to_player(self, vehicle_id, vehicle):
		return dict(
			name       = str(vehicle["name"]),
			id         = int(vehicle["accountDBID"]),
			vehicle_id = int(vehicle_id),
			is_alive   = True,
			is_me      = int(vehicle["accountDBID"]) == int(gameapi.Player.get_my_dbid())
		)

	def __on_model_added(self, new_item):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("PlayerNotifications"):
			plugin_info.plugin_object.on_player_added("battle", dict(new_item))

	def __on_model_modified(self, old_item, new_item):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("PlayerNotifications"):
			plugin_info.plugin_object.on_player_modified("battle", dict(new_item))

	def __on_model_removed(self, old_item):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("PlayerNotifications"):
			plugin_info.plugin_object.on_player_removed("battle", dict(old_item))
