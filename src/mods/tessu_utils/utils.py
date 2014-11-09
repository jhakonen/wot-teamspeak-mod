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
from gui import SystemMessages
from gui.WindowsManager import g_windowsManager
from messenger.storage import storage_getter
from messenger.proto.bw import find_criteria
import ResMgr
import os
import functools
import inspect
import time

def noop(*args, **kwargs):
	'''Function that does nothing. A safe default value for callback
	parameters.
	'''
	pass

def call_in_loop(secs, func):
	if not callable(secs):
		secs_value = secs
		secs = lambda: secs_value
	def wrapper(*args, **kwargs):
		func(*args, **kwargs)
		BigWorld.callback(secs(), wrapper)
	BigWorld.callback(secs(), wrapper)

def with_args(func, *args, **kwargs):
	def wrapper():
		return func(*args, **kwargs)
	return wrapper

def benchmark(func):
	def wrapper(*args, **kwargs):
		LOG_DEBUG("Function {0}() START".format(func.__name__))
		start_t = time.time()
		try:
			return func(*args, **kwargs)
		finally:
			LOG_DEBUG("Function function {0}() END: {1} s".format(func.__name__, time.time() - start_t))
	functools.update_wrapper(wrapper, func)
	return wrapper

def find_vehicle_id(matcher):
	'''Finds 'vehicle_id' using given 'matcher' function.'''
	try:
		vehicles = BigWorld.player().arena.vehicles
		for id in vehicles:
			vehicle = vehicles[id]
			if matcher(vehicle):
				return id
	except AttributeError:
		pass
	return None

def get_vehicle(vehicle_id):
	'''Returns vehicle info with matching 'vehicle_id' if available.
	Returns None if not.
	'''
	if vehicle_id is None:
		return None
	try:
		return BigWorld.player().arena.vehicles[vehicle_id]
	except AttributeError:
		pass

def get_my_name():
	'''Returns current player's nickname. None if not available.'''
	try:
		return BigWorld.player().name
	except AttributeError:
		pass

def get_my_dbid():
	'''Returns current player's account dbid. None if not available.'''
	try:
		return BigWorld.player().databaseID
	except AttributeError:
		pass

def find_prebattle_account_info(matcher):
	'''Finds player information from prebattle rosters (e.g. in practise room
	when you assign players to teams). Given 'matcher' function is used pick
	desired info. Returns None if nothing found.
	'''
	try:
		rosters = BigWorld.player().prebattle.rosters
		for roster in rosters:
			for id in rosters[roster]:
				info = rosters[roster][id]
				if matcher(info):
					return info
	except AttributeError:
		pass

def get_player_info_by_name(player_name):
	'''Extracts player information with matching 'player_name' from
	various locations. Returns 'dbid' and 'vehicle_id' in a dict if available,
	returns empty dict if nothing found.
	''' 
	player_name = player_name.lower()
	vehicle_id = find_vehicle_id(lambda v: v["name"].lower() == player_name)
	if vehicle_id is not None:
		return {
			"dbid": get_vehicle(vehicle_id)["accountDBID"],
			"vehicle_id": vehicle_id
		}
	if get_my_name().lower() == player_name:
		return {
			"dbid": get_my_dbid()
		}
	info = find_prebattle_account_info(lambda i: i["name"].lower() == player_name)
	if info:
		return {
			"dbid": info["dbID"]
		}
	return {}

def get_player_info_by_dbid(dbid):
	'''Extracts player information with matching account 'dbid' from
	various locations. Returns 'player_name' and 'vehicle_id' in a dict if
	available, returns empty dict if nothing found.
	''' 
	vehicle_id = find_vehicle_id(lambda v: v["accountDBID"] == dbid)
	if vehicle_id is not None:
		return {
			"player_name": get_vehicle(vehicle_id)["name"],
			"vehicle_id": vehicle_id
		}
	if get_my_dbid() == dbid:
		return {
			"player_name": get_my_name()
		}
	info = find_prebattle_account_info(lambda i: i["dbID"] == dbid)
	if info:
		return {
			"player_name": info["name"]
		}
	return {}

def push_system_message(message, type):
	'''Pushes given 'message' to system notification center in garage. 'type'
	is one of the SystemMessages.SM_TYPE.* constants.
	'''
	try:
		if SystemMessages.g_instance is None:
			BigWorld.callback(1, with_args(push_system_message, message, type))
		else:
			SystemMessages.pushMessage(message, type)
	except:
		LOG_CURRENT_EXCEPTION()
		return

def get_ini_dir_path():
	res = ResMgr.openSection('../paths.xml')
	sb = res['Paths']
	vals = sb.values()
	for vl in vals:
		path = vl.asString + "/scripts/client/mods/"
		if os.path.isdir(path):
			return path
	return ""

def get_players(in_battle=False, in_prebattle=False, clanmembers=False, friends=False):
	if in_battle:
		try:
			vehicles = BigWorld.player().arena.vehicles
			for id in vehicles:
				vehicle = vehicles[id]
				yield Player(vehicle["name"], vehicle["accountDBID"])
		except AttributeError:
			pass
	if in_prebattle:
		try:
			rosters = BigWorld.player().prebattle.rosters
			for roster in rosters:
				for id in rosters[roster]:
					info = rosters[roster][id]
					yield Player(info["name"], info["dbID"])
		except AttributeError:
			pass
	users_storage = storage_getter('users')()
	if clanmembers:
		for member in users_storage.getClanMembersIterator(False):
			yield Player(member.getName(), member.getID())
	if friends:
		for friend in users_storage.getList(find_criteria.BWFriendFindCriteria()):
			yield Player(friend.getName(), friend.getID())

class Player(object):

	def __init__(self, name, id):
		self._name = name
		self._id = id

	@property
	def name(self):
		return self._name

	@property
	def id(self):
		return self._id

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
			g_windowsManager.battleWindow.minimap.showActionMarker(self._vehicle_id, self._action)
		except AttributeError:
			pass

class LOG_LEVEL(object):
	DEBUG = 0
	NOTE = 1
	WARNING = 2
	ERROR = 3

CURRENT_LOG_LEVEL = LOG_LEVEL.NOTE

def LOG_DEBUG(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
		debug_utils._doLog('DEBUG', msg, args)

def LOG_NOTE(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.NOTE:
		debug_utils._doLog('NOTE', msg, args)

def LOG_WARNING(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.WARNING:
		debug_utils._doLog('WARNING', msg, args)

def LOG_ERROR(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.ERROR:
		debug_utils._doLog('ERROR', msg, args)

LOG_CURRENT_EXCEPTION = debug_utils.LOG_CURRENT_EXCEPTION

def LOG_CALL(msg=""):
	def wrap(func):
		def wrapper(*args, **kwargs):
			try:
				if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
					callargs = inspect.getcallargs(func, *args, **kwargs)
					callargs = { key: repr(callargs[key]) for key in callargs }
					debug_utils._doLog('DEBUG', func.__name__ + "():", msg.format(**callargs))
			except:
				pass
			return func(*args, **kwargs)
		functools.update_wrapper(wrapper, func)
		return wrapper
	return wrap
