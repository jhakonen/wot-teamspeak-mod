# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2019  Janne Hakonen
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

try:
	# Python 2 (game)
	from ConfigParser import ConfigParser as ParentConfigParser
except ImportError:
	# Python 3 (test suite)
	from configparser import ConfigParser as ParentConfigParser

from .py3compat import demand_unicode, to_unicode

class ConfigParser(ParentConfigParser):

	def options(self, section):
		demand_unicode(section)
		return ParentConfigParser.options(self, section)

	def add_section(self, section):
		demand_unicode(section)
		ParentConfigParser.add_section(self, section)

	def has_section(self, section):
		demand_unicode(section)
		return ParentConfigParser.has_section(self, section)

	def get(self, section, option, *args, **kwargs):
		demand_unicode(section)
		demand_unicode(option)
		return to_unicode(ParentConfigParser.get(self, section, option, *args, **kwargs))

	def getint(self, section, option):
		demand_unicode(section)
		demand_unicode(option)
		return ParentConfigParser.getint(self, section, option)

	def getfloat(self, section, option):
		demand_unicode(section)
		demand_unicode(option)
		return ParentConfigParser.getfloat(self, section, option)

	def getboolean(self, section, option):
		demand_unicode(section)
		demand_unicode(option)
		return ParentConfigParser.getboolean(self, section, option)

	def items(self, section, *args, **kwargs):
		demand_unicode(section)
		return [(to_unicode(key), to_unicode(value)) for key, value in ParentConfigParser.items(self, section, *args, **kwargs)]

	def set(self, section, option, value):
		demand_unicode(section)
		demand_unicode(option)
		demand_unicode(value)
		ParentConfigParser.set(self, section, option, value)

	def write(self, fp):
		"""Copied from Python 2.7 and altered to properly write unicode."""
		if self._defaults:
			fp.write(u"[%s]\n" % DEFAULTSECT)
			for (key, value) in self._defaults.items():
				fp.write(u"%s = %s\n" % (to_unicode(key), to_unicode(value).replace(u'\n', u'\n\t')))
			fp.write("\n")
		for section in self._sections:
			fp.write(u"[%s]\n" % section)
			for (key, value) in self._sections[section].items():
				if key == "__name__":
					continue
				if (value is not None) or (self._optcre == self.OPTCRE):
					key = u" = ".join((to_unicode(key), to_unicode(value).replace('\n', '\n\t')))
				fp.write(u"%s\n" % to_unicode(key))
			fp.write(u"\n")

	def remove_option(self, section, option):
		demand_unicode(section)
		demand_unicode(option)
		return ParentConfigParser.remove_option(self, section, option)

	def remove_section(self, section):
		demand_unicode(section)
		return ParentConfigParser.remove_section(self, section)

	def optionxform(self, option):
		demand_unicode(option)
		return ParentConfigParser.optionxform(self, option)
