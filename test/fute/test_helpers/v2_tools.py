import asyncio
import time
from unittest import mock

def contains_match(pattern):
	class Matcher(object):
		def __eq__(self, string):
			return pattern.lower() in string.lower()
	return Matcher()

def message_decorator_matches_fragments(fragments):
	class Matcher(object):
		def __eq__(self, decorator):
			contents_str = repr(decorator.getListVO())
			for fragment in fragments:
				if fragment not in contents_str:
					return False
			return True
	return Matcher()

def mock_was_called_with(mock_obj, *args, **kwargs):
	'''Returns True if 'mock_obj' was ever called with provided arguments.'''
	return mock.call(*args, **kwargs) in mock_obj.call_args_list

async def wait_until_true(checker_func, timeout=5):
	timeout_time = time.time() + timeout
	while not checker_func():
		assert time.time() < timeout_time, "Wait timed out"
		await asyncio.sleep(0.001)

async def wait_until_equal(checker_func, expected, timeout=5):
	timeout_time = time.time() + timeout
	while True:
		value = checker_func()
		if value == expected:
			break
		assert time.time() < timeout_time, "Wait timed out, %s != %s" % (value, expected)
		await asyncio.sleep(0.001)

class ExecTimer:
	def __enter__(self):
		self.start = time.time()
		return self

	def __exit__(self, *args):
		self.end = time.time()
