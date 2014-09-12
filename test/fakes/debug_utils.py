import traceback

def LOG_NOTE(*args):
	print args

def LOG_ERROR(*args):
	print args

def LOG_CURRENT_EXCEPTION():
	traceback.print_exc()
