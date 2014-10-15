# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
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

import Event
import mmap
import struct

ENTITY_REFRESH_TIMEOUT = 5
TS_UPDATE_TIMEOUT = 0.1

def init(big_world, player_events, ts_users, user_cache):

	context = Context()
	context.player_vehicle_ids = {}
	context.vehicle_positions = {}
	context.data_updated = False
	context.camera_position = None
	context.camera_direction = None

	def on_become_player():
		'''Called when BigWorld.player() object becomes available at start
		of battle.
		'''
		context.vehicle_positions.clear()
		context.player_vehicle_ids.clear()
		context.data_updated = True
		arena().onNewVehicleListReceived += on_arena_vehicles_updated
		arena().onVehicleAdded           += on_arena_vehicles_updated
		arena().onVehicleUpdated         += on_arena_vehicles_updated
		arena().onVehicleKilled          += on_arena_vehicles_updated
		arena().onPositionsUpdated       += on_arena_positions_changed
		entity_positions_timer.start()
		ts_update_timer.start()

	def on_become_nonplayer():
		'''Called when BigWorld.player() object is removed at end of battle.
		'''
		entity_positions_timer.stop()
		ts_update_timer.stop()
		on_update_to_ts()

	def on_arena_vehicles_updated(*args, **kwargs):
		'''Called when vehicles in the arena are updated.

		Builds a lookup table for converting player ID to vehicle ID.
		'''
		context.player_vehicle_ids.clear()
		for vehicle_id in arena().vehicles:
			vehicle = arena().vehicles[vehicle_id]
			if vehicle["isAlive"]:
				player_id = vehicle["accountDBID"]
				context.player_vehicle_ids[player_id] = vehicle_id
		context.data_updated = True

	def on_arena_positions_changed():
		'''Called when vehicle positions in the arena are updated.

		Seems to be only those vehicles which are close by. Updates a lookup
		table for converting vehicle ID to position.
		'''
		for vehicle_id in arena().positions:
			context.vehicle_positions[vehicle_id] = arena().positions[vehicle_id]
		context.data_updated = True

	def on_refresh_entity_positions():
		'''Called every ENTITY_REFRESH_TIMEOUT intervals.

		Updates positions of ALL vehicles in the arena to a loopkup table for
		converting vehicle ID to position.
		'''
		for vehicle_id in arena().vehicles:
			if big_world.entities.has_key(vehicle_id):
				context.vehicle_positions[vehicle_id] = big_world.entities[vehicle_id].position
				context.data_updated = True

	def on_ts_users_changed(*args, **kwargs):
		context.data_updated = True

	def on_user_cache_updated():
		context.data_updated = True

	def get_data_entries():
		entries = []
		for user in ts_users.itervalues():
			position = get_vehicle_id_position(player_id_to_vehicle_id(ts_user_to_player_id(user)))
			if position:
				entries.append((user.client_id, position))
		return entries

	def ts_user_to_player_id(ts_user):
		return next(user_cache.get_paired_player_ids(ts_user.unique_id), None)

	def player_id_to_vehicle_id(player_id):
		return context.player_vehicle_ids.get(player_id)

	def get_vehicle_id_position(vehicle_id):
		return context.vehicle_positions.get(vehicle_id)

	def arena():
		return big_world.player().arena

	def on_update_to_ts():
		if (context.data_updated or is_camera_updated()) and len(ts_users):
			context.data_updated = False
			data = []
			shmem = None
			camera = big_world.camera()
			data.append(pack_float_vector(camera.position))
			data.append(struct.pack("3f", *camera.direction))
			entries = get_data_entries()
			data.append(struct.pack("B", len(entries)))
			for client_id, position in entries:
				data.append(struct.pack("h", client_id))
				data.append(pack_float_vector(position))
			data = "".join(data)
			try:
				shmem = mmap.mmap(0, 1024, "TessuModTSPlugin3dAudio", mmap.ACCESS_WRITE)
				shmem.seek(2) # skip version
				shmem.write(data)
			finally:
				if shmem:
					shmem.close()

	def is_camera_updated():
		camera = big_world.camera()
		if not camera:
			return False
		return context.camera_position != camera.position or context.camera_direction != camera.direction

	def pack_float_vector(vector):
		return struct.pack("3f", vector.x, vector.y, vector.z)

	player_events.onAvatarBecomePlayer    += on_become_player
	player_events.onAvatarBecomeNonPlayer += on_become_nonplayer
	ts_users.on_added    += on_ts_users_changed
	ts_users.on_removed  += on_ts_users_changed
	ts_users.on_modified += on_ts_users_changed
	user_cache.on_updated += on_user_cache_updated

	entity_positions_timer = RepeatTimer(big_world, ENTITY_REFRESH_TIMEOUT)
	entity_positions_timer.on_timeout += on_refresh_entity_positions

	ts_update_timer = RepeatTimer(big_world, TS_UPDATE_TIMEOUT)
	ts_update_timer.on_timeout += on_update_to_ts

class Context(object):
	pass

class RepeatTimer(object):

	def __init__(self, big_world, timeout):
		self._big_world = big_world
		self._timeout   = timeout
		self._stopped   = True
		self.on_timeout = Event.Event()

	def start(self):
		self._stopped = False
		self._do_call()

	def stop(self):
		self._stopped = True

	def _do_call(self):
		if not self._stopped:
			self._big_world.callback(self._timeout, self._on_timeout)

	def _on_timeout(self):
		if not self._stopped:
			self.on_timeout()
			self._do_call()
