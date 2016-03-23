import Event

class InputHandler(object):

	def __init__(self):
		self.onKeyDown = Event.Event()

g_instance = InputHandler()
