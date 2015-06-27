class TestArena(object):
	
	def __init__(self):
		self.vehicles = {}

class Avatar(object):

	def onBecomePlayer(self):
		self.arena = TestArena()
