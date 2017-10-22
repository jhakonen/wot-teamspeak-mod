# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
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
import re
import shutil
import subprocess
import urllib2
import zipfile

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

def execute():
	# configuration
	BUILD_DIR        = os.path.join(os.getcwd(), "build")
	DIST_DIR         = os.path.join(os.getcwd(), "dist")
	PLUGIN_URL       = "https://github.com/jhakonen/wot-teamspeak-mod/releases/download/ts-3.1.1/tessumod.ts3_plugin"
	MOD_VERSION      = get_tessumod_version()
	MOD_PACKAGE_PATH = os.path.join(os.getcwd(), "tessumod-{0}-bin.zip".format(MOD_VERSION))
	# create release archive
	remove_file(MOD_PACKAGE_PATH)
	remove_dir(BUILD_DIR)
	remove_dir(DIST_DIR)
	package_tessumod(BUILD_DIR, os.path.join(DIST_DIR, "tessumod"))
	download_file(PLUGIN_URL, os.path.join(DIST_DIR, "tessumod", "tessumod.ts3_plugin"))
	shutil.copyfile(os.path.join(ROOT_DIR, "tessumod", "README"), os.path.join(DIST_DIR, "tessumod", "README"))
	create_release(DIST_DIR, MOD_PACKAGE_PATH)

def remove_file(file_path):
	try:
		os.remove(file_path)
	except:
		pass

def remove_dir(dir_path):
	try:
		shutil.rmtree(dir_path)
	except:
		pass

def create_dir(dir_path):
	try:
		os.makedirs(dir_path)
	except:
		pass

def get_tessumod_version():
	result = run_tessumod_setup("--quiet", "--version").strip()
	# Command may produce garbage even with --quiet, so try to parse version
	# string from output, likely to be last match in it
	return re.findall("[\d.]+", result)[-1]

def package_tessumod(build_dir, dist_dir):
	run_tessumod_setup(
		"build", "--build-base=%s" % build_dir,
		"bdist_wotmod", "--dist-dir=%s" % dist_dir
	)

def run_tessumod_setup(*args):
	proc = subprocess.Popen(["python", "setup.py"] + list(args),
		cwd = os.path.join(ROOT_DIR, "tessumod"),
		stdout = subprocess.PIPE,
		stderr = subprocess.STDOUT
	)
	out = proc.communicate()[0]
	if proc.returncode != 0:
		print out
		raise RuntimeError("TessuMod packaging failed")
	return out

def download_file(url, target):
	with open(target, "wb") as target_file:
		target_file.write(urllib2.urlopen(url).read())

def create_release(source_dir, release_path):
	with zipfile.ZipFile(release_path, "w") as package_file:
		for root, dirs, files in os.walk(source_dir):
			for filename in files:
				filepath = os.path.join(root, filename)
				# Build relative path from bdist_dir forward
				arcpath = filepath.replace(os.path.commonprefix(
					[source_dir, filepath]), '').strip('/')
				package_file.write(filepath, arcpath)

execute()
