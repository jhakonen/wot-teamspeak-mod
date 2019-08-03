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

import os
import types
import functools
import json

import BigWorld
from gui import SystemMessages
from notification import NotificationMVC
from notification.settings import NOTIFICATION_TYPE
from notification.decorators import _NotificationDecorator
from gui.shared.notifications import NotificationGuiSettings
from helpers import dependency
from skeletons.gui.system_messages import ISystemMessages

import resources
import utils

TSPLUGIN_DOWNLOAD  = "TessuModTSPluginDownload"
TSPLUGIN_MOREINFO = "TessuModTSPluginMoreInfo"
TSPLUGIN_IGNORED  = "TessuModTSPluginIgnore"
SETTINGS_PATH     = "TessuModSettingsPath"

NOTIFICATION_FILES = {
	"install": "tsplugin_install_notification.json",
	"update": "tsplugin_update_notification.json"
}

def init():
	global _event_handlers
	global _is_plugin_install_shown
	global _are_notifications_enabled
	_event_handlers = []
	_is_plugin_install_shown = {
		"install": False,
		"update": False
	}
	_are_notifications_enabled = True

def set_notifications_enabled(enabled):
	global _are_notifications_enabled
	_are_notifications_enabled = enabled

def add_event_handler(action, handler):
	_event_handlers.append((action, handler))

def push_ts_plugin_install_message(message_type, **data):
	if not _is_plugin_install_shown[message_type]:
		msg_tmpl = resources.read_file(utils.get_resource_data_path() + "/" + NOTIFICATION_FILES[message_type])
		_push_notification(_MessageDecorator(_get_new_message_id(), msg_tmpl, dict(data, **{
			"download_action": TSPLUGIN_DOWNLOAD,
			"ignore_action": TSPLUGIN_IGNORED,
			"moreinfo_action": TSPLUGIN_MOREINFO
		})))
		_is_plugin_install_shown[message_type] = True

def update_message(type_id, msg_id, data):
	model = NotificationMVC.g_instance.getModel()
	if model is not None:
		notification = model.collection.getItem(type_id, msg_id)
		if notification:
			notification.update(data)
		model.updateNotification(type_id, msg_id, data, False)

def push_info_message(message):
	_push_system_message(message, SystemMessages.SM_TYPE.Information)

def push_warning_message(message):
	_push_system_message(message, SystemMessages.SM_TYPE.Warning)

def push_error_message(message):
	_push_system_message(message, SystemMessages.SM_TYPE.Error)

def _push_system_message(message, type):
	'''Pushes given 'message' to system notification center in garage. 'type'
	is one of the SystemMessages.SM_TYPE.* constants.
	'''
	try:
		system_messages = dependency.instance(ISystemMessages)
		if system_messages is None:
			BigWorld.callback(1, functools.partial(_push_system_message, message, type))
		elif _are_notifications_enabled:
			system_messages.pushMessage(message, type)
	except:
		utils.LOG_CURRENT_EXCEPTION()

def _push_notification(notification):
	model = NotificationMVC.g_instance.getModel()
	if model is None:
		BigWorld.callback(1, functools.partial(_push_notification, notification))
	elif _are_notifications_enabled:
		model.addNotification(notification)

def _get_new_message_id():
	try:
		system_messages = dependency.instance(ISystemMessages)
		return system_messages.proto.serviceChannel._ServiceChannelManager__idGenerator.next()
	except AttributeError:
		return 0

class _MessageDecorator(_NotificationDecorator):

	def __init__(self, entity_id, msg_tmpl, item):
		self.__item = None
		self.__msg_tmpl = msg_tmpl
		super(_MessageDecorator, self).__init__(entity_id, item, NotificationGuiSettings(isNotify=True, showAt=BigWorld.time()))

	def getType(self):
		return NOTIFICATION_TYPE.MESSAGE

	def update(self, item):
		self._make(item)

	def get_item(self):
		return self.__item

	def _make(self, item = None, settings = None):
		super(_MessageDecorator, self)._make(item, settings)
		self.__item = item
		self._vo = {
			"typeID": self.getType(),
			"entityID": self.getID(),
			"message": self.__parse_json(self.__msg_tmpl % item),
			"notify": self.isNotify(),
			"auxData": ["GameGreeting"]
		}

	def __parse_json(self, json_data):
		json_data = json.loads(json_data)
		vo_data = {
			"bgIcon":      "../../" + json_data.get("bgIcon", ""),
			"defaultIcon": "../../" + json_data.get("defaultIcon", ""),
			"icon":        "../../" + json_data.get("icon", ""),
			"savedData":   int(json_data.get("savedData", 0)),
			"timestamp":   int(json_data.get("timestamp", -1)),
			"type":        json_data.get("type", "black"),
			"message":     "\n".join(json_data["message"]),
			"filters": [],
			"buttonsLayout": []
		}
		for button in json_data.get("buttons", []):
			vo_data["buttonsLayout"].append({
				"label":  button.get("label", ""),
				"action": button.get("action", ""),
				"type":   button.get("type", "submit")
			})
		return vo_data

def _patch_instance_method(instance, method_name, new_function):
	original_method = getattr(instance, method_name)
	new_method = types.MethodType(functools.partial(new_function, original_method), instance)
	setattr(instance, method_name, new_method)

def _handleAction(original_method, self, typeID, entityID, action):
	if action in map(lambda x: x[0], _event_handlers):
		notification = self.getModel().collection.getItem(typeID, entityID)
		if notification:
			for handler_action, handler in _event_handlers:
				if action == handler_action:
					item = None
					if hasattr(notification, "get_item"):
						item = notification.get_item()
					handler(typeID, entityID, item)
	else:
		original_method(typeID, entityID, action)

_patch_instance_method(NotificationMVC.g_instance, "handleAction", _handleAction)
