import random

class TestArena(object):
	
	def __init__(self):
		self.vehicles = {}

	def add_vehicle(self, name):
		vehicle_id = str(random.randint(0, 1000000))
		dbid = str(random.randint(0, 1000000))
		self.vehicles[vehicle_id] = dict(
			accountDBID=dbid,
			name=name
		)

class Avatar(object):

	def onBecomePlayer(self):
		self.arena = TestArena()
