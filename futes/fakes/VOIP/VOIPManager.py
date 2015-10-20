from debug_utils import LOG_NOTE

class VOIPManager(object):

	def isParticipantTalking(self, dbid):
		return True

	def onPlayerSpeaking(self, dbid, state):
		LOG_NOTE("TEST_SUITE: onPlayerSpeaking() called")
