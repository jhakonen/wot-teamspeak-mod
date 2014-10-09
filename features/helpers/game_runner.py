import time
import os
import sys
import importlib
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

	base_path = os.path.dirname(os.path.realpath(__file__))
	root_path = os.path.realpath(os.path.join(base_path, "..", ".."))
	test_tmp_path = os.path.join(root_path, "tmp")

	sys.path.append(os.path.dirname(mod_path))
	sys.path.append(os.path.join(base_path, "fakes"))

	import ResMgr
	ResMgr.RES_MODS_VERSION_PATH = test_tmp_path
	try:
		os.makedirs(os.path.join(test_tmp_path, "scripts", "client", "mods"))
	except:
		pass

	importlib.import_module(os.path.basename(mod_path).replace(".py", ""))
	
	import tessu_utils.ts3
	tessu_utils.ts3._RETRY_TIMEOUT = 1

	import BigWorld

	while True:
		if not service.tick():
			break
		BigWorld.tick()
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
		import BigWorld
		import Account
		BigWorld.player(Account.PlayerAccount())

	def notification_center_has_message(self, message):
		import BigWorld
		import gui.SystemMessages
		end_t = time.time() + 20
		while time.time() < end_t:
			if message in gui.SystemMessages.messages:
				return True
			BigWorld.tick()
			time.sleep(0.01)
		return False

	def get_logs(self):
		import debug_utils
		return debug_utils.logs
