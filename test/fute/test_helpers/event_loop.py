
import time

class EventLoop(object):

	def __init__(self):
		self.__once_callbacks = []
		self.__repeat_callbacks = []

	def fini(self):
		del self.__once_callbacks[:]
		del self.__repeat_callbacks[:]

	def execute(self):
		self.__exit_called = False
		while not self.__exit_called:
			for callback in list(self.__once_callbacks):
				if callback.should_call():
					self.__once_callbacks.remove(callback)
					callback.call()
			for callback in list(self.__repeat_callbacks):
				if callback.should_call():
					callback.call()
					callback.reset()
			time.sleep(0.001)

	def exit(self):
		self.__exit_called = True

	def call(self, callback, repeat=False, timeout=0):
		if repeat:
			self.__repeat_callbacks.append(Callback(callback, timeout))
		else:
			self.__once_callbacks.append(Callback(callback, timeout))

	def cancel_call(self, callback):
		found = False
		for callback_obj in self.__once_callbacks:
			if callback_obj.callback == callback:
				self.__once_callbacks.remove(callback_obj)
				found = True
				break
		if not found:
			for callback_obj in self.__repeat_callbacks:
				if callback_obj.callback == callback:
					self.__repeat_callbacks.remove(callback_obj)
					found = True
					break
		assert found, "No such callback: %s" % callback

class Callback(object):

	def __init__(self, callback, timeout):
		self.callback = callback
		self.timeout = timeout
		self.reset()

	def reset(self):
		self.time_end = time.time() + self.timeout

	def should_call(self):
		return time.time() >= self.time_end

	def call(self):
		self.callback()
