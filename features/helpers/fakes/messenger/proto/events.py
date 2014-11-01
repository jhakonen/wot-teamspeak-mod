
import Event

class Events(object):
	
	def __init__(self):
		self.users = Users()

class Users(object):

	def __init__(self):
		self.onUsersRosterReceived = Event.Event()

g_messengerEvents = Events()
