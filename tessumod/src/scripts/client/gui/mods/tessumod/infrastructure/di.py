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

__provider = {}

def provide(name, obj):
	__provider[name] = obj

def get_provided(name):
	return __provider[name]

def inject(name):
	def injector(cls):
		if not hasattr(cls, "__getattr__"):
			def __getattr__(self, name):
				assert name in self.__injections, "No such @inject provided as {}".format(name)
				return self.__injections[name]
			setattr(cls, "__getattr__", __getattr__)
		return cls
	return injector

def install_provider(obj):
	try:
		obj.__injections = __provider
	except AttributeError:
		pass
