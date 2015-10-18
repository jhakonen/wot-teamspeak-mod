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
from messenger.storage import storage_getter
from messenger.proto.shared_find_criteria import FriendsFindCriteria
import ResMgr
import Event
import os
import functools
import inspect
import time
import types

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
		try:
			return get_vehicle(BigWorld.player().playerVehicleID)["accountDBID"]
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

def get_player_by_dbid(dbid):
	'''Extracts player information with matching account 'dbid' from
	various locations.
	''' 
	vehicle_id = find_vehicle_id(lambda v: v["accountDBID"] == dbid)
	if vehicle_id is not None:
		vehicle = get_vehicle(vehicle_id)
		return dict(id=dbid, name=vehicle["name"], vehicle_id=vehicle_id, is_alive=vehicle["isAlive"])
	info = find_prebattle_account_info(lambda i: i["dbID"] == dbid)
	if info:
		return dict(id=dbid, name=info["name"])
	return None

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

def get_old_ini_dir_path():
	path = os.path.join(find_res_mods_version_path(), "scripts", "client", "mods")
	if os.path.isdir(path):
		return path
	return ""

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

def ts_user_to_player(user_nick, user_game_nick, extract_patterns=[], mappings={}, players=[], use_metadata=False, use_ts_nick_search=False):
	players = list(players)

	def find_player(nick, comparator=lambda a, b: a == b):
		if hasattr(nick, "lower"):
			for player in players:
				if comparator(player["name"].lower(), nick.lower()):
					return player

	def map_nick(nick):
		if hasattr(nick, "lower"):
			try:
				return mappings[nick.lower()]
			except:
				pass

	# find player using TS user's WOT nickname in metadata (available if user
	# has TessuMod installed)
	if use_metadata and user_game_nick:
		player = find_player(user_game_nick)
		if player:
			LOG_DEBUG("Matched TS user to player with TS metadata", user_nick, user_game_nick, player)
		return player
	# no metadata, try find player by using WOT nickname extracted from TS
	# user's nickname using nick_extract_patterns
	for pattern in extract_patterns:
		matches = pattern.match(user_nick)
		if matches is not None and matches.groups():
			extracted_nick = matches.group(1).strip()
			player = find_player(extracted_nick)
			if player:
				LOG_DEBUG("Matched TS user to player with pattern", user_nick, player, pattern.pattern)
				return player
			# extracted nickname didn't match any player, try find player by
			# mapping the extracted nickname to WOT nickname (if available)
			player = find_player(map_nick(extracted_nick))
			if player:
				LOG_DEBUG("Matched TS user to player with pattern and mapping", user_nick, player, pattern.pattern)
				return player
	# extract patterns didn't help, try find player by mapping TS nickname to
	# WOT nickname (if available)
	player = find_player(map_nick(user_nick))
	if player:
		LOG_DEBUG("Matched TS user to player via mapping", user_nick, player)
		return player
	# still no match, as a last straw, try find player by searching each known
	# WOT nickname from the TS nickname
	if use_ts_nick_search:
		player = find_player(user_nick, comparator=lambda a, b: a in b)
		if player:
			LOG_DEBUG("Matched TS user to player with TS nick search", user_nick, player)
			return player
	# or alternatively, try find player by just comparing that TS nickname and
	# WOT nicknames are same
	else:
		player = find_player(user_nick)
		if player:
			LOG_DEBUG("Matched TS user to player by comparing names", user_nick, player)
			return player
	LOG_DEBUG("Failed to match TS user", user_nick)

def get_players(in_battle=False, in_prebattle=False, clanmembers=False, friends=False):
	if in_battle:
		try:
			vehicles = BigWorld.player().arena.vehicles
			for id in vehicles:
				vehicle = vehicles[id]
				LOG_DEBUG("Found player from battle", vehicle["name"])
				yield dict(name=vehicle["name"], id=vehicle["accountDBID"])
		except AttributeError:
			pass
	if in_prebattle:
		try:
			# get players from Team Battle room
			for unit in BigWorld.player().unitMgr.units.itervalues():
				for id, player in unit.getPlayers().iteritems():
					LOG_DEBUG("Found player from unit", player["nickName"])
					yield dict(name=player["nickName"], id=id)
		except AttributeError:
			pass
		try:
			# get players from Training Room and the like
			for roster in BigWorld.player().prebattle.rosters.itervalues():
				for info in roster.itervalues():
					LOG_DEBUG("Found player from rosters", info["name"])
					yield dict(name=info["name"], id=info["dbID"])
		except AttributeError:
			pass
	users_storage = storage_getter('users')()
	if clanmembers:
		for member in users_storage.getClanMembersIterator(False):
			LOG_DEBUG("Found clan member", member.getName())
			yield dict(name=member.getName(), id=member.getID())
	if friends:
		for friend in users_storage.getList(FriendsFindCriteria()):
			LOG_DEBUG("Found friend", friend.getName())
			yield dict(name=friend.getName(), id=friend.getID())

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
			LOG_CURRENT_EXCEPTION()


class RepeatTimer(object):

	def __init__(self, timeout):
		self._timeout   = timeout
		self._stopped   = True
		self.on_timeout = Event.Event()

	def start(self):
		self._stopped = False
		self._do_call()

	def stop(self):
		self._stopped = True

	def _do_call(self):
		if not self._stopped:
			BigWorld.callback(self._timeout, self._on_timeout)

	def _on_timeout(self):
		if not self._stopped:
			self.on_timeout()
			self._do_call()

class LOG_LEVEL(object):
	DEBUG = 0
	NOTE = 1
	WARNING = 2
	ERROR = 3

CURRENT_LOG_LEVEL = LOG_LEVEL.NOTE

def LOG_DEBUG(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
		debug_utils._doLog('DEBUG', _prefix_with_timestamp(msg), args)

def LOG_NOTE(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.NOTE:
		debug_utils._doLog('NOTE', _prefix_with_timestamp(msg), args)

def LOG_WARNING(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.WARNING:
		debug_utils._doLog('WARNING', _prefix_with_timestamp(msg), args)

def LOG_ERROR(msg, *args):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.ERROR:
		debug_utils._doLog('ERROR', _prefix_with_timestamp(msg), args)

def _prefix_with_timestamp(message):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
		return time.strftime('[%H:%M:%S] ') + str(message)
	return message

LOG_CURRENT_EXCEPTION = debug_utils.LOG_CURRENT_EXCEPTION

def LOG_CALL(msg=""):
	def wrap(func):
		def wrapper(*args, **kwargs):
			try:
				if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
					callargs = inspect.getcallargs(func, *args, **kwargs)
					callargs = { key: repr(callargs[key]) for key in callargs }
					debug_utils._doLog('DEBUG', _prefix_with_timestamp(func.__name__ + "():"), msg.format(**callargs))
			except:
				pass
			return func(*args, **kwargs)
		functools.update_wrapper(wrapper, func)
		return wrapper
	return wrap

def patch_instance_method(instance, method_name, new_function):
	original_method = getattr(instance, method_name)
	new_method = types.MethodType(functools.partial(new_function, original_method), instance)
	setattr(instance, method_name, new_method)
