import time
import os
import sys
from Queue import Empty
from multiprocessing import Process, Queue
from test_events import process_events

class GameRunner(object):

	def __init__(self, mod_path, ini_path):
		self._mod_path = mod_path
		self._ini_path = ini_path
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
			args=(self._to_proc_queue, self._from_proc_queue, self._mod_path, self._ini_path)
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
		while True:
			process_events()
			try:
				result = self._from_queue.get(block=False)
				break
			except Empty:
				pass
		if issubclass(result.__class__, Exception):
			raise result
		return result


def game_main(from_runner_queue, to_runner_queue, mod_path, ini_path):
	service = GameService(from_runner_queue, to_runner_queue)

	base_path = os.path.dirname(os.path.realpath(__file__))

	sys.path.append(os.path.dirname(mod_path))
	sys.path.append(os.path.join(base_path, "fakes"))

	# create directory structure for ini-file
	try:
		os.makedirs(os.path.dirname(ini_path))
	except:
		pass
	# remove previous ini-file (if one exists)
	try:
		os.remove(ini_path)
	except:
		pass
	import tessu_mod
	import tessu_utils.ts3
	import tessu_utils.settings
	tessu_utils.ts3._RETRY_TIMEOUT = 1
	tessu_utils.settings.settings(ini_path)

	tessu_mod.load_mod()

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
		self._found_log_indexes = []

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

	def enter_battle(self):
		import BigWorld
		import Avatar
		BigWorld.player(Avatar.Avatar())

	def notification_center_has_message(self, message):
		import gui.SystemMessages
		for _ in self._processing_events():
			if message in gui.SystemMessages.messages:
				return True
		return False

	def _processing_events(self, timeout=20):
		import BigWorld
		end_t = time.time() + timeout
		while time.time() < end_t:
			yield
			BigWorld.tick()
			time.sleep(0.01)

	def get_logs(self):
		import debug_utils
		return debug_utils.logs

	def add_player(self, player_name):
		import BigWorld
		BigWorld.player().arena.add_vehicle(player_name)

	def is_player_speaking(self, player_name):
		import VOIP
		for _ in self._processing_events():
			if VOIP.getVOIPManager().isParticipantTalking(self._get_player_dbid(player_name)):
				return True
		return False

	def is_player_not_speaking(self, player_name):
		import VOIP
		for _ in self._processing_events():
			if not VOIP.getVOIPManager().isParticipantTalking(self._get_player_dbid(player_name)):
				return True
		return False

	def wait_for_log(self, log_message, once=True):
		import debug_utils
		for _ in self._processing_events():
			for index in range(len(debug_utils.logs)):
				if once and index in self._found_log_indexes:
					continue
				log = debug_utils.logs[index]
				if log_message.lower() in log[1].lower():
					self._found_log_indexes.append(index)
					return True
		return False	

	def reload_ini_file(self):
		from tessu_utils.settings import settings
		settings().reload()

	def _get_player_dbid(self, player_name):
		import BigWorld
		for vehicle_id in BigWorld.player().arena.vehicles:
			vehicle = BigWorld.player().arena.vehicles[vehicle_id]
			if player_name == vehicle["name"]:
				return vehicle["accountDBID"]
		raise RuntimeError("Player {0} doesn't exist".format(player_name))
