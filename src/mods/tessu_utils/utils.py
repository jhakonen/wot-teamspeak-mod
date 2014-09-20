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
import threading
from debug_utils import LOG_CURRENT_EXCEPTION
from gui import SystemMessages
from gui.WindowsManager import g_windowsManager
	
def call_in_loop(secs, func):
	def wrapper(*args, **kwargs):
		func(*args, **kwargs)
		BigWorld.callback(secs, wrapper)
	BigWorld.callback(secs, wrapper)

def with_args(func, *args, **kwargs):
	def wrapper():
		return func(*args, **kwargs)
	return wrapper

class ThreadCaller(object):

	def __init__(self):
		self.calls = []

	def call(self, func, callback):
		call = ThreadCall(func, callback)
		self.calls.append(call)
		call.start()

	def tick(self):
		for call in self.calls:
			done = call.check()
			if done:
				self.calls.remove(call)

class ThreadCall(object):
	def __init__(self, func, callback):
		self._finished = threading.Event()
		self._func = func
		self._result_callback = callback
		self._error = None
		self._result = None
		self._thread = threading.Thread(target=self._target)

	def start(self):
		self._thread.start()

	def check(self):
		if self._finished.is_set():
			try:
				self._result_callback(self._error, self._result)
			except:
				LOG_CURRENT_EXCEPTION()
			return True
		return False

	def _target(self):
		try:
			self._result = self._func()
		except Exception as e:
			self._error = e
		self._finished.set()

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

import time

class MarkerRepeater(object):
	'''MarkerRepeater class repeatably starts given marker 'action' every
	'interval' seconds in minimap over given 'vehicle_id', effectively creating
	continuous animation until the marker action is stopped.
	'''

	def __init__(self, interval, action):
		self._interval = interval
		self._action = action
		self._running_ids = set()

	def start(self, vehicle_id):
		'''Starts playing action marker for given 'vehicle_id'.'''
		if vehicle_id not in self._running_ids:
			self._running_ids.add(vehicle_id)
			self._repeat(vehicle_id)

	def stop(self, vehicle_id):
		'''Stops playing action marker for given 'vehicle_id'.'''
		try:
			self._running_ids.remove(vehicle_id)
		except KeyError:
			pass

	def stop_all(self):
		'''Stops all marker animations.'''
		self._running_ids.clear()

	def _repeat(self, vehicle_id):
		try:
			if vehicle_id in self._running_ids:
				g_windowsManager.battleWindow.minimap.showActionMarker(vehicle_id, self._action)
				BigWorld.callback(self._interval, with_args(self._repeat, vehicle_id))
		except AttributeError:
			pass
