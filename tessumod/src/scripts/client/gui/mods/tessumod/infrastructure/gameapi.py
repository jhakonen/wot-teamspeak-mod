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
from gui import SystemMessages
from gui.shared.notifications import NotificationGuiSettings
from notification import NotificationMVC
from notification.settings import NOTIFICATION_TYPE
from notification.decorators import _NotificationDecorator
from debug_utils import LOG_CURRENT_EXCEPTION

from utils import patch_instance_method

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
			BigWorld.callback(1, functools.partial(cls.__push_notification, notification))
		elif cls.__enabled:
			model.addNotification(notification)

	@classmethod
	def __get_new_message_id(cls):
		try:
			return SystemMessages.g_instance.proto.serviceChannel._ServiceChannelManager__idGenerator.next()
		except AttributeError:
			return 0

	@classmethod
	def __show_system_message(cls, message, type):
		try:
			if SystemMessages.g_instance is None:
				BigWorld.callback(1, functools.partial(cls.__show_system_message, message, type))
			elif cls.__enabled:
				SystemMessages.pushMessage(message, type)
		except:
			LOG_CURRENT_EXCEPTION()

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
