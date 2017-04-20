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

import BigWorld
from helpers import dependency
from gui import SystemMessages
from gui.shared.notifications import NotificationGuiSettings
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from gui.prb_control.dispatcher import _PrbControlLoader
from gui.prb_control.entities.listener import IGlobalListener
from messenger.proto.events import g_messengerEvents
from messenger.proto.shared_find_criteria import FriendsFindCriteria
from messenger.storage import storage_getter
from notification import NotificationMVC
from notification.settings import NOTIFICATION_TYPE
from notification.decorators import _NotificationDecorator
from skeletons.gui.battle_session import IBattleSessionProvider
from skeletons.gui.system_messages import ISystemMessages
from debug_utils import _doLog, _makeMsgHeader
import Event as _Event
import VOIP
from VOIP.VOIPManager import VOIPManager
import BattleReplay
import ResMgr
import BWLogging

from functools import partial
from traceback import format_exception
import sys
import types
import logging

import logutils

logger = logutils.logger.getChild("gameapi")

g_sessionProvider = dependency.instance(IBattleSessionProvider)

Event = _Event.Event

class EventLoop(object):

	@classmethod
	def callback(cls, timeout, function, *args, **kwargs):
		if args or kwargs:
			function = partial(function, *args, **kwargs)
		return BigWorld.callback(timeout, function)

	@classmethod
	def cancel_callback(cls, id):
		BigWorld.cancelCallback(id)

	@classmethod
	def create_callback_repeater(cls, function):
		return _EventRepeater(function)

class _EventRepeater(object):

	def __init__(self, function):
		self.__id       = None
		self.__timeout  = None
		self.__started  = False
		self.__function = function

	def start(self, timeout):
		self.__timeout = timeout
		self.stop()
		self.__start_callback()
		self.__started  = True

	def __start_callback(self):
		if self.__id is None:
			self.__id = EventLoop.callback(self.__timeout, self.__on_timeout)

	def stop(self):
		if self.__id is not None:
			EventLoop.cancel_callback(self.__id)
			self.__id = None
		self.__started = False

	def is_active(self):
		return self.__started

	def __on_timeout(self):
		self.__id = None
		self.__function()
		if self.__started:
			self.__start_callback()

class Battle(object):

	@classmethod
	def get_camera_position(cls):
		camera = BigWorld.camera()
		if camera:
			return (camera.position.x, camera.position.y, camera.position.z)

	@classmethod
	def get_camera_direction(cls):
		camera = BigWorld.camera()
		if camera:
			return (camera.direction.x, camera.direction.y, camera.direction.z)

	@classmethod
	def get_entity(cls, entity_id):
		entity = BigWorld.entities.get(entity_id)
		if entity:
			assert hasattr(entity, "position")
			return entity

	@classmethod
	def patch_battle_replay_play(cls, patch_function):
		original_method = BattleReplay.BattleReplay.play
		def wrapper_play(self, fileName=None):
			return patch_function(self, original_method, fileName)
		BattleReplay.BattleReplay.play = wrapper_play

	@classmethod
	def find_vehicle_id(cls, matcher):
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

	@classmethod
	def get_vehicle(cls, vehicle_id):
		'''Returns vehicle info with matching 'vehicle_id' if available.
		Returns None if not.
		'''
		if vehicle_id is None:
			return None
		try:
			return BigWorld.player().arena.vehicles[vehicle_id]
		except AttributeError:
			pass

class Player(object):

	@classmethod
	def get_player_by_dbid(cls, dbid):
		'''Extracts player information with matching account 'dbid' from
		various locations.
		'''
		vehicle_id = Battle.find_vehicle_id(lambda v: v["accountDBID"] == dbid)
		if vehicle_id is not None:
			vehicle = Battle.get_vehicle(vehicle_id)
			return dict(id=dbid, name=vehicle["name"], in_battle=True, vehicle_id=vehicle_id, is_alive=vehicle["isAlive"])
		info = cls.find_prebattle_account_info(lambda i: i["id"] == dbid)
		if info:
			return dict(id=dbid, name=info["name"], in_battle=False)
		return None

	@classmethod
	def get_my_name(cls):
		'''Returns current player's nickname. None if not available.'''
		try:
			return BigWorld.player().name
		except AttributeError:
			pass

	@classmethod
	def get_my_dbid(cls):
		'''Returns current player's account dbid. None if not available.'''
		try:
			return BigWorld.player().databaseID
		except AttributeError:
			try:
				return Battle.get_vehicle(BigWorld.player().playerVehicleID)["accountDBID"]
			except AttributeError:
				pass

	@classmethod
	def find_prebattle_account_info(cls, matcher):
		'''Finds player information from prebattle rosters (e.g. in practise room
		when you assign players to teams). Given 'matcher' function is used pick
		desired info. Returns None if nothing found.
		'''
		try:
			for player in g_prebattleListener.get_players():
				if matcher(player):
					return dict(player)
		except AttributeError as error:
			print error

	@classmethod
	def get_players(cls, in_battle=False, in_prebattle=False, clanmembers=False, friends=False):
		yielded_names = []

		if in_battle:
			try:
				vehicles = BigWorld.player().arena.vehicles
				names = []
				for id in vehicles:
					vehicle = vehicles[id]
					names.append(vehicle["name"])
					if vehicle["name"] not in yielded_names:
						yield dict(name=vehicle["name"], id=vehicle["accountDBID"], in_battle=True)
						yielded_names.append(vehicle["name"])
				logger.debug("Found players from battle: %s", names)
			except AttributeError:
				pass

		if in_prebattle:
			names = []
			for player in g_prebattleListener.get_players():
				names.append(player["name"])
				if player["name"] not in yielded_names:
					yield dict(player, in_battle=False)
					yielded_names.append(player["name"])
			logger.debug("Found players from prebattle: %s", names)

		users_storage = storage_getter('users')()

		if clanmembers:
			names = []
			for member in users_storage.getClanMembersIterator(False):
				names.append(member.getName())
				if member.getName() not in yielded_names:
					yield dict(name=member.getName(), id=member.getID(), in_battle=False)
					yielded_names.append(member.getName())
			logger.debug("Found clan members: %s", names)

		if friends:
			names = []
			for friend in users_storage.getList(FriendsFindCriteria()):
				names.append(friend.getName())
				if friend.getName() not in yielded_names:
					yield dict(name=friend.getName(), id=friend.getID(), in_battle=False)
					yielded_names.append(friend.getName())
			logger.debug("Found friends: %s", names)

class Notifications(object):

	__enabled = True
	__event_handlers = []

	@classmethod
	def init(cls):
		patch_instance_method(NotificationMVC.g_instance, "handleAction", cls.__handleAction)

	@classmethod
	def set_enabled(cls, enabled):
		cls.__enabled = enabled

	@classmethod
	def add_event_handler(cls, action, handler):
		cls.__event_handlers.append((action, handler))

	@classmethod
	def show_info_message(cls, message):
		cls.__show_system_message(message, SystemMessages.SM_TYPE.Information)

	@classmethod
	def show_warning_message(cls, message):
		cls.__show_system_message(message, SystemMessages.SM_TYPE.Warning)

	@classmethod
	def show_error_message(cls, message):
		cls.__show_system_message(message, SystemMessages.SM_TYPE.Error)

	@classmethod
	def show_custom_message(cls, icon="", message="", buttons_layout=[], item={}):
		cls.__push_notification(cls.__MessageDecorator(
			entity_id = cls.__get_new_message_id(),
			icon = icon,
			message = message,
			buttons_layout = buttons_layout,
			item = item
		))

	@classmethod
	def update_custom_message(cls, type_id, msg_id, data):
		model = NotificationMVC.g_instance.getModel()
		if model is not None:
			notification = model.collection.getItem(type_id, msg_id)
			if notification:
				notification.update(data)
			model.updateNotification(type_id, msg_id, data, False)

	@classmethod
	def __handleAction(cls, original_method, self, typeID, entityID, action):
		if action in map(lambda x: x[0], cls.__event_handlers):
			notification = self.getModel().collection.getItem(typeID, entityID)
			if notification:
				for handler_action, handler in cls.__event_handlers:
					if action == handler_action:
						handler(typeID, entityID, notification.get_item())
		else:
			original_method(typeID, entityID, action)

	@classmethod
	def __push_notification(cls, notification):
		model = NotificationMVC.g_instance.getModel()
		if model is None:
			EventLoop.callback(1, cls.__push_notification, notification)
		elif cls.__enabled:
			model.addNotification(notification)

	@classmethod
	def __get_new_message_id(cls):
		try:
			system_messages = dependency.instance(ISystemMessages)
			return system_messages.proto.serviceChannel._ServiceChannelManager__idGenerator.next()
		except AttributeError:
			return 0

	@classmethod
	def __show_system_message(cls, message, type):
		try:
			system_messages = dependency.instance(ISystemMessages)
			if system_messages is None:
				EventLoop.callback(1, cls.__show_system_message, message, type)
			elif cls.__enabled:
				system_messages.pushMessage(message, type)
		except:
			logger.exception("Showing system message failed")

	class __MessageDecorator(_NotificationDecorator):

		def __init__(self, entity_id, icon, message, buttons_layout, item):
			self.__item = None
			self.__icon = icon
			self.__message = message
			self.__buttons_layout = buttons_layout
			_NotificationDecorator.__init__(self, entity_id, item, NotificationGuiSettings(isNotify=True, showAt=BigWorld.time()))

		def getType(self):
			return NOTIFICATION_TYPE.MESSAGE

		def update(self, item):
			self._make(item)

		def get_item(self):
			return self.__item

		def _make(self, item = None, settings = None):
			_NotificationDecorator._make(self, item, settings)
			self.__item = item
			buttons_layout = []
			for button in self.__buttons_layout:
				buttons_layout.append({
					"label": button.get("label", "") % item,
					"action": button.get("action", "") % item,
					"type": button.get("type", "submit") % item
				})
			message = {
				"bgIcon": "",
				"defaultIcon": "",
				"icon": self.__icon % item,
				"savedData": 0,
				"timestamp": -1,
				"type": "black",
				"message": self.__message % item,
				"filters": [],
				"buttonsLayout": buttons_layout
			}
			self._vo = {
				"typeID": self.getType(),
				"entityID": self.getID(),
				"message": message,
				"notify": self.isNotify(),
				"auxData": ["GameGreeting"]
			}

class VoiceChat(object):

	@classmethod
	def set_player_speaking(cls, player_id, speaking):
		g_messengerEvents.voip.onPlayerSpeaking(player_id, speaking)

	@classmethod
	def patch_is_participant_speaking(cls, patch_function):
		original_method = VOIPManager.isParticipantTalking
		def wrapper_isParticipantTalking(self, dbid):
			return patch_function(self, original_method, dbid)
		VOIPManager.isParticipantTalking = wrapper_isParticipantTalking

class MinimapMarkerAnimation(object):

	def __init__(self, vehicle_id, interval, action, on_done):
		self.__interval   = interval
		self.__action     = action
		self.__vehicle_id = vehicle_id
		self.__on_done    = on_done
		self.__timer      = EventLoop.create_callback_repeater(self.__updateMinimap)

	def start(self):
		if not self.__timer.is_active():
			self.__timer.start(self.__interval)
			self.__updateMinimap()

	def stop(self):
		self.__timer.stop()

	def __updateMinimap(self):
		if self.__timer.is_active():
			try:
				if g_sessionProvider.shared.feedback:
					g_sessionProvider.shared.feedback.onMinimapFeedbackReceived(
						FEEDBACK_EVENT_ID.MINIMAP_SHOW_MARKER, self.__vehicle_id, self.__action)
			except AttributeError:
				logger.exception("Updating minimap failed")
		else:
			self.__on_done(self.__vehicle_id)

class Environment(object):

	@classmethod
	def find_res_mods_version_path(cls):
		for path in cls.get_resource_paths():
			if "res_mods" in path:
				return path
		return ""

	@classmethod
	def get_resource_paths(cls):
		res = ResMgr.openSection('../paths.xml')
		sb = res['Paths']
		vals = sb.values()
		for vl in vals:
			yield vl.asString

def patch_instance_method(instance, method_name, new_function):
	original_method = getattr(instance, method_name)
	new_method = types.MethodType(partial(new_function, original_method), instance)
	setattr(instance, method_name, new_method)

class PrebattleListener(IGlobalListener):

	def __init__(self):
		self.__players = {}

	def get_players(self):
		return self.__players.values()

	def onPrbFunctionalFinished(self):
		self.__players.clear()

	def onUnitFunctionalFinished(self):
		self.__players.clear()

	def onPlayerAdded(self, functional, info):
		self.__add_player_info(info)

	def onUnitPlayerAdded(self, info):
		self.__add_player_info(info)

	def onUnitPlayerInfoChanged(self, info):
		self.__add_player_info(info)

	def __add_player_info(self, info):
		self.__players[info.dbID] = dict(id=info.dbID, name=info.name)

g_prebattleListener = PrebattleListener()

def PrbControlLoader_onAccountShowGUI(original):
	def decorator(self, ctx):
		original(self, ctx)
		g_prebattleListener.startGlobalListening()
	return decorator
_PrbControlLoader.onAccountShowGUI = PrbControlLoader_onAccountShowGUI(_PrbControlLoader.onAccountShowGUI)

class LogRedirectionHandler(logging.Handler):
	"""
	Specialized logging handler which redirects logging calls to BigWorld's
	logging facility. In a difference to BWLogging.BWLogRedirectionHandler this
	handles also exception information, printing it log output as well.
	"""

	def emit(self, record):
		category = record.name.encode(sys.getdefaultencoding())
		msg = record.getMessage()
		if record.exc_info is not None:
			msg += "\n" + "".join(format_exception(*record.exc_info))
		msg = msg.encode(sys.getdefaultencoding())
		BWLogging.logLevelToBigWorldFunction[record.levelno](category, msg, None)
