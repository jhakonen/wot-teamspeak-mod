
class Event(object):

	def __init__(self):
		self.callbacks = []

	def __iadd__(self, other):
		self.callbacks.append(other)
		return self

	def __call__(self, *args, **kwargs):
		for callback in self.callbacks:
			callback(*args, **kwargs)
