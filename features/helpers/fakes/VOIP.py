from debug_utils import LOG_NOTE

g_instance = None

def getVOIPManager():
	global g_instance
	if not g_instance:
		g_instance = VOIPManager()
	return g_instance

class VOIPManager(object):

	def isParticipantTalking(self, dbid):
		return True

	def onPlayerSpeaking(self, dbid, state):
		LOG_NOTE("TEST_SUITE: onPlayerSpeaking() called")
