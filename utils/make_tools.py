# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2016  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
import time
import glob
import copy
import py_compile
import shutil
import zipfile
import subprocess
import traceback
import Queue
import threading
import warnings
from contextlib import contextmanager

# 3rd party libs
import nose
import tailer
import colorama
from termcolor import colored

def init():
	global BUILDER_LOOKUP, PROJECT_COL_WIDTH, BUILDER_COL_WIDTH
	BUILDER_LOOKUP = {
		"in_generate": InGenerateBuilder,
		"py_compile":  PythonCompileBuilder,
		"copy":        CopyBuilder,
		"compress":    CompressBuilder,
		"uncompress":  UncompressBuilder,
		"qmake":       QMakeBuilder,
		"nosetests":   NoseTestsBuilder,
		"tailfile":    TailFileBuilder
	}
	colorama.init()

@contextmanager
def with_builders(logger, root, config, exclude=[]):
	config = copy.deepcopy(config)
	variables = dict(config.pop("vars", {}), cwd=os.getcwd(), root=root)
	builders = __collect_builders(logger, variables, config)
	builders = __exclude_builders_with_tags(builders, exclude)
	yield builders
	__deinitialize_builders(builders)

def __collect_builders(logger, variables, config):
	builders = []
	for builder_entry in config.get("builders", []):
		builders.append(__create_builder(logger, variables, [], builder_entry))
	for project_name, project_config in config.get("projects", {}).iteritems():
		project_vars = dict(variables, **project_config.get("vars", {}))
		project_tags = project_config.get("tags", [])
		for builder_entry in project_config.get("builders", []):
			builders.append(__create_builder(logger, project_vars, project_tags, builder_entry))
	return builders

def __create_builder(logger, variables, tags, builder_entry):
	name, config = builder_entry.items()[0]
	tags = config.pop("tags", []) + tags
	assert name in BUILDER_LOOKUP, "No such builder: {}".format(name)
	builder = BUILDER_LOOKUP[name]()
	builder.logger = logger
	builder.variables = variables
	builder.tags = tags
	builder.config = config
	builder.initialize()
	return builder

def __exclude_builders_with_tags(builders, exclude):
	results = []
	for builder in builders:
		if all([tag not in builder.tags for tag in exclude]):
			results.append(builder)
	return results

def __deinitialize_builders(builders):
	for builder in builders:
		builder.deinitialize()

class Logger(object):

	def __init__(self, verbose):
		self.__verbose = verbose
		self.__on_empty_line = True

	def debug(self, *args, **kwargs):
		if self.__verbose:
			lb_end = kwargs.pop("lb_end", True)
			lb_start = kwargs.pop("lb_start", True) and not self.__on_empty_line
			self.__write(sys.stdout, self.__format_msg(None, lb_start, lb_end, *args, **kwargs))

	def info(self, *args, **kwargs):
		lb_end = kwargs.pop("lb_end", True)
		lb_start = kwargs.pop("lb_start", True) and not self.__on_empty_line
		self.__write(sys.stdout, self.__format_msg(None, lb_start, lb_end, *args, **kwargs))

	def warning(self, *args, **kwargs):
		lb_end = kwargs.pop("lb_end", True)
		lb_start = kwargs.pop("lb_start", True) and not self.__on_empty_line
		self.__write(sys.stderr, self.__format_msg("yellow", lb_start, lb_end, "Warning:", *args, **kwargs))

	def error(self, *args, **kwargs):
		lb_end = kwargs.pop("lb_end", True)
		lb_start = kwargs.pop("lb_start", True) and not self.__on_empty_line
		self.__write(sys.stderr, self.__format_msg("red", lb_start, lb_end, "Error:", *args, **kwargs))

	def exception(self, **kwargs):
		lb_end = kwargs.pop("lb_end", True)
		lb_start = kwargs.pop("lb_start", True) and not self.__on_empty_line
		self.__write(sys.stderr, self.__format_msg("red", lb_start, lb_end, "Exception:", traceback.format_exc()))

	def __format_msg(self, color, lb_start, lb_end, *args, **kwargs):
		msg = " ".join([str(arg) for arg in args])
		try:
			msg = msg.format(kwargs)
		except KeyError:
			pass
		if color is not None:
			msg = colored(msg, color)
		if self.__on_empty_line or lb_start:
			msg = colored(time.strftime("[%H:%M:%S] "), "grey", attrs=["bold"]) + msg
		if lb_start and not self.__on_empty_line:
			msg = "\n" + msg
		if lb_end:
			msg = msg + "\n"
		return msg

	def __write(self, device, msg):
		device.write(msg)
		self.__on_empty_line = msg.endswith("\n")

class AbstractBuilder(object):

	def __init__(self):
		super(AbstractBuilder, self).__init__()

	@property
	def logger(self):
		return self.__logger

	@logger.setter
	def logger(self, logger):
		self.__logger = logger

	@property
	def variables(self):
		pass

	@variables.setter
	def variables(self, variables):
		self.__variables = variables

	@property
	def config(self):
		return self.__config

	@config.setter
	def config(self, config):
		self.__config = config

	@property
	def tags(self):
		return self.__tags

	@tags.setter
	def tags(self, tags):
		self.__tags = tags

	def initialize(self):
		pass

	def deinitialize(self):
		pass

	def expand_value(self, input):
		if not hasattr(input, "format"):
			return input
		prev_value = input
		while True:
			new_value = prev_value.format(**self.__variables)
			if prev_value == new_value:
				return new_value
			prev_value = new_value

	def expand_path(self, path):
		return os.path.normpath(self.expand_value(path))

	def create_dirpath(self, path):
		if not os.path.exists(path):
			os.makedirs(path)

	def safe_remove_empty_dirpath(self, path):
		try:
			path = os.path.normcase(os.path.normpath(path))
			cwd  = os.path.normcase(os.path.normpath(os.getcwd()))
			if path not in cwd and os.path.exists(path) and not os.listdir(path):
				self.logger.debug("Removing directory:", path)
				os.rmdir(path)
				self.safe_remove_empty_dirpath(os.path.dirname(path))
		except Exception as error:
			self.logger.warning("Failed to remove directory {}, reason:".format(path), error)

	def safe_rmtree(self, dirpath):
		if os.path.exists(dirpath):
			self.logger.debug("Removing directory and its contents:", dirpath)
			def error_logger(function, path, excinfo):
				self.logger.warning("Failed to remove file {}, reason:".format(path), excinfo)
			shutil.rmtree(dirpath, onerror=error_logger)

	def safe_file_remove(self, filepath):
		try:
			if os.path.exists(filepath):
				self.logger.debug("Removing file:", filepath)
				os.remove(filepath)
		except Exception as error:
			self.logger.warning("Failed to remove file {}, reason:".format(filepath), error)

class InputFilesMixin(object):

	def __init__(self):
		super(InputFilesMixin, self).__init__()

	def get_input_files(self):
		output = []
		for input_path in self.config["input_files"]:
			input_path = self.expand_path(input_path)
			for input_filepath in glob.glob(input_path):
				output.append(input_filepath)
		return output

class TargetDirMixin(object):

	def __init__(self):
		super(TargetDirMixin, self).__init__()

	def get_target_dir(self):
		return self.expand_path(self.config["target_dir"])

class DefinesMixin(object):

	def __init__(self):
		super(DefinesMixin, self).__init__()

	def get_defines(self):
		output = {}
		for name, value in self.config["defines"].iteritems():
			output[name] = self.expand_value(value)
		return output

class InGenerateBuilder(AbstractBuilder, InputFilesMixin, TargetDirMixin, DefinesMixin):

	def __init__(self):
		super(InGenerateBuilder, self).__init__()

	def execute(self):
		self.create_dirpath(self.get_target_dir())
		for input_path in self.get_input_files():
			self.logger.debug("Processing:", os.path.relpath(input_path))

			# test for valid input
			assert os.path.isfile(input_path), "Input file does not exist: " + input_path
			assert input_path.endswith(".in"), "Input file is not a in-file: " + input_path

			# generate in-file to output file
			output_path = self.__transform_to_output_path(input_path)
			with open(input_path, "r") as input_file:
				with open(output_path, "w") as output_file:
					output_file.write(input_file.read().format(**self.get_defines()))

	def __transform_to_output_path(self, path):
		return os.path.join(self.get_target_dir(), os.path.basename(path)[:-3])

	def clean(self):
		for input_path in self.get_input_files():
			output_path = self.__transform_to_output_path(input_path)
			self.safe_file_remove(output_path)
			self.safe_remove_empty_dirpath(os.path.dirname(output_path))

class PythonCompileBuilder(AbstractBuilder, InputFilesMixin, TargetDirMixin):

	def __init__(self):
		super(PythonCompileBuilder, self).__init__()

	def initialize(self):
		self.dbg_dir = self.expand_value(self.config["dbg_dir"])

	def execute(self):
		self.create_dirpath(self.get_target_dir())
		for input_path in self.get_input_files():
			self.logger.debug("Compiling:", os.path.relpath(input_path))

			# test for valid input
			assert os.path.isfile(input_path), "Input file does not exist: " + input_path
			assert input_path.endswith(".py"), "Input file is not a python source file: " + input_path

			# compile python file
			output_path = self.__transform_to_output_path(input_path)
			dbg_filepath = self.__transform_to_debug_path(input_path)
			py_compile.compile(file=input_path, cfile=output_path, dfile=dbg_filepath, doraise=True)

	def __transform_to_output_path(self, path):
		return os.path.join(self.get_target_dir(), os.path.basename(path) + "c")

	def __transform_to_debug_path(self, path):
		return os.path.join(self.dbg_dir, os.path.basename(path)).replace("\\", "/").strip("/")

	def clean(self):
		for input_path in self.get_input_files():
			output_path = self.__transform_to_output_path(input_path)
			self.safe_file_remove(output_path)
			self.safe_remove_empty_dirpath(os.path.dirname(output_path))

class CopyBuilder(AbstractBuilder, InputFilesMixin, TargetDirMixin):

	def __init__(self):
		super(CopyBuilder, self).__init__()

	def execute(self):
		self.create_dirpath(self.get_target_dir())
		for input_path in self.get_input_files():
			self.logger.debug("Copying:", os.path.relpath(input_path))

			# test for valid input
			assert os.path.isfile(input_path), "Input file does not exist: " + input_path

			# copy file to its destination
			output_path = self.__transform_to_output_path(input_path)
			shutil.copyfile(input_path, output_path)

	def __transform_to_output_path(self, path):
		return os.path.join(self.get_target_dir(), os.path.basename(path))

	def clean(self):
		for input_path in self.get_input_files():
			output_path = self.__transform_to_output_path(input_path)
			self.safe_file_remove(output_path)
			self.safe_remove_empty_dirpath(os.path.dirname(output_path))

class CompressBuilder(AbstractBuilder):

	__archive_filepaths = set()

	def __init__(self):
		super(CompressBuilder, self).__init__()

	def initialize(self):
		self.__contents_dir = self.expand_path(self.config["contents_dir"])
		self.__archive_path = self.expand_path(self.config["archive_path"])
		self.__prefix = self.expand_path(self.config.get("prefix", ""))

	def deinitialize(self):
		self.__archive_filepaths.discard(self.__archive_path)

	def execute(self):
		if self.__archive_path in self.__archive_filepaths:
			self.logger.debug("Adding files to archive:", self.__archive_path)
			mode = "a"
		else:
			self.logger.debug("Creating archive:", self.__archive_path)
			mode = "w"

		assert os.path.exists(self.__contents_dir), \
			"Archive input contents directory doesn't exist, is '{}' correct?".format(self.config["contents_dir"])

		try:
			self.__archive_filepaths.add(self.__archive_path)

			self.create_dirpath(os.path.dirname(self.__archive_path))
			with warnings.catch_warnings(record=True) as warn_logs:
				with zipfile.ZipFile(self.__archive_path, mode) as package_file:
					for dirpath, dirnames, filenames in os.walk(self.__contents_dir):
						for filename in filenames:
							# form input file path
							input_filepath = os.path.join(dirpath, filename)
							# form output file path
							in_archive_filepath = os.path.join(self.__prefix, 
								input_filepath.replace(self.__contents_dir, "").strip(os.sep)).strip(os.sep)
							# compress to archive
							self.logger.debug("Compressing:", os.path.relpath(input_filepath))
							package_file.write(input_filepath, in_archive_filepath)
							while warn_logs:
								self.logger.warning(warn_logs.pop(0).message)
		except:
			self.logger.error("Creating archive", self.__archive_path, "failed")
			raise

	def clean(self):
		self.__archive_filepaths.discard(self.__archive_path)
		self.safe_file_remove(self.__archive_path)
		self.safe_remove_empty_dirpath(os.path.dirname(self.__archive_path))

class UncompressBuilder(AbstractBuilder, TargetDirMixin):

	def __init__(self):
		super(UncompressBuilder, self).__init__()

	def initialize(self):
		self.__archive_path = self.expand_path(self.config["archive_path"])

	def execute(self):
		assert os.path.exists(self.__archive_path), \
			"Archive file doesn't exist, is '{}' correct?".format(self.config["archive_path"])
		self.create_dirpath(self.get_target_dir())
		with zipfile.ZipFile(self.__archive_path, "r") as package_file:
			for input_path in package_file.namelist():
				self.logger.debug("Extracting:", input_path, "to", self.get_target_dir())
				package_file.extract(input_path, self.get_target_dir())

	def clean(self):
		raise NotImplementedError("uncompress builder's clean target is not yet implemented")

class QMakeBuilder(AbstractBuilder, DefinesMixin):

	def __init__(self):
		super(QMakeBuilder, self).__init__()

	def initialize(self):
		self.__architecture = self.config["architecture"]
		self.__source_dir = self.expand_path(self.config["source_dir"])
		self.__build_dir = self.expand_path(self.config["build_dir"])
		self.__qmake_path = self.expand_path(self.config["qmake_path"])
		self.__msvc_vars_path = self.expand_path(self.config["msvc_vars_path"])
		self.__output_dll_path = self.expand_path(self.config["output_dll_path"])
		self.__output_dbg_path = self.expand_path(self.config["output_dbg_path"])
		self.__batch_path = os.path.join(self.__build_dir, "build.bat")
		self.__threads = []

	def execute(self):
		self.logger.debug("Building:", self.__source_dir)

		assert os.path.exists(self.__source_dir), \
			"Source directory doesn't exist, is '{}' correct?".format(self.config["source_dir"])
		assert os.path.exists(self.__qmake_path), \
			"qmake.exe executable doesn't exist, is '{}' correct?".format(self.config["qmake_path"])
		assert os.path.exists(self.__msvc_vars_path), \
			"vcvarsall.bat batch file doesn't exist, is '{}' correct?".format(self.config["msvc_vars_path"])

		qmake_defs = dict(
			DLLDESTDIR             = ("=", os.path.dirname(self.__output_dll_path)),
			TARGET                 = ("=", os.path.splitext(os.path.basename(self.__output_dll_path))[0]),
			QMAKE_CXXFLAGS_RELEASE = ("+=", "/Fd\\\"{}\\\"".format(self.__output_dbg_path))
		)
		for name, value in self.get_defines().iteritems():
			qmake_defs[name] = ("=", value)

		self.create_dirpath(self.__build_dir)
		self.create_dirpath(os.path.dirname(self.__output_dbg_path))

		# create build batch file
		with open(self.__batch_path, "w") as file:
			file.write("@echo off\r\n")
			file.write("call \"{0}\" {1} \r\n".format(self.__msvc_vars_path, self.__architecture))
			file.write("\"{qmake}\" \"{source_dir}\" -after {qmake_defs}\r\n".format(
				qmake      = self.__qmake_path,
				source_dir = self.__source_dir,
				qmake_defs = " ".join("\"{0}{1}{2}\"".format(d, *qmake_defs[d]) for d in qmake_defs).replace("'", "\\'")
			))
			file.write("nmake\r\n")
		# execute the batch file
		proc = subprocess.Popen([self.__batch_path], cwd=self.__build_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout_queue = self.__stream_to_queue(proc.stdout)
		stderr_queue = self.__stream_to_queue(proc.stderr)
		try:
			while proc.poll() is None or not stdout_queue.empty() or not stderr_queue.empty():
				try:
					self.logger.debug(stdout_queue.get(timeout=0.01))
				except Queue.Empty:
					pass
				try:
					self.logger.debug(stderr_queue.get(timeout=0.01))
				except Queue.Empty:
					pass
		except KeyboardInterrupt:
			proc.terminate()

		for thread in self.__threads:
			thread.join()
		proc.wait()
		assert proc.returncode == 0, "Compiling failed"

	def __stream_to_queue(self, stream):
		queue = Queue.Queue()
		def run():
			for line in stream:
				try:
					queue.put(line.strip(), block=False)
				except Queue.Full:
					pass

		thread = threading.Thread(target=run)
		thread.start()
		return queue

	def clean(self):
		self.safe_rmtree(self.__build_dir)
		self.safe_file_remove(self.__output_dll_path)
		self.safe_remove_empty_dirpath(os.path.dirname(self.__output_dll_path))
		self.safe_file_remove(self.__output_dbg_path)
		self.safe_remove_empty_dirpath(os.path.dirname(self.__output_dbg_path))
		self.safe_remove_empty_dirpath(os.path.dirname(self.__build_dir))

class NoseTestsBuilder(AbstractBuilder):

	def __init__(self):
		super(NoseTestsBuilder, self).__init__()

	def initialize(self):
		self.__tests_dir = self.expand_path(self.config["tests_dir"])
		self.__tmp_dir = self.expand_path(self.config["tmp_dir"])

	def execute(self):
		self.logger.debug("Running tests")

		assert os.path.exists(self.__tests_dir), \
			"Tests directory doesn't exist, is '{}' correct?".format(self.config["tests_dir"])

		os.environ["TESTS_TEMP_DIR"] = self.__tmp_dir
		result = nose.run(
			argv=[
				"",
				self.__tests_dir,
				"--with-process-isolation",
				"--with-process-isolation-individual"
			]
		);
		assert result, "Unit tests execution failed"

	def clean(self):
		self.safe_rmtree(self.__tmp_dir)
		self.safe_remove_empty_dirpath(os.path.dirname(self.__tmp_dir))

class TailFileBuilder(AbstractBuilder):

	def __init__(self):
		super(TailFileBuilder, self).__init__()

	def initialize(self):
		self.__filepath = self.expand_path(self.config["filepath"])

	def execute(self):
		self.logger.info("Tailing '{}', press Ctrl+C to cancel".format(self.__filepath))
		try:
			with open(self.__filepath, "r") as file:
				for line in tailer.follow(file):
					self.logger.info(line)
		except KeyboardInterrupt:
			pass

	def clean(self):
		# empty
		pass

init()
