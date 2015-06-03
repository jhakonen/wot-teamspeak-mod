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
import xml.etree.ElementTree as ET

import BigWorld
from gui import SystemMessages
from notification import NotificationMVC
from notification.settings import NOTIFICATION_TYPE
from notification.decorators import _NotificationDecorator
from gui.shared.notifications import NotificationGuiSettings

import utils

TSPLUGIN_INSTALL  = "TessuModTSPluginInstall"
TSPLUGIN_MOREINFO = "TessuModTSPluginMoreInfo"
TSPLUGIN_IGNORED  = "TessuModTSPluginIgnore"

_event_handlers = []
_is_plugin_install_shown = False

def add_event_handler(action, handler):
	_event_handlers.append((action, handler))

def push_ts_plugin_install_message(**data):
	global _is_plugin_install_shown
	if not _is_plugin_install_shown:
		msg_tmpl_filepath = os.path.join(utils.find_res_mods_version_path(), "gui", "tessu_mod", "tsplugin_install_notification.xml")
		_push_notification(_MessageDecorator(_get_new_message_id(), msg_tmpl_filepath, dict(data, **{
			"install_action": TSPLUGIN_INSTALL,
			"ignore_action": TSPLUGIN_IGNORED,
			"moreinfo_action": TSPLUGIN_MOREINFO
		})))
		_is_plugin_install_shown = True

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
		if SystemMessages.g_instance is None:
			BigWorld.callback(1, functools.partial(_push_system_message, message, type))
		else:
			SystemMessages.pushMessage(message, type)
	except:
		LOG_CURRENT_EXCEPTION()

def _push_notification(notification):
	model = NotificationMVC.g_instance.getModel()
	if model is None:
		BigWorld.callback(1, functools.partial(_push_notification, notification))
	else:
		model.addNotification(notification)

def _get_new_message_id():
	try:
		return SystemMessages.g_instance.proto.serviceChannel._ServiceChannelManager__idGenerator.next()
	except AttributeError:
		return 0

class _MessageDecorator(_NotificationDecorator):

	def __init__(self, entity_id, msg_tmpl_filepath, item):
		self.__item = None
		self.__msg_tmpl_filepath = msg_tmpl_filepath
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
			"message": self.__parse_xml(self.__exec_template(self.__msg_tmpl_filepath, item)),
			"notify": self.isNotify(),
			"auxData": ["GameGreeting"]
		}

	def __exec_template(self, filepath, data):
		with open(filepath, "r") as tmpl_file:
			return tmpl_file.read() % data

	def __parse_xml(self, xml_data):
		root = ET.fromstring(xml_data)
		vo_data = {
			"bgIcon":      root.findtext("./bgIcon", default=""),
			"defaultIcon": root.findtext("./defaultIcon", default=""),
			"icon":        root.findtext("./icon", default=""),
			"savedData":   int(root.findtext("./savedData", default=0)),
			"timestamp":   int(root.findtext("./timestamp", default=-1)),
			"type":        root.findtext("./type", default="black"),
			"message":     self.__xml_element_contents_to_text(root.find("./message")),
			"filters": [],
			"buttonsLayout": []
		}
		for button in root.findall("./buttonsLayout/button"):
			vo_data["buttonsLayout"].append({
				"label":  button.get("label", default=""),
				"action": button.get("action", default=""),
				"type":   button.get("type", default="submit")
			})
		return vo_data

	def __xml_element_contents_to_text(self, element):
		if element is None:
			return ""
		contents = []
		contents.append(element.text or "")
		for sub_element in element:
			contents.append(ET.tostring(sub_element))
		contents.append(element.tail or "")
		return "".join(contents).strip()

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
					handler(typeID, entityID, notification.get_item())
	else:
		original_method(typeID, entityID, action)

_patch_instance_method(NotificationMVC.g_instance, "handleAction", _handleAction)
