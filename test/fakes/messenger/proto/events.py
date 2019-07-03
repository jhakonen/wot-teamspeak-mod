import Event

def reset_fake():
	g_messengerEvents.users.onUsersListReceived.clear()
	g_messengerEvents.voip.onPlayerSpeaking.clear()

class Events(object):

	def __init__(self):
		self.users = Users()
		self.voip = VOIPSharedEvents()

class Users(object):

	def __init__(self):
		self.onUsersListReceived = Event.Event()

class VOIPSharedEvents(object):

	def __init__(self):
		self.onPlayerSpeaking = Event.Event()

g_messengerEvents = Events()

reset_fake()
