import time

class GameRunner(object):

	def __init__(self, mod_path):
		self._mod_path = mod_path

	def start(self):
		pass

	def stop(self):
		pass

	def login(self):
		pass

	def notification_center_has_message(self, message):
		time.sleep(600)
