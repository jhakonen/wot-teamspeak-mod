import random

class PlayerAccount(object):

	def __init__(self):
		self.prebattle = Prebattle()
		self.name = "TestiNukke"
	
	def onBecomePlayer(self):
		pass

class Prebattle(object):

	def __init__(self):
		self.rosters = {0: {}}
