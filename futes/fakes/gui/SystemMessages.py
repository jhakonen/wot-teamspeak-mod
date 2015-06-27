class SM_TYPE(object):
	Warning = 0
	Information = 1

g_instance = True

messages = []

def pushMessage(message, type):
	messages.append(message)
