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

import os
import collections
import json

class KeyValueStorage(collections.MutableMapping):

	def __init__(self, storage_path):
		self.__storage_path = storage_path
		self.__cache_mapping = {}
		self.__create_storage_dir()
		self.__load_cache_from_storage_path()

	def __create_storage_dir(self):
		if not os.path.isdir(self.__storage_path):
			os.makedirs(self.__storage_path)

	def __load_cache_from_storage_path(self):
		for filename in os.listdir(self.__storage_path):
			filepath = self.__make_key_path(filename)
			if os.path.isfile(filepath):
				with open(filepath, "r") as file:
					self.__cache_mapping[filename] = json.loads(file.read())

	def __make_key_path(self, key):
		return os.path.join(self.__storage_path, key)

	def __getitem__(self, key):
		return self.__cache_mapping[key]

	def __setitem__(self, key, value):
		with open(self.__make_key_path(key), "w") as file:
			file.write(json.dumps(value))
			self.__cache_mapping[key] = value

	def __delitem__(self, key):
		del self.__cache_mapping[key]
		os.remove(self.__make_key_path(key))

	def __iter__(self):
		return iter(self.__cache_mapping)

	def __len__(self):
		return len(self.__cache_mapping)
