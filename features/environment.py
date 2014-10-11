from helpers.ts_client_query import TSClientQueryService
from helpers.game_runner import GameRunner
from helpers import test_events
import os
import sys
import inspect

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

def before_scenario(context, scenario):
	context.ts_client = TSClientQueryService()
	context.game = GameRunner(
		mod_path=os.path.join(
			os.path.dirname(os.path.realpath(__file__)),
				"..", "src", "mods", "tessu_mod.py")
	)
	test_events.add_callback(context.ts_client.check)
	context.ts_to_player_name = {}

def after_scenario(context, scenario):
	context.ts_client.stop()
	context.game.stop()
	test_events.clear_callbacks()
