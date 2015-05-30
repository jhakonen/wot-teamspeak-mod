from helpers.ts_client_query import TSClientQueryService
from helpers.game_runner import GameRunner
from helpers import test_events
import os
import sys
import inspect
from ConfigParser import SafeConfigParser
import coverage
import mmap
import struct
import time

# hack to get non-english error messages from e.g. socket
# not to screw up the test suite
try:
	# use e.g. cp850 for Finnish
	TEST_ENCODING = os.environ["TEST_ENCODING"]
	reload(sys)
	sys.setdefaultencoding(TEST_ENCODING)
except:
	pass

TEST_INI = """
[General]
log_level: 1
ini_check_interval: 5
speak_stop_delay: 1
get_wot_nick_from_ts_metadata: on
update_cache_in_replays: off
ts_nick_search_enabled: on
nick_extract_patterns:

[NameMappings]

[TSClientQueryService]
host: localhost
port: 25639
polling_interval: 0.1

[VoiceChatNotifications]
enabled: on
self_enabled: on

[MinimapNotifications]
enabled: on
self_enabled: on
action: attackSender
repeat_interval: 3.5

[3DAudio]
enabled: on
"""

def print_call(func):
	def printer(*args, **kwargs):
		call_args = inspect.getcallargs(func, *args, **kwargs)
		print "Called: {0}({1})".format(func.__name__, ", ".join(
			name + "=" + repr(call_args[name]) for name in call_args if name != "self"))
		return func(*args, **kwargs)
	return printer

from helpers.ts_client_query import TSClientQueryHandler
TSClientQueryHandler.push = print_call(TSClientQueryHandler.push)
TSClientQueryHandler.handle_command = print_call(TSClientQueryHandler.handle_command)

def set_ini_variable(context, section, key, value):
	config = SafeConfigParser()
	config.read([context.ini_path])
	config.set(section, key, value)
	with open(context.ini_path, "w") as f:
		config.write(f)
	if context.game.is_running():
		context.game.reload_ini_file()

def before_all(context):
	context.coverage = coverage.coverage()
	context.coverage.erase()

def after_all(context):
	context.coverage.load()
	context.coverage.html_report(directory="coverage_report")
	context.coverage.report()

def before_scenario(context, scenario):
	context.ts_client = TSClientQueryService()
	context.ts_client.add_wait_of_command("clientlist")
	context.ini_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "tmp")
	context.ini_path = os.path.join(context.ini_dir_path, "tessu_mod.ini")
	context.game = GameRunner(
		mod_path=os.path.join(
			os.path.dirname(os.path.realpath(__file__)),
				"..", "tessumod", "src", "scripts", "client", "mods", "tessu_mod.py"),
		ini_dir_path=context.ini_dir_path
	)
	context.set_ini_variable = set_ini_variable.__get__(context)
	test_events.add_callback(context.ts_client.check)
	context.ts_plugin = TSPluginFake()

	# create directory structure for ini-file
	try:
		os.makedirs(context.ini_dir_path)
	except:
		pass
	# remove previous ini-files (if any exists)
	try:
		for file_name in os.listdir(context.ini_dir_path):
			os.remove(os.path.join(context.ini_dir_path, file_name))
	except:
		pass
	with open(context.ini_path, "w") as ini_file:
		ini_file.write(TEST_INI)

def after_scenario(context, scenario):
	context.ts_client.stop()
	context.game.stop()
	test_events.clear_callbacks()
	context.ts_plugin.disabled()

class TSPluginFake(object):

	TAG_NAME = "TessuModTSPlugin"
	DATA_FORMAT = "H"
	DATA_SIZE = struct.calcsize(DATA_FORMAT)
	VERSION = 1

	def __init__(self):
		self._shmem = None
		self._version = self.VERSION

	def enabled(self):
		self._shmem = mmap.mmap(0, self.DATA_SIZE, self.TAG_NAME, mmap.ACCESS_WRITE)
		self._write()

	def disabled(self):
		if self._shmem:
			self._shmem.close()
		self._shmem = None

	def set_version_as_newer(self):
		self._version = self.VERSION + 1
		self._write()

	def _write(self):
		if self._shmem:
			self._shmem.seek(0)
			self._shmem.write(struct.pack("H", self._version))
