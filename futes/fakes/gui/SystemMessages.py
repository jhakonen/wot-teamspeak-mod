class SM_TYPE(object):
	Information = 0
	Warning = 1
	Error = 2

g_instance = True

messages = []

def pushMessage(message, type):
	messages.append(message)
