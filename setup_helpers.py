from distutils.command.clean import clean
from distutils.dir_util import remove_tree
from setuptools.command.build_py import build_py

import os
from glob import glob

class GenerateInFilesCommand(build_py):
	'''
	Converts .py.in files to .py files.
	'''

	def run(self):
		options = {name[4:]: method() for name, method in self.distribution.__dict__.iteritems() if name.startswith('get_')}
		if self.packages:
			for package in self.packages:
				package_dir = self.get_package_dir(package)
				module_files = glob(os.path.join(package_dir, "*.py.in"))
				for module_file in module_files:
					package = package.split('.')
					module = os.path.basename(module_file).split('.')[0]
					outfile = self.get_module_outfile(self.build_lib, package, module)
					self.mkpath(os.path.dirname(outfile))
					with open(module_file, 'r') as input_file:
						with open(outfile, 'w') as output_file:
							output_file.write(input_file.read().format(**options))
		build_py.run(self)

class CleanCommand(clean):
	'''
	Like normal distutils clean command, but with more throughout cleaning and
	less complaining.
	'''
	def run(self):
		clean_directories = (
			self.build_temp,
			self.build_lib,
			self.bdist_base,
			self.build_scripts,
			"tmp",
			"tessumod.egg-info",
			"dist"
		)
		for directory in clean_directories:
			if os.path.exists(directory):
				remove_tree(directory, dry_run=self.dry_run)
		for root, dirs, files in os.walk("."):
			for name in files:
				file_path = os.path.join(root, name)
				if os.path.splitext(file_path)[1] == ".pyc":
					os.remove(file_path)
