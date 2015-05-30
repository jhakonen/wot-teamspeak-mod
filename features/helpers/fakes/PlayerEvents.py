import Event

class _PlayerEvents(object):

	def __init__(self):
		self.onAvatarBecomePlayer = Event.Event()
		self.onAvatarBecomeNonPlayer = Event.Event()

g_playerEvents = _PlayerEvents()
