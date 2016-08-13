class BattleSessionProvider(object):

	def __init__(self):
		self.__sharedRepo = SharedControllersLocator()

	@property
	def shared(self):
		return self.__sharedRepo

class SharedControllersLocator(object):

	def __init__(self):
		self.feedback = BattleFeedbackAdaptor()

class BattleFeedbackAdaptor(object):

	def onMinimapFeedbackReceived(self, eventID, entityID, value):
		pass

g_sessionProvider = BattleSessionProvider()
