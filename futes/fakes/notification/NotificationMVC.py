import json
import Event
import BigWorld
from functools import partial

class _NotificationMVC(object):

	def __init__(self):
		self.__model = _NotificationModel(self)
		self.futes_on_add_notification = Event.Event()

	def handleAction(self, typeID, entityID, action):
		pass

	def getModel(self):
		return self.__model

class _NotificationModel(object):

	def __init__(self, mvc):
		self.__mvc = mvc
		self.collection = _NotificationCollection()

	def addNotification(self, msg):
		self.collection.addItem(msg)
		BigWorld.callback(0, partial(self.__mvc.futes_on_add_notification, msg))

	def updateNotification(self, typeID, entityID, entity, isStateChanged):
		pass

class _NotificationCollection(object):

	def __init__(self):
		self.__notifications = {}

	def getItem(self, typeID, itemID):
		return self.__notifications[json.dumps([typeID, itemID])]

	def addItem(self, item):
		itemIds = json.dumps([item.getType(), item.getID()])
		if itemIds in self.__notifications:
			return False
		self.__notifications[itemIds] = item
		return True

g_instance = _NotificationMVC()
