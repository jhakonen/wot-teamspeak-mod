#
# TeamSpeak 3 ClientQuery example
# Copyright (c) 2010 TeamSpeak Systems GmbH
#
# Common clientquery functions
#

_API_NOT_CONNECTED_TO_SERVER = 1794
_API_INVALID_SCHANDLER_ID = 1799

#
# Get value by key from "key=value" string
#
def getParamValue(data, key):
	datas = data.split()
	for data in datas:
		s = data.split('=', 1)
		if s[0] == key:
			return unescape(s[1]) if len(s) > 1 else ""
	return None

def unescape(data):
	'''Tries to unescape any escapes that client query might return.
	Only tested with very limited amount of special characters.
	'''
	try:
		return data.decode('string-escape').replace('\s', ' ').replace('\/', '/')
	except AttributeError:
		# Python 3 error: 'str' object has no attribute 'decode'
		return data.replace('\s', ' ').replace('\/', '/')

#
# Check received data for error message
# Return None if no error occured. Otherwise return a tuple (errorID, errorMessage).
#
def checkError(data):
	if not data[0].startswith('error '):
		return None
	e = data[0].split()
	id = int(getParamValue(e[1], 'id'))
	if id == 0:  # ERROR_ok == 0
		return None
	msg = getParamValue(e[2], 'msg')
	if id == _API_NOT_CONNECTED_TO_SERVER:
		return APINotConnectedError(msg)
	if id == _API_INVALID_SCHANDLER_ID:
		return APIInvalidSchandlerIDError(msg)
	return APIError(str(id) + ": " + msg)

class APIError(Exception):
	pass

class APINotConnectedError(APIError):
	pass

class APIInvalidSchandlerIDError(APIError):
	pass
