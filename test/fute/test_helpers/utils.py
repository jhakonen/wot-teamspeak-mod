import functools
from unittest import mock

def mock_was_called_with(mock_obj, *args, **kwargs):
	'''Returns True if 'mock_obj' was ever called with provided arguments.'''
	return mock.call(*args, **kwargs) in mock_obj.call_args_list

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

def use_event_loop(method):
	def wrapper(self, *args, **kwargs):
		method(self, *args, **kwargs)
		self.run_in_event_loop()
	functools.update_wrapper(wrapper, method)
	return wrapper

class CheckerTruthy(object):
	def __init__(self, callback):
		self.callback = callback

	def is_valid(self):
		try:
			return self.callback()
		except Exception as error:
			return False

	def get_error_msg(self):
		return "Failed"

class CheckerEqual(object):
	def __init__(self, value1, value2):
		self.value1 = value1
		self.value2 = value2

	def is_valid(self):
		return self._get_value1() == self._get_value2()

	def _get_value1(self):
		if callable(self.value1):
			try:
				return self.value1()
			except Exception as error:
				return error
		return self.value1

	def _get_value2(self):
		if callable(self.value2):
			try:
				return self.value2()
			except Exception as error:
				return error
		return self.value2

	def get_error_msg(self):
		return "%s == %s" % (repr(self._get_value1()), repr(self._get_value2()))
