
class _NotificationMVC(object):

	def __init__(self):
		self.__model = _NotificationModel()

	def handleAction(self, typeID, entityID, action):
		pass

	def getModel(self):
		return self.__model

class _NotificationModel(object):
	pass

g_instance = _NotificationMVC()
