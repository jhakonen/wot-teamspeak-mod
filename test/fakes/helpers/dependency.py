from skeletons.gui.system_messages import ISystemMessages
from skeletons.gui.battle_session import IBattleSessionProvider

def reset_fake():
	global g_system_messages
	global g_battle_session_provider
	g_system_messages = SystemMessages()
	g_battle_session_provider = BattleSessionProvider()

class SystemMessages(ISystemMessages):
	def pushMessage(self, message, type):
		pass

class BattleSessionProvider(IBattleSessionProvider):
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

def instance(_class):
	if _class == ISystemMessages:
		return g_system_messages
	if _class == IBattleSessionProvider:
		return g_battle_session_provider

reset_fake()
