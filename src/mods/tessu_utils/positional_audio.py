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
import os
import BigWorld
from utils import RepeatTimer
import utils
import time

ENTITY_REFRESH_TIMEOUT = 1
TS_UPDATE_TIMEOUT = 0.1

class PositionalAudio(object):

	def __init__(self, ts_users, user_cache):
		self._ts_users = ts_users
		self._user_cache = user_cache
		self._player_vehicle_ids = {}
		self._vehicle_positions = {}
		self._data_updated = False
		self._camera_position = None
		self._camera_direction = None
		self._shared_memory = None
		self._audio_backend = 0

		ts_users.on_added     += self.on_ts_users_changed
		ts_users.on_removed   += self.on_ts_users_changed
		ts_users.on_modified  += self.on_ts_users_changed
		user_cache.on_updated += self.on_user_cache_updated

		self._entity_positions_timer = RepeatTimer(ENTITY_REFRESH_TIMEOUT)
		self._entity_positions_timer.on_timeout += self.on_refresh_entity_positions

		self._ts_update_timer = RepeatTimer(TS_UPDATE_TIMEOUT)
		self._ts_update_timer.on_timeout += self.on_update_to_ts

	def on_become_player(self):
		'''Called when BigWorld.player() object becomes available at start
		of battle.
		'''
		self._shared_memory = mmap.mmap(0, 1024, "TessuModTSPlugin3dAudio", mmap.ACCESS_WRITE)
		self._vehicle_positions.clear()
		self._player_vehicle_ids.clear()
		self._data_updated = True
		self._arena().onNewVehicleListReceived += self.on_arena_vehicles_updated
		self._arena().onVehicleAdded           += self.on_arena_vehicles_updated
		self._arena().onVehicleUpdated         += self.on_arena_vehicles_updated
		self._arena().onVehicleKilled          += self.on_arena_vehicles_updated
		self._arena().onPositionsUpdated       += self.on_arena_positions_changed
		self._entity_positions_timer.start()
		self._ts_update_timer.start()
		self.on_update_to_ts(forced=True)

	def on_become_nonplayer(self):
		'''Called when BigWorld.player() object is removed at end of battle.
		'''
		self._entity_positions_timer.stop()
		self._ts_update_timer.stop()
		self._player_vehicle_ids.clear()
		self._vehicle_positions.clear()
		self.on_update_to_ts(forced=True)
		if self._shared_memory:
			self._shared_memory.close()
			self._shared_memory = None

	def on_arena_vehicles_updated(self, *args, **kwargs):
		'''Called when vehicles in the arena are updated.

		Builds a lookup table for converting player ID to vehicle ID.
		'''
		self._player_vehicle_ids.clear()
		for vehicle_id in self._arena().vehicles:
			vehicle = self._arena().vehicles[vehicle_id]
			if vehicle["isAlive"]:
				player_id = vehicle["accountDBID"]
				self._player_vehicle_ids[player_id] = vehicle_id
		self._data_updated = True

	def on_arena_positions_changed(self):
		'''Called when vehicle positions in the arena are updated.

		Seems to be only those vehicles which are close by. Updates a lookup
		table for converting vehicle ID to position.
		'''
		for vehicle_id in self._arena().positions:
			self._vehicle_positions[vehicle_id] = _Vector(*self._arena().positions[vehicle_id])
		self._data_updated = True

	def on_refresh_entity_positions(self):
		'''Called every ENTITY_REFRESH_TIMEOUT intervals.

		Updates positions of ALL vehicles in the arena to a loopkup table for
		converting vehicle ID to position.
		'''
		for vehicle_id in self._arena().vehicles:
			if BigWorld.entities.has_key(vehicle_id):
				self._vehicle_positions[vehicle_id] = BigWorld.entities[vehicle_id].position
				self._data_updated = True

	def on_ts_users_changed(self, *args, **kwargs):
		self._data_updated = True

	def on_user_cache_updated(self):
		self._data_updated = True

	def on_update_to_ts(self, forced=False):
		if self._shared_memory and (forced or self._data_updated or self._is_camera_updated()):
			self._data_updated = False
			camera = BigWorld.camera()
			self._camera_position = camera.position
			self._camera_direction = camera.direction

			self._shared_memory.seek(0)
			data = _DataVersion()
			data.deserialize(self._shared_memory)
			if data.version == 1:
				data = _DataV1()
				data.audio_backend = self._audio_backend
				data.camera_position = camera.position
				data.camera_direction = camera.direction
				data.client_positions = self._get_data_entries()
				data.serialize(self._shared_memory)

	def set_audio_backend(self, backend):
		if self._audio_backend != backend:
			self._audio_backend = backend
			self._data_updated = True

	def _get_data_entries(self):
		entries = []
		for user in self._ts_users.itervalues():
			position = self._get_vehicle_id_position(self._player_id_to_vehicle_id(self._ts_user_to_player_id(user)))
			if position:
				entries.append((user.client_id, position))
		return entries

	def _ts_user_to_player_id(self, ts_user):
		return next(self._user_cache.get_paired_player_ids(ts_user.unique_id), None)

	def _player_id_to_vehicle_id(self, player_id):
		return self._player_vehicle_ids.get(player_id)

	def _get_vehicle_id_position(self, vehicle_id):
		return self._vehicle_positions.get(vehicle_id)

	def _arena(self):
		return BigWorld.player().arena

	def _is_camera_updated(self):
		camera = BigWorld.camera()
		if not camera:
			return False
		return self._camera_position != camera.position or self._camera_direction != camera.direction

class _DataVersion(object):

	def __init__(self):
		self.version = 0

	def deserialize(self, source):
		self.version = struct.unpack("H", source.read(2))[0]

class _DataV1(object):

	def __init__(self):
		self.audio_backend = 0
		self.camera_position = None
		self.camera_direction = None
		self.client_positions = {}

	def serialize(self, destination):
		destination.write(struct.pack("I", int(time.time())))
		destination.write(struct.pack("B", self.audio_backend))
		destination.write(self._pack_float_vector(self.camera_position))
		destination.write(self._pack_float_vector(self.camera_direction))
		destination.write(struct.pack("B", len(self.client_positions)))
		for client_id, position in self.client_positions:
			destination.write(struct.pack("h", client_id))
			destination.write(self._pack_float_vector(position))

	def _pack_float_vector(self, vector):
		return struct.pack("3f", vector.x, vector.y, vector.z)

class _Vector(object):

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z
