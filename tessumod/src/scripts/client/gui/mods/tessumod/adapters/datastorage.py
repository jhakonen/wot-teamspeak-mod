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

import copy
import os
import json

class DataStorageAdapter(object):

	def __init__(self):
		self.__storage_path = None
		self.__cache_mapping = {}

	def init(self, data_dirpath):
		self.__storage_path = data_dirpath
		if not os.path.isdir(self.__storage_path):
			os.makedirs(self.__storage_path)
		for filename in os.listdir(self.__storage_path):
			filepath = self.__make_key_path(filename)
			if os.path.isfile(filepath):
				with open(filepath, "r") as file:
					self.__cache_mapping[filename] = json.loads(file.read())

	def get(self, name):
		return self.__cache_mapping.get(name)

	def set(self, name, value):
		with open(self.__make_key_path(name), "w") as file:
			file.write(json.dumps(value))
			self.__cache_mapping[name] = value
		return value

	def __make_key_path(self, name):
		return os.path.join(self.__storage_path, name)
