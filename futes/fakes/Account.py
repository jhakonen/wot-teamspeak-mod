import random
from PlayerEvents import g_playerEvents

class PlayerAccount(object):

	def __init__(self):
		self.prebattle = Prebattle()
		self.name = "TestiNukke"
	
	def onBecomePlayer(self):
		g_playerEvents.onAccountBecomePlayer()

	def onBecomeNonPlayer(self):
		g_playerEvents.onAccountBecomeNonPlayer()

class Prebattle(object):

	def __init__(self):
		self.rosters = {0: {}}
