import Event

def reset_fake():
	g_playerEvents.onAvatarBecomePlayer.clear()
	g_playerEvents.onAvatarBecomeNonPlayer.clear()
	g_playerEvents.onAvatarReady.clear()
	g_playerEvents.onAccountBecomePlayer.clear()
	g_playerEvents.onAccountBecomeNonPlayer.clear()

class _PlayerEvents(object):

	def __init__(self):
		self.onAvatarBecomePlayer = Event.Event()
		self.onAvatarBecomeNonPlayer = Event.Event()
		self.onAvatarReady = Event.Event()
		self.onAccountBecomePlayer = Event.Event()
		self.onAccountBecomeNonPlayer = Event.Event()

g_playerEvents = _PlayerEvents()
reset_fake()
