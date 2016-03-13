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

from timer import TimerMixin
from eventemitter import EventEmitterMixin
from ..thirdparty.iniparse import ConfigParser

import csv
import io
import os
import re

class INIFile(TimerMixin, EventEmitterMixin):

	def __init__(self, default_contents):
		super(INIFile, self).__init__()
		self.__default_contents = default_contents
		self.__parser = ConfigParser()
		self.__filepath = None
		self.__writing_enabled = True
		self.__write_needed = False
		self.reset_last_modified()

	def set_filepath(self, filepath):
		self.__filepath = filepath

	def get_filepath(self):
		return self.__filepath

	def reset_last_modified(self):
		self.__load_time = 0

	def set_file_check_interval(self, interval):
		self.on_timeout(interval, self.__sync, repeat=True)

	def set_writing_enabled(self, enabled):
		self.__writing_enabled = enabled

	def init(self):
		self.__create_filedir()
		self.__write_default_file()
		self.__sync()

	def get_int(self, section, option):
		return self.__parser.getint(section, option)

	def get_float(self, section, option):
		return self.__parser.getfloat(section, option)

	def get_boolean(self, section, option):
		return self.__parser.getboolean(section, option)

	def get_string(self, section, option):
		return self.__parser.get(section, option)

	def get_list(self, section, option):
		items = []
		for row in csv.reader([self.__parser.get(section, option)]):
			for item in row:
				items.append(item)
		return items

	def get_dict(self, section, key_getter):
		return {option: key_getter(section, option) for option in self.__parser.options(section)}

	def set(self, section, option, value):
		value = str(value)
		if self.__parser.has_option(section, option):
			if self.__parser.get(section, option) == value:
				return
		self.__parser.set(section, self.__ini_escape(option), value)
		self.__write_needed = True

	def set_list(self, section, option, value):
		bytes_io = io.BytesIO()
		csv_out = csv.writer(bytes_io)
		csv_out.writerow(value)
		value = bytes_io.getvalue().rstrip("\r\n")
		self.set(section, option, value)

	def add_section(self, section):
		self.__parser.add_section(section)
		self.__write_needed = True

	def remove(self, section, option):
		self.__parser.remove_option(section, option)
		self.__write_needed = True

	def __create_filedir(self):
		ini_dirpath = os.path.dirname(self.__filepath)
		if not os.path.exists(ini_dirpath):
			os.makedirs(ini_dirpath)

	def __write_default_file(self):
		if not os.path.isfile(self.__filepath):
			with open(self.__filepath, "w") as f:
				f.write(self.__default_contents)

	def __sync(self):
		if self.__is_modified():
			self.__read_file()
		if self.__writing_enabled and self.__write_needed:
			self.__write_file()

	def __is_modified(self):
		return self.__load_time < self.__get_modified_time()

	def __get_modified_time(self):
		return os.path.getmtime(self.__filepath)

	def __read_file(self):
		self.emit("file-load-before")
		if self.__parser.read(self.__filepath):
			self.__load_time = self.__get_modified_time()
			self.emit("file-load-after")
		else:
			log.LOG_ERROR("Failed to parse ini file '{0}'".format(self.__filepath))

	def __write_file(self):
		with open(self.__filepath, "w") as file:
			self.__parser.write(file)

	def __ini_escape(self, value):
		return re.sub(r"[\[\]=:\\]", "*", value)
