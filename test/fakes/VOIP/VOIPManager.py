from debug_utils import LOG_NOTE

def reset_fake():
	global g_instance
	g_instance = VOIPManager()

def getVOIPManager():
	return g_instance

class VOIPManager(object):

	def isParticipantTalking(self, dbid):
		return True

	def onPlayerSpeaking(self, dbid, state):
		LOG_NOTE("TEST_SUITE: onPlayerSpeaking() called")

reset_fake()
