import time
from debug_utils import LOG_CURRENT_EXCEPTION

g_callback_events = []

class UserDataObject(object):
	pass

def callback(secs, func):
	g_callback_events.append((time.time()+secs, func))

def loop():
	while True:
		try:
			t = time.time()
			for event in g_callback_events:
				if t > event[0]:
					g_callback_events.remove(event)
					event[1]()
			time.sleep(0.1)
		except KeyboardInterrupt:
			LOG_CURRENT_EXCEPTION()
			return
		except:
			LOG_CURRENT_EXCEPTION()
