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

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
	string_types = str,
	text_type = str
	binary_type = bytes
else:
	string_types = basestring,
	text_type = unicode
	binary_type = str

def to_unicode(value):
	if isinstance(value, binary_type):
		return value.decode("utf8")
	return text_type(value)

def to_bytes(value):
	if isinstance(value, text_type):
		return value.encode("utf8")
	return binary_type(value)

def demand_unicode(value):
	assert isinstance(value, text_type), "Value '%s' is not unicode string" % value
