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

import logutils
import traceback

logger = logutils.logger.getChild("events")

class Message(object):
	ACTIONS = None
	ITEM = None
	def __init__(self, action, parameters):
		assert action in self.ACTIONS, "Action not supported: %s" % action
		self.__action = action
		self.__parameters = self.ITEM(parameters)

	@property
	def action(self):
		return self.__action

	@property
	def parameters(self):
		return self.__parameters

	def __repr__(self):
		return "%s(%s :: PARAMETERS: [%s])" % \
			(self.__class__.__name__, self.__action, ", ".join("%s=%s" % i for i in self.__parameters.iteritems()))

class MessagePump(object):

	def __init__(self):
		self.__subscriptions = {}

	def publish(self, message):
		assert isinstance(message, Message)
		for function in self.__get_message_cls_subscriptions(message.__class__):
			try:
				function(message.action, message.parameters)
			except Exception:
				logger.exception("Exception caught while publishing message: %s", message)
				logger.info("Publish called from: %s", "".join(traceback.format_stack()))

	def subscribe(self, message_cls, function):
		assert issubclass(message_cls, Message)
		self.__get_message_cls_subscriptions(message_cls).add(function)

	def unsubscribe(self, message_cls, function):
		assert issubclass(message_cls, Message)
		self.__get_message_cls_subscriptions(message_cls).remove(function)

	def __get_message_cls_subscriptions(self, message_cls):
		return self.__subscriptions.setdefault(message_cls, set())
