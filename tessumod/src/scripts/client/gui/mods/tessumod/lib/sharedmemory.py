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

import mmap

ACCESS_READ = mmap.ACCESS_READ
ACCESS_WRITE = mmap.ACCESS_WRITE

class SharedMemory(object):

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
