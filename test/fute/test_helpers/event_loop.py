
import time

class EventLoop(object):

	def __init__(self):
		self.__callbacks = []

	def fini(self):
		del self.__callbacks[:]

	def execute(self):
		self.__exit_called = False
		while not self.__exit_called:
			for callback in self.__callbacks:
				if callback.should_call():
					self.__callbacks.remove(callback)
					callback()
					if callback.repeat:
						self.__callbacks.append(callback)

			time.sleep(0.001)

	def exit(self):
		self.__exit_called = True

	def call(self, callback, repeat=False, timeout=0):
		self.__callbacks.append(Callback(callback, repeat, timeout))

	def cancel_call(self, callback):
		for callback_obj in self.__callbacks:
			if callback_obj.callback == callback:
				callback_obj.repeat = False
				self.__callbacks.remove(callback_obj)
				break

class Callback(object):

	def __init__(self, callback, repeat, timeout):
		self.callback = callback
		self.repeat = repeat
		self.timeout = timeout
		self.__set_time_end()

	def __set_time_end(self):
		self.time_end = time.time() + self.timeout

	def should_call(self):
		return time.time() >= self.time_end

	def __call__(self):
		self.callback()
		if self.repeat:
			self.__set_time_end()
