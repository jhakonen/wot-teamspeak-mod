import Event

class _PlayerEvents(object):

	def __init__(self):
		self.onAvatarBecomePlayer = Event.Event()
		self.onAvatarBecomeNonPlayer = Event.Event()
		self.onAvatarReady = Event.Event()
		self.onAccountBecomePlayer = Event.Event()

g_playerEvents = _PlayerEvents()
