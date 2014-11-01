import random

class PlayerAccount(object):

	def __init__(self):
		self.prebattle = Prebattle()
		self.name = "TestiNukke"
	
	def onBecomePlayer(self):
		pass

class Prebattle(object):

	def __init__(self):
		self.rosters = dict(foo={})
		self.id_counter = 0

	def add_roster(self, name):
		self.rosters["foo"][self.id_counter] = dict(
			name=name,
			dbID=str(random.randint(0, 1000000))
		)
		self.id_counter += 1
