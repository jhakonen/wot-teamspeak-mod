import py_compile
import zipfile
import os
import sys
import fnmatch
import shutil
import argparse
import re

WOT_VERSION          = "0.9.20.0"
SUPPORT_URL          = "http://forum.worldoftanks.eu/index.php?/topic/433614-/"
ROOT_DIR             = os.path.dirname(os.path.realpath(__file__))
SRC_DIR              = os.path.join(ROOT_DIR, "src")
PACKAGE_ROOT_DIR     = os.path.join("res_mods", WOT_VERSION)
DEFAULT_MOD_VERSION  = "dev"
BUILD_DIR            = os.path.join(os.getcwd(), "build")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--mod-version', default=DEFAULT_MOD_VERSION)
	args = parser.parse_args()
	in_file_parameters = {
		"build_info.py.in": dict(
			MOD_VERSION = args.mod_version,
			SUPPORT_URL = SUPPORT_URL
		),
		"TessuMod.txt.in": dict(
			SUPPORT_URL = SUPPORT_URL
		)
	}
	packager = Packager(
		src_dir               = SRC_DIR,
		build_dir             = BUILD_DIR,
		package_path          = os.path.join(os.getcwd(), "tessumod-{0}-bin.zip".format(args.mod_version)),
		package_root_dir      = PACKAGE_ROOT_DIR,
		in_file_parameters    = in_file_parameters,
		ignored_file_patterns = [".+_test.py"]
	)
	packager.create()
	print "Package file path:", packager.get_package_path()
	print "Package root path:", packager.get_package_root_path()

def accepts_extensions(extensions):
	'''Decorator function which allows call to pass to the decorated function
	if passed filepath has extension in list of given 'extensions'.
	'''
	def decorator(original_function):
		def wrapper(self, src_filepath):
			for extension in extensions:
				if src_filepath.lower().endswith(extension.lower()):
					return original_function(self, src_filepath)
		return wrapper
	return decorator

class CallbackList(object):

	def __init__(self, *callbacks):
		self.__callbacks = callbacks

	def __call__(self, *args, **kwargs):
		for callback in self.__callbacks:
			callback(*args, **kwargs)

class Packager(object):

	def __init__(self, src_dir, build_dir, package_path, package_root_dir, in_file_parameters, ignored_file_patterns=[]):
		self.__src_dir = os.path.normpath(src_dir)
		self.__build_dir = os.path.normpath(build_dir)
		self.__package_path = package_path
		self.__package_root_dir = package_root_dir
		self.__in_file_parameters = in_file_parameters
		self.__ignored_file_patterns = ignored_file_patterns
		self.__builders = CallbackList(
			self.__compile_py_file,
			self.__copy_file,
			self.__run_template_file
		)

	def get_package_path(self):
		return self.__package_path

	def get_package_root_path(self):
		return self.__package_root_dir

	def create(self):
		self.__remove_build_dir()
		self.__remove_old_package()
		self.__build_files(self.__iterate_src_filepaths())
		self.__package_files()

	def __remove_build_dir(self):
		try:
			shutil.rmtree(self.__build_dir)
		except:
			pass

	def __remove_old_package(self):
		try:
			os.remove(self.__package_path)
		except:
			pass

	def __build_files(self, src_filepaths):
		for src_filepath in src_filepaths:
			self.__builders(src_filepath)

	def __iterate_src_filepaths(self):
		'''Returns an iterator which returns paths to all files within source dir.'''
		for root, dirs, files in os.walk(self.__src_dir):
			for filename in files:
				if all([not re.match(pattern, filename, re.IGNORECASE) for pattern in self.__ignored_file_patterns]):
					yield os.path.normpath(os.path.join(root, filename))

	@accepts_extensions([".py"])
	def __compile_py_file(self, src_filepath):
		'''Compiles 'src_filepath' python source file into python bytecode file and
		saves it build dir.
		'''
		debug_filepath = src_filepath.replace(self.__src_dir, "").replace("\\", "/").strip("/")
		build_filepath = self.__src_path_to_build_path(src_filepath) + "c"
		self.__make_parent_dirs(build_filepath)
		# compile source py-file into bytecode pyc-file
		py_compile.compile(file=src_filepath, cfile=build_filepath, dfile=debug_filepath, doraise=True)

	@accepts_extensions([".swf", ".txt", ".json", ".xml", ".png"])
	def __copy_file(self, src_filepath):
		'''Simply copies file at 'src_filepath' to build dir.'''
		build_filepath = self.__src_path_to_build_path(src_filepath)
		self.__make_parent_dirs(build_filepath)
		# simply copy file from source to build dir
		shutil.copyfile(src_filepath, build_filepath)

	@accepts_extensions([".in"])
	def __run_template_file(self, src_filepath):
		build_filepath = src_filepath[:-3]
		parameters = self.__in_file_parameters[os.path.basename(src_filepath)]
		# run 'parameters' through in-template and produce temporary output file
		with open(src_filepath, "r") as in_file, open(build_filepath, "w") as out_file:
			out_file.write(in_file.read().format(**parameters))
		# further process the output file with other builders
		self.__builders(build_filepath)
		# remove the temporary output file
		os.remove(build_filepath)

	def __src_path_to_build_path(self, src_path):
		# ${SRC_DIR}/whereever/whatever --> ${BUILD_DIR}/whereever/whatever
		return src_path.replace(self.__src_dir, self.__build_dir)

	def __make_parent_dirs(self, filepath):
		'''Creates any missing parent directories of file indicated in 'filepath'.'''
		try:
			os.makedirs(os.path.dirname(filepath))
		except:
			pass

	def __package_files(self):
		paths = []
		for root, dirs, files in os.walk(self.__build_dir):
			target_dirpath = root.replace(self.__build_dir, self.__package_root_dir)
			for filename in files:
				paths.append((os.path.join(root, filename), os.path.join(target_dirpath, filename)))

		with zipfile.ZipFile(self.__package_path, "w") as package_file:
			for source, target in paths:
				package_file.write(source, target)

if __name__ == "__main__":
	sys.exit(main())
