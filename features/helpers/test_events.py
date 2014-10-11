import time

_callbacks = []

def add_callback(callback):
	_callbacks.append(callback)

def clear_callbacks():
	del _callbacks[:]

def process_events(timeout=0.01):
	for callback in _callbacks:
		callback()
	time.sleep(timeout)
