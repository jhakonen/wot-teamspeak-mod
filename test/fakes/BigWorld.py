import time as _time
from debug_utils import LOG_CURRENT_EXCEPTION

def reset_fake():
	global _player
	global _camera
	global entities
	global g_callback_events
	global g_next_handle
	_player = None
	_camera = Camera()
	entities = {}
	g_callback_events = {}
	g_next_handle = 0

class UserDataObject(object):
	pass

def callback(secs, func):
	global g_next_handle
	result = g_next_handle
	g_callback_events[g_next_handle] = (_time.time()+secs, func)
	g_next_handle += 1
	return result

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

def player(entity=None):
	global _player
	if entity is None:
		if _player is not None:
			return _player
		return None
	assert _player is None, "Call BigWorld.fake_clear_player() first"
	_player = entity
	_player.onBecomePlayer()
	return _player

def fake_clear_player():
	global _player
	if _player is None:
		return
	temp = _player
	_player = None
	temp.onBecomeNonPlayer()

def time():
	return _time.time()

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

	def __repr__(self):
		return "Vector(%d, %d, %d)" % (self.x, self.y, self.z)

class Entity(object):

	def __init__(self):
		self.position = Vector(0, 0, 0)

reset_fake()
