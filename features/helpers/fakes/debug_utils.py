import traceback

logs = []

def _doLog(type, msg, args):
	logs.append((type, msg, args))

def LOG_DEBUG(msg, *args):
	logs.append(("DEBUG", msg, args))

def LOG_NOTE(msg, *args):
	logs.append(("NOTE", msg, args))

def LOG_ERROR(msg, *args):
	logs.append(("ERROR", msg, args))

def LOG_CURRENT_EXCEPTION():
	logs.append(("EXCEPTION", traceback.format_exc(), []))
