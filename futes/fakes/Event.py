from debug_utils import LOG_CURRENT_EXCEPTION

class Event(object):

	def __init__(self):
		self.callbacks = []

	def __iadd__(self, other):
		self.callbacks.append(other)
		return self

	def __call__(self, *args, **kwargs):
		for callback in self.callbacks:
			try:
				callback(*args, **kwargs)
			except:
				LOG_CURRENT_EXCEPTION()
