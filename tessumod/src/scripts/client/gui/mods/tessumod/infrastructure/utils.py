# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
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

import BigWorld
import debug_utils
import ResMgr
import os
import functools
import inspect
import time
import types

import log

def noop(*args, **kwargs):
	'''Function that does nothing. A safe default value for callback
	parameters.
	'''
	pass

def with_args(func, *args, **kwargs):
	def wrapper():
		return func(*args, **kwargs)
	return wrapper

def benchmark(func):
	def wrapper(*args, **kwargs):
		log.LOG_DEBUG("Function {0}() START".format(func.__name__))
		start_t = time.time()
		try:
			return func(*args, **kwargs)
		finally:
			log.LOG_DEBUG("Function function {0}() END: {1} s".format(func.__name__, time.time() - start_t))
	functools.update_wrapper(wrapper, func)
	return wrapper

def get_resource_paths():
	res = ResMgr.openSection('../paths.xml')
	sb = res['Paths']
	vals = sb.values()
	for vl in vals:
		yield vl.asString

def find_res_mods_version_path():
	for path in get_resource_paths():
		if "res_mods" in path:
			return path
	return ""

def get_ini_dir_path():
	return os.path.join(find_res_mods_version_path(), "..", "configs", "tessu_mod")

def get_states_dir_path():
	return os.path.join(get_ini_dir_path(), "states")

def get_plugin_installer_path():
	return os.path.join(find_res_mods_version_path(), "tessumod.ts3_plugin")

def get_mod_version():
	try:
		import build_info
		return build_info.MOD_VERSION
	except ImportError:
		return "undefined"

def get_support_url():
	try:
		import build_info
		return build_info.SUPPORT_URL
	except ImportError:
		return "undefined"

class MinimapMarkersController(object):
	'''MinimapMarkersController class repeatably starts given marker 'action' every
	'interval' seconds in minimap over given 'vehicle_id', effectively creating
	continuous animation until the marker action is stopped.
	'''

	def __init__(self):
		self._running_animations = {}

	def start(self, vehicle_id, action, interval):
		'''Starts playing action marker for given 'vehicle_id'.'''
		if vehicle_id not in self._running_animations:
			self._running_animations[vehicle_id] = MinimapMarkerAnimation(
				vehicle_id, interval, action, self._on_done)
		self._running_animations[vehicle_id].start()

	def stop(self, vehicle_id):
		'''Stops playing action marker for given 'vehicle_id'.'''
		if vehicle_id in self._running_animations:
			self._running_animations[vehicle_id].stop()

	def stop_all(self):
		'''Stops all marker animations.'''
		for vehicle_id in self._running_animations:
			self._running_animations[vehicle_id].stop()

	def _on_done(self, vehicle_id):
		del self._running_animations[vehicle_id]

class MinimapMarkerAnimation(object):

	def __init__(self, vehicle_id, interval, action, on_done):
		self._interval   = interval
		self._action     = action
		self._vehicle_id = vehicle_id
		self._on_done    = on_done
		self._is_started = False
		self._is_running = False

	def start(self):
		self._is_started = True
		if not self._is_running:
			self._repeat()

	def stop(self):
		self._is_started = False

	def _repeat(self):
		self._is_running = self._is_started
		if self._is_started:
			self._updateMinimap()
			BigWorld.callback(self._interval, self._repeat)
		else:
			self._on_done(self._vehicle_id)

	def _updateMinimap(self):
		try:
			from gui.app_loader import g_appLoader
			app = g_appLoader.getDefBattleApp()
			if app:
				app.minimap.showActionMarker(self._vehicle_id, self._action)
		except AttributeError:
			log.LOG_CURRENT_EXCEPTION()

def patch_instance_method(instance, method_name, new_function):
	original_method = getattr(instance, method_name)
	new_method = types.MethodType(functools.partial(new_function, original_method), instance)
	setattr(instance, method_name, new_method)
