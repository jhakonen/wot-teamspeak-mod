from PlayerEvents import g_playerEvents
import BigWorld
import Event

class TestArena(object):
	
	def __init__(self):
		self.vehicles = {}
		self.positions = {}
		self.onNewVehicleListReceived = Event.Event()
		self.onVehicleAdded = Event.Event()
		self.onVehicleUpdated = Event.Event()
		self.onVehicleKilled = Event.Event()
		self.onPositionsUpdated = Event.Event()

class Avatar(object):

	name = "not set"

	def __init__(self):
		self.__ready_timer_id = None

	def onBecomePlayer(self):
		self.arena = TestArena()
		g_playerEvents.onAvatarBecomePlayer()
		self.__ready_timer_id = BigWorld.callback(0.1, g_playerEvents.onAvatarReady)

	def onBecomeNonPlayer(self):
		if self.__ready_timer_id is not None:
			BigWorld.cancelCallback(self.__ready_timer_id)
			self.__ready_timer_id = None
		g_playerEvents.onAvatarBecomeNonPlayer()
