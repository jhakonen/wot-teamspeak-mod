
def reset_fake():
	global g_instance
	global messages
	g_instance = True
	messages = []

class SM_TYPE(object):
	Information = 0
	Warning = 1
	Error = 2

def pushMessage(message, type):
	messages.append(message)

reset_fake()
