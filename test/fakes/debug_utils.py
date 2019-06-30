import traceback

logs = []

def _doLog(type, msg, args):
	logs.append((type, msg, args))
	print "{type}: {msg} {args}".format(type=type, msg=msg, args=args)

def LOG_DEBUG(msg, *args):
	_doLog("DEBUG", msg, args)

def LOG_NOTE(msg, *args):
	_doLog("NOTE", msg, args)

def LOG_ERROR(msg, *args):
	_doLog("ERROR", msg, args)

def LOG_CURRENT_EXCEPTION():
	_doLog("EXCEPTION", traceback.format_exc(), [])
