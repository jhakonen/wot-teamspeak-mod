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

from __future__ import absolute_import
from collections import deque

import BigWorld
from helpers import dependency
from gui import SystemMessages
from gui.shared.notifications import NotificationGuiSettings
from messenger.formatters import collections_by_type
from messenger.m_constants import SCH_CLIENT_MSG_TYPE
from notification import NotificationMVC
from notification.settings import NOTIFICATION_TYPE
from notification.decorators import MessageDecorator, _NotificationDecorator
from skeletons.gui.system_messages import ISystemMessages

from .hookutils import hook_method, CALL_WITH_ORIGINAL

notification_handlers = {}
_notifications_queue = deque()

def show_notification(data):
	is_advanced = "icon" in data or "ignorable" in data or "buttons" in data or "actions" in data
	is_basic = "type" in data
	assert (is_basic ^ is_advanced) and "message" in data, "Invalid notification data provided"
	assert isinstance(data["message"], list), "Message must be a list"
	entity_id = _get_new_message_id()
	decorator = None
	if is_basic:
		decorator = _BasicMessageDecorator(
			entity_id=entity_id,
			type=data["type"],
			message=data["message"]
		)
	if is_advanced:
		decorator = _AdvancedMessageDecorator(
			entity_id=entity_id,
			icon=data["icon"],
			message=data["message"],
			buttons=data["buttons"],
			ignorable=data["ignorable"],
			ignore_action=data["ignore_action"],
			actions=data["actions"]
		)

	assert decorator, "Message decorator not formed"
	_add_notification(decorator)

@hook_method(NotificationMVC._NotificationMVC, "handleAction", call_style=CALL_WITH_ORIGINAL)
def _handleAction(original, self, typeID, entityID, action):
	if entityID in notification_handlers:
		notification_handlers[entityID].handle_action(action)
	else:
		return original(self, typeID, entityID, action)

def _add_action_listener(listener):
	notification_handlers[listener.getID()] = listener

def _remove_action_listener(listener):
	del notification_handlers[listener.getID()]

def _get_new_message_id():
	try:
		system_messages = dependency.instance(ISystemMessages)
		return system_messages.proto.serviceChannel._ServiceChannelManager__idGenerator.next()
	except AttributeError:
		return 0

def _add_notification(notification):
	_notifications_queue.append(notification)
	_process_notification_queue()

def _process_notification_queue():
	if not _notifications_queue:
		return
	model = NotificationMVC.g_instance.getModel()
	if not model:
		BigWorld.callback(1, _process_notification_queue)
		return
	model.addNotification(_notifications_queue.popleft())

class _BasicMessageDecorator(MessageDecorator):

	TYPE_LOOKUP = {
		"info": SystemMessages.SM_TYPE.Information,
		"warning": SystemMessages.SM_TYPE.Warning
	}

	def __init__(self, entity_id, type, message):
		assert len(message) == 1, "Only single message line supported"
		sm_type = self.TYPE_LOOKUP[type]
		formatter = collections_by_type.CLIENT_FORMATTERS.get(SCH_CLIENT_MSG_TYPE.SYS_MSG_TYPE)
		formatted, settings = formatter.format(message[0], [sm_type.name(), None, None])[0]
		super(_BasicMessageDecorator, self).__init__(entity_id, formatted, settings)

class _AdvancedMessageDecorator(_NotificationDecorator):

	def __init__(self, entity_id, icon, message, buttons, ignorable, ignore_action, actions):
		self.__icon = icon
		self.__message = message
		self.__ignorable = ignorable
		self.__ignore_action = ignore_action
		self.__ignored = False
		self.__actions = actions
		self.__buttons_layout = []
		for button in buttons:
			self.__buttons_layout.append({
				"label": button.get("label", ""),
				"action": button.get("action", ""),
				"type": "submit"
			})
		item = None # unused
		settings = NotificationGuiSettings(isNotify=True, showAt=BigWorld.time())
		super(_AdvancedMessageDecorator, self).__init__(entity_id, item, settings)
		_add_action_listener(self)

	def getType(self):
		return NOTIFICATION_TYPE.MESSAGE

	def update(self, item):
		self._make(item)

	def get_item(self):
		return self.__item

	def _make(self, item = None, settings = None):
		super(_AdvancedMessageDecorator, self)._make(item, settings)

		message = ""
		for paragraph in self.__message:
			message += "<p>" + paragraph + "</p>\n"

		if self.__ignorable:
			ignore_state = "on" if self.__ignored else "off"
			icon_url = "img://scripts/client/gui/mods/tessumod/assets/checkbox_{}.png".format(ignore_state)
			message += "\n<p align=\"right\">"
			message += "<a href=\"event:ignore_message\">No thanks, don't show this again</a>"
			message += "   <img src=\"{}\" height=\"12\" width=\"12\" align=\"right\"/>".format(icon_url)
			message += "</p>\n"

		self._vo = {
			"typeID": self.getType(),
			"entityID": self.getID(),
			"message": {
				"bgIcon": "",
				"defaultIcon": "",
				"icon": "../../" + self.__icon,
				"savedData": 0,
				"timestamp": -1,
				"type": "black",
				"message": message,
				"filters": [],
				"buttonsLayout": self.__buttons_layout
			},
			"notify": self.isNotify(),
			"auxData": ["GameGreeting"]
		}

	def clear(self):
		"""
		Called when this notification is removed from notification model.
		"""
		_remove_action_listener(self)
		super(_AdvancedMessageDecorator, self).clear()

	def handle_action(self, action):
		if action == "ignore_message":
			self.__ignored = not self.__ignored
			model = NotificationMVC.g_instance.getModel()
			model.updateNotification(self.getType(), self.getID(), None, True)
			if self.__ignore_action:
				self.__ignore_action(self.__ignored)
		elif action in self.__actions:
			self.__actions[action]()
