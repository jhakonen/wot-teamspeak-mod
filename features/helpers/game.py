import time
from multiprocessing import Process, Queue

class GameRunner(object):

	def __init__(self, mod_path):
		self._mod_path = mod_path
		self._to_proc_queue = Queue()
		self._from_proc_queue = Queue()
		self._process = None

	def __getattr__(self, name):
		return self._stub(name)

	def _stub(self, name):
		return MethodStub(name, self._to_proc_queue, self._from_proc_queue)

	def start(self):
		self._process = Process(
			target=game_main,
			args=(self._to_proc_queue, self._from_proc_queue, self._mod_path)
		)
		self._process.start()

	def stop(self):
		if self._process:
			self.quit()
			self._process.join()
			self._process = None

class MethodStub(object):

	def __init__(self, method_name, to_queue, from_queue):
		self._method_name = method_name
		self._to_queue = to_queue
		self._from_queue = from_queue

	def __call__(self, *args, **kwargs):
		self._to_queue.put((self._method_name, args, kwargs))
		result = self._from_queue.get(timeout=600)
		if issubclass(result.__class__, Exception):
			raise result
		return result


def game_main(from_runner_queue, to_runner_queue, mod_path):
	service = GameService(from_runner_queue, to_runner_queue)
	while service.tick():
		time.sleep(0.01)

class GameService(object):

	def __init__(self, from_queue, to_queue):
		self._from_queue = from_queue
		self._to_queue = to_queue
		self._quit = False

	def tick(self):
		try:
			call = self._from_queue.get(block=False)
		except:
			call = None
		if call:
			method_name, args, kwargs = call
			try:
				result = getattr(self, method_name)(*args, **kwargs)
			except Exception as error:
				result = error
			self._to_queue.put(result)
		return not self._quit

	def quit(self):
		self._quit = True

	def login(self):
		raise NotImplementedError("Login() not implemented")

	def notification_center_has_message(self, message):
		raise NotImplementedError("notification_center_has_message() not implemented")
