class _NotificationDecorator(object):

	def __init__(self, entityID, entity=None, settings=None):
		self._entityID = entityID
		self._make(entity, settings)

	def _make(self, entity=None, settings=None):
		self._vo = {}

	def getID(self):
		return self._entityID

	def isNotify(self):
		return False

	def getListVO(self):
		return self._vo
