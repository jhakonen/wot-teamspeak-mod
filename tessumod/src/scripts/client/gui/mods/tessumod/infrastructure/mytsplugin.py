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

import struct
import mmap
import time

class _SharedMemory(object):

	NAME = None
	SIZE = 0
	ACCESS_TYPE = None

	def __init__(self):
		self.__memory = None

	def __enter__(self):
		self.open()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def is_open(self):
		return self.__memory is not None

	def open(self):
		if not self.is_open():
			self.__memory = mmap.mmap(0, self.SIZE, self.NAME, self.ACCESS_TYPE)

	def close(self):
		if self.is_open():
			self.__memory.close()
			self.__memory = None

	def read(self, byte_count):
		if self.is_open():
			return self.__memory.read(byte_count)

	def write(self, data):
		if self.is_open():
			self.__memory.write(data)

	def seek(self, pos):
		if self.is_open():
			self.__memory.seek(pos)

class InfoAPI(_SharedMemory):

	NAME = "TessuModTSPluginInfo"
	SIZE = 1
	ACCESS_TYPE = mmap.ACCESS_READ

	def get_api_version(self):
		self.seek(0)
		return struct.unpack("=B", self.read(1))[0]

class PositionalDataAPI(_SharedMemory):

	NAME = "TessuModTSPlugin3dAudio"
	SIZE = 1024
	ACCESS_TYPE = mmap.ACCESS_WRITE

	def __init__(self):
		_SharedMemory.__init__(self)
		self.__previous_camera_position = None
		self.__previous_camera_direction = None
		self.__previous_positions = None
		self.__previous_timestamp = None

	def set_data(self, camera_position, camera_direction, positions):
		timestamp = int(time.time())
		if self.__has_data_updated(timestamp, camera_position, camera_direction, positions):
			self.seek(0)
			self.write(struct.pack("I", timestamp))
			self.write(self.__pack_float_vector(camera_position))
			self.write(self.__pack_float_vector(camera_direction))
			self.write(struct.pack("B", len(positions)))
			for client_id, position in positions.iteritems():
				self.write(struct.pack("h", client_id))
				self.write(self.__pack_float_vector(position))
			self.__previous_timestamp = timestamp
			self.__previous_camera_position = camera_position
			self.__previous_camera_direction = camera_direction
			self.__previous_positions = positions

	def __has_data_updated(self, timestamp, camera_position, camera_direction, positions):
		return (
			self.__previous_timestamp != timestamp
			or self.__previous_camera_position != camera_position
			or self.__previous_camera_direction != camera_direction
			or self.__previous_positions != positions
		)

	def __pack_float_vector(self, vector):
		return struct.pack("3f", vector[0], vector[1], vector[2])
