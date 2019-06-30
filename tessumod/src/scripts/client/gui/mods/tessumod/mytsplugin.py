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
import platform
import os

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

	def open(self):
		if self.__memory:
			return
		if platform.system() == "Linux":
			# For a test suite running on Linux, not for actual communication
			# with the plugin
			file_path = os.path.join("/tmp", self.NAME)
			if not os.path.exists(file_path):
				with open(file_path, "wb") as file:
					file.write('\x00' * self.SIZE)
			self.__memory = open(file_path, "r+b", 0)
		else:
			# Used when loaded into WoT on Windows (or Linux over WINE)
			self.__memory = mmap.mmap(0, self.SIZE, self.NAME, self.ACCESS_TYPE)

	def close(self):
		if self.__memory:
			self.__memory.close()
			self.__memory = None

	def read(self, byte_count):
		if self.__memory:
			return self.__memory.read(byte_count)

	def write(self, data):
		if self.__memory:
			self.__memory.write(data)

	def seek(self, pos):
		if self.__memory:
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

	def set_data(self, data):
		self.seek(0)
		self.write(struct.pack("I", int(time.time())))
		self.write(self.__pack_float_vector(data.camera_position))
		self.write(self.__pack_float_vector(data.camera_direction))
		self.write(struct.pack("B", len(data.client_positions)))
		for client_id, position in data.client_positions:
			self.write(struct.pack("h", client_id))
			self.write(self.__pack_float_vector(position))

	def __pack_float_vector(self, vector):
		return struct.pack("3f", vector.x, vector.y, vector.z)

class PositionalData(object):

	def __init__(self):
		self.camera_position = None
		self.camera_direction = None
		self.client_positions = {}

	def __repr__(self):
		return "PositionalData(camera_position=%s, camera_direction=%s, client_positions=%s)" % (
			self.camera_position,
			self.camera_direction,
			self.client_positions
		)

class Vector(object):

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

	def __repr__(self):
		return "Vector(%d, %d, %d)" % (self.x, self.y, self.z)
