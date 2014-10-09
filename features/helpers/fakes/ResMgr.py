
RES_MODS_VERSION_PATH = ""

class Paths(object):

	def values(self):
		return [Value(RES_MODS_VERSION_PATH)]

class Value(object):
	def __init__(self, value):
		self.asString = str(value)

def openSection(path):
	return { "Paths": Paths() }
