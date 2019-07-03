import json
import Event
from functools import partial

def reset_fake():
	g_instance.cleanUp()

class _NotificationMVC(object):

	def __init__(self):
		self.__model = _NotificationModel(self)

	def handleAction(self, typeID, entityID, action):
		pass

	def getModel(self):
		return self.__model

	def cleanUp(self):
		self.__model.cleanUp()

class _NotificationModel(object):

	def __init__(self, mvc):
		self.__mvc = mvc
		self.collection = _NotificationCollection()
		# Not part of real model, provided for easier testing
		self.on_addNotification = Event.Event()

	def addNotification(self, msg):
		self.collection.addItem(msg)
		self.on_addNotification(msg)

	def updateNotification(self, typeID, entityID, entity, isStateChanged):
		pass

	def cleanUp(self):
		self.on_addNotification.clear()
		self.collection.clear()

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

	def clear(self):
		self.__notifications.clear()

g_instance = _NotificationMVC()
reset_fake()

