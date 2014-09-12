class SM_TYPE(object):
	Warning = 0

g_instance = True

def pushMessage(message, type):
	print "Pushed system message '{0}' and type '{1}'".format(message, type)
