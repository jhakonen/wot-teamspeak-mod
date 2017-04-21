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

from gui.mods.tessumod import plugintypes
from gui.mods.tessumod.lib import logutils
from gui.mods.tessumod.lib.pluginmanager import Plugin
from gui.mods.tessumod.models import g_player_model, PlayerItem

from PlayerEvents import g_playerEvents
import BigWorld

logger = logutils.logger.getChild("playersinbattle")

class PlayersInBattlePlugin(Plugin):
	"""
	This plugin provides a model for other plugins which contains players in battle.
	"""

	NS = "battle"

	def __init__(self):
		super(PlayersInBattlePlugin, self).__init__()
		self.__killed_vehicles = set()
		self.__players = {}
		self.__my_vehicle_id = None
		g_player_model.add_namespace(self.NS)

	@property
	def arena(self):
		arena = BigWorld.player().arena
		if not arena:
			raise RuntimeError("Arena does not exist")
		return arena

	@logutils.trace_call(logger)
	def initialize(self):
		g_playerEvents.onAvatarBecomePlayer += self.__on_avatar_become_player
		g_playerEvents.onAvatarBecomeNonPlayer += self.__on_avatar_become_non_player
		g_playerEvents.onAvatarReady += self.__on_avatar_ready

	@logutils.trace_call(logger)
	def deinitialize(self):
		g_playerEvents.onAvatarBecomePlayer -= self.__on_avatar_become_player
		g_playerEvents.onAvatarBecomeNonPlayer -= self.__on_avatar_become_non_player
		g_playerEvents.onAvatarReady -= self.__on_avatar_ready

	def __on_avatar_become_player(self):
		self.arena.onNewVehicleListReceived += self.__on_new_vehicle_list_received
		self.arena.onVehicleAdded += self.__on_vehicle_added
		self.arena.onVehicleKilled += self.__on_vehicle_killed

	def __on_avatar_become_non_player(self):
		g_player_model.clear(self.NS)

	def __on_avatar_ready(self):
		for vehicle_id, vehicle in self.arena.vehicles.iteritems():
			g_player_model.set(self.NS, self.__vehicle_to_player(vehicle_id, vehicle))

	def __on_new_vehicle_list_received(self):
		players = [self.__vehicle_to_player(vehicle_id, vehicle) for vehicle_id, vehicle in self.arena.vehicles.iteritems()]
		g_player_model.set_all(self.NS, players)

	def __on_vehicle_added(self, vehicle_id):
		g_player_model.set(self.NS, self.__vehicle_to_player(vehicle_id, self.arena.vehicles[vehicle_id]))

	def __on_vehicle_killed(self, vehicle_id, *args, **kwargs):
		self.__killed_vehicles.add(int(vehicle_id))
		g_player_model.set(self.NS, self.__vehicle_to_player(vehicle_id, self.arena.vehicles[vehicle_id]))

	def __vehicle_to_player(self, vehicle_id, vehicle):
		return PlayerItem(
			id         = int(vehicle["accountDBID"]),
			name       = str(vehicle["name"]),
			vehicle_id = int(vehicle_id),
			is_alive   = int(vehicle_id) not in self.__killed_vehicles
		)
