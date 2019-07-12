from debug_utils import LOG_NOTE

def reset_fake():
	global g_instance
	g_instance = VOIPManager()

def getVOIPManager():
	return g_instance

class VOIPManager(object):

	def __init__(self):
		self.fake_talkers = {}

	def isParticipantTalking(self, dbid):
		return self.fake_talkers.get(dbid, None)

	def onPlayerSpeaking(self, dbid, state):
		LOG_NOTE("TEST_SUITE: onPlayerSpeaking() called")

reset_fake()
