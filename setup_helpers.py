from distutils.command.clean import clean
from distutils.dir_util import remove_tree
from setuptools.command.build_py import build_py
from setuptools import Command

from glob import glob
import os
import zipfile

class GenerateInFilesCommand(build_py):
	'''
	Converts .py.in files to .py files.
	'''

	def run(self):
		self._outputs = []
		options = {name[4:]: method() for name, method in self.distribution.__dict__.items() if name.startswith('get_')}
		if self.packages:
			for package in self.packages:
				package_dir = self.get_package_dir(package)
				module_files = glob(os.path.join(package_dir, "*.py.in"))
				for module_file in module_files:
					package = package.split('.')
					module = os.path.basename(module_file).split('.')[0]
					outfile = self.get_module_outfile(self.build_lib, package, module)
					self._outputs.append(outfile)
					self.mkpath(os.path.dirname(outfile))
					with open(module_file, 'r') as input_file:
						with open(outfile, 'w') as output_file:
							output_file.write(input_file.read().format(**options))
		build_py.run(self)

	def byte_compile(self, files):
		return build_py.byte_compile(self, files + self._outputs)

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
				filepath = os.path.join(root, name)
				if os.path.splitext(filepath)[1] == ".pyc":
					os.remove(filepath)


class PackageCommand(Command):
	'''
	A command to create release package.
	'''

	user_options = [
		("dist-dir=", "d", "destination directory for the release package (cwd by default)"),
	]

	def initialize_options(self):
		self.dist_dir = None

	def finalize_options(self):
		if self.dist_dir is None:
			self.dist_dir = os.getcwd()

	def run(self):
		wotmod_filepath = self.create_wotmod_file()
		self.create_release_file(wotmod_filepath)

	def create_wotmod_file(self):
		self.distribution.run_command('clean')
		self.distribution.run_command('bdist_wotmod')
		bdist_wotmod = self.distribution.get_command_obj('bdist_wotmod')

		# TODO: Copied from bdist_wotmod. Should instead add a method to the
		#       bdist_wotmod command class for asking the path programmatically.
		wotmod_filename = "%s.%s_%s.wotmod" % (
			bdist_wotmod.author_id, bdist_wotmod.mod_id, bdist_wotmod.mod_version)
		return os.path.abspath(os.path.join(bdist_wotmod.dist_dir, wotmod_filename))

	def create_release_file(self, wotmod_filepath):
		wotmod_filename = os.path.basename(wotmod_filepath)

		readme_src_filepath = os.path.join(os.path.dirname(__file__), "docs", "install-readme.txt")
		readme_dst_filename = "README"

		# Resolve the path where the release file will be written to
		release_filename = "tessumod-%s.zip" % self.distribution.get_version()
		release_filepath = os.path.join(self.dist_dir, release_filename)

		# Create the release file
		self.mkpath(self.dist_dir)
		with zipfile.ZipFile(release_filepath, 'w', zipfile.ZIP_DEFLATED) as release_file:
			release_file.write(readme_src_filepath, "tessumod/%s" % readme_dst_filename)
			release_file.write(wotmod_filepath, "tessumod/%s" % wotmod_filename)
