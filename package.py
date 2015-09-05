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

import py_compile, zipfile, os, fnmatch
import subprocess
import re
import shutil

# configuration
MOD_VERSION        = "0.6.3"
ROOT_DIR           = os.path.dirname(os.path.realpath(__file__))
BUILD_DIR          = os.path.join(os.getcwd(), "build")
MOD_PACKAGE_PATH   = os.path.join(os.getcwd(), "tessumod-{0}-bin.zip".format(MOD_VERSION))
DEBUG_ARCHIVE_PATH = os.path.join(os.getcwd(), "tessumod-{0}-dbg.zip".format(MOD_VERSION))

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

def package_ts_plugin(build_dir):
	create_dir(build_dir)
	proc = subprocess.Popen([
		"python",
		os.path.join(ROOT_DIR, "tsplugin", "package.py"),
		"--version=" + MOD_VERSION
	], cwd=build_dir, stdout=subprocess.PIPE)
	out = proc.communicate()[0]
	if proc.returncode != 0:
		print out
		raise RuntimeError("TS plugin packaging failed")
	return (
		re.search("^Installer file path: (.+)$", out, re.MULTILINE).group(1).strip(),
		re.search("^Debug archive file path: (.+)$", out, re.MULTILINE).group(1).strip()
	)

def package_tessumod(build_dir):
	create_dir(build_dir)
	proc = subprocess.Popen([
		"python",
		os.path.join(ROOT_DIR, "tessumod", "package.py"),
		"--mod-version=" + MOD_VERSION
	], cwd=build_dir, stdout=subprocess.PIPE)
	out = proc.communicate()[0]
	if proc.returncode != 0:
		print out
		raise RuntimeError("TessuMod packaging failed")
	return (
		re.search("^Package file path: (.+)$", out, re.MULTILINE).group(1).strip(),
		re.search("^Package root path: (.+)$", out, re.MULTILINE).group(1).strip()
	)

remove_file(MOD_PACKAGE_PATH)
remove_file(DEBUG_ARCHIVE_PATH)
remove_dir(BUILD_DIR)

plugin_installer_path, plugin_debug_path = package_ts_plugin(os.path.join(BUILD_DIR, "tsplugin"))
package_path, package_root_path = package_tessumod(os.path.join(BUILD_DIR, "tessumod"))

shutil.copy(plugin_debug_path, DEBUG_ARCHIVE_PATH)
shutil.copy(package_path, MOD_PACKAGE_PATH)

with zipfile.ZipFile(MOD_PACKAGE_PATH, "a") as package_file:
	package_file.write(plugin_installer_path, os.path.join(package_root_path, os.path.basename(plugin_installer_path)))
