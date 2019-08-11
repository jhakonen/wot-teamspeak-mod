
def reset_fake():
	global _STORAGE
	_STORAGE = { "users": UsersStorage() }

class UsersStorage(object):
	pass

class storage_getter(object):

	def __init__(self, name):
		if name not in _STORAGE:
			raise RuntimeError('Storage {0} not found'.format(name))
		self._name = name

	def __call__(self, *args):
		return _STORAGE[self._name]

reset_fake()
