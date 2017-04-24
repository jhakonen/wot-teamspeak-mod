# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

from functools import partial

_hooks = []

def install_hooks():
	for hook in _hooks:
		hook.install()

def uninstall_hooks():
	for hook in _hooks:
		hook.uninstall()
	del _hooks[:]

def CALL_BEFORE(original_func, hook_func, *args, **kwargs):
	hook_func(*args, **kwargs)
	return original_func(*args, **kwargs)

def CALL_WITH_ORIGINAL(original_func, hook_func, *args, **kwargs):
	return hook_func(original_func, *args, **kwargs)

def hook_method(cls, method_name, call_style=CALL_BEFORE):
	def hook_receiver(hook_function):
		_hooks.append(_MethodHook(cls, method_name, call_style, hook_function))
		return hook_function
	return hook_receiver

class _MethodHook(object):

	def __init__(self, method_cls, method_name, call_style, hook_function):
		self.__method_cls = method_cls
		self.__method_name = method_name
		self.__call_style = call_style
		self.__hook_function = hook_function
		self.__original_function = None

	def install(self):
		self.__original_function = getattr(self.__method_cls, self.__method_name)
		def hook(*args, **kwargs):
			return self.__call_style(self.__original_function, self.__hook_function, *args, **kwargs)
		setattr(self.__method_cls, self.__method_name, hook)

	def uninstall(self):
		setattr(self.__method_cls, self.__method_name, self.__original_function)
