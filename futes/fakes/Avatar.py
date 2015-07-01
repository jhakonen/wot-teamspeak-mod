from PlayerEvents import g_playerEvents

class TestArena(object):
	
	def __init__(self):
		self.vehicles = {}

class Avatar(object):

	def onBecomePlayer(self):
		self.arena = TestArena()
		g_playerEvents.onAvatarBecomePlayer()

	def onBecomeNonPlayer(self):
		g_playerEvents.onAvatarBecomeNonPlayer()
