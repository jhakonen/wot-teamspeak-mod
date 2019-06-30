import os

RES_MODS_VERSION_PATH = ""

class PathsXml(object):
	def __init__(self):
		pass

	def values(self):
		return [PathValue(RES_MODS_VERSION_PATH)]


class PathValue(object):
	def __init__(self, path):
		self.__path = path

	@property
	def asString(self):
		return self.__path


class FileValue(object):
	def __init__(self, path):
		self.__path = path

	@property
	def asString(self):
		with open(self.__path, "r") as file:
			return file.read()

	@property
	def asBinary(self):
		with open(self.__path, "rb") as file:
			return file.read()


def openSection(path):
	if os.path.basename(path) == "paths.xml":
		return { "Paths": PathsXml() }
	elif os.path.isfile(path):
		return FileValue(path)
	elif os.path.isdir(path):
		return { FileValue(os.path.join(path, name)): None for name in os.listdir(path) }


def isFile(path):
	return os.path.isfile(path)


def isDir(path):
	return os.path.isdir(path)
