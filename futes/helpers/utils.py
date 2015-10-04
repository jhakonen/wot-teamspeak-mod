import mock
import functools

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
