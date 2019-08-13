import asyncio
import time
from unittest import mock

def contains_match(pattern):
	class Matcher(object):
		def __eq__(self, string):
			return pattern.lower() in string.lower()
	return Matcher()

def mock_was_called_with(mock_obj, *args, **kwargs):
	'''Returns True if 'mock_obj' was ever called with provided arguments.'''
	return mock.call(*args, **kwargs) in mock_obj.call_args_list

async def wait_until_true(checker_func, timeout=5):
	timeout_time = time.time() + timeout
	while not checker_func():
		assert time.time() < timeout_time, "Timeout"
		await asyncio.sleep(0.001)
