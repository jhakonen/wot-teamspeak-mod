import asyncio

loop = asyncio.get_event_loop()

class EventLoop(object):

	def __init__(self):
		self.__handles = {}

	def fini(self):
		for handle in self.__handles.values():
			handle.cancel()
		self.__handles.clear()

	def execute(self):
		loop.run_forever()

	def exit(self):
		loop.stop()

	def call(self, callback, repeat=False, timeout=0):
		if repeat:
			handle = loop.create_task(repeat_call(timeout, callback))
		else:
			handle = loop.call_later(timeout, callback)
		self.__handles[callback] = handle

	def cancel_call(self, callback):
		self.__handles[callback].cancel()
		del self.__handles[callback]

async def repeat_call(timeout, callback):
	while True:
		await asyncio.sleep(timeout)
		callback()
