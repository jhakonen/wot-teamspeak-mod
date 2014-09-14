import time
from debug_utils import LOG_CURRENT_EXCEPTION

g_callback_events = {}
g_next_handle = 0

class UserDataObject(object):
	pass

def callback(secs, func):
	global g_next_handle
	g_callback_events[g_next_handle] = (time.time()+secs, func)
	g_next_handle += 1

def cancelCallback(handle):
	try:
		del g_callback_events[handle]
	except:
		pass

def loop():
	while True:
		try:
			t = time.time()
			for handle in g_callback_events.keys():
				event = g_callback_events[handle]
				if t > event[0]:
					cancelCallback(handle)
					event[1]()
			time.sleep(0.1)
		except KeyboardInterrupt:
			LOG_CURRENT_EXCEPTION()
			return
		except:
			LOG_CURRENT_EXCEPTION()
