from helpers.ts_client_query import TSClientQueryService
from helpers.game_runner import GameRunner
from helpers import test_events
import os
import sys
import inspect
from ConfigParser import SafeConfigParser
import coverage

# hack to get non-english error messages from e.g. socket
# not to screw up the test suite
try:
	# use e.g. cp850 for Finnish
	TEST_ENCODING = os.environ["TEST_ENCODING"]
	reload(sys)
	sys.setdefaultencoding(TEST_ENCODING)
except:
	pass

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
	context.ini_path = os.path.join(os.path.dirname(
		os.path.realpath(__file__)), "..", "tmp", "tessu_mod.ini")
	context.game = GameRunner(
		mod_path=os.path.join(
			os.path.dirname(os.path.realpath(__file__)),
				"..", "src", "mods", "tessu_mod.py"),
		ini_path=context.ini_path
	)
	context.set_ini_variable = set_ini_variable.__get__(context)
	test_events.add_callback(context.ts_client.check)

def after_scenario(context, scenario):
	context.ts_client.stop()
	context.game.stop()
	test_events.clear_callbacks()
