import time as _time
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION

g_callback_events = {}
g_next_handle = 0

class UserDataObject(object):
	pass

def logError(type, msg, *args):
	print "{type}: {msg}".format(type=type, msg=msg)
	for arg in args:
		print arg

def callback(secs, func):
	global g_next_handle
	g_callback_events[g_next_handle] = (_time.time()+secs, func)
	g_next_handle += 1

def cancelCallback(handle):
	try:
		del g_callback_events[handle]
	except:
		pass

def tick():
	try:
		t = _time.time()
		for handle in g_callback_events.keys():
			event = g_callback_events[handle]
			if t > event[0]:
				cancelCallback(handle)
				event[1]()
	except KeyboardInterrupt:
		LOG_CURRENT_EXCEPTION()
		return
	except:
		LOG_CURRENT_EXCEPTION()

_player = None

def player(entity=None):
	global _player
	if entity is not None:
		if _player is not None:
			_player.onBecomeNonPlayer()
		_player = entity
		_player.onBecomePlayer()
	return _player

def time():
	return _time.time()

_camera = None

def camera():
	global _camera
	if _camera is None:
		_camera = Camera()
	return _camera

class Camera(object):

	def __init__(self):
		self.position = Vector(0.0, 0.0, 0.0)
		self.direction = Vector(0.0, 0.0, 0.0)

class Vector(object):

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

entities = {}

class Entity(object):

	def __init__(self):
		self.position = Vector(0, 0, 0)
