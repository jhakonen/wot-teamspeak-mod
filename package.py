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

# configuration
WOT_VERSION = "0.9.4"
MOD_VERSION = "0.5.0"
CLIENT_PACKAGE_DIR = os.path.join("res_mods", WOT_VERSION, "scripts", "client")
BUILD_DIR = os.path.join(os.getcwd(), "build")
SRC_DIR = os.path.join(os.getcwd(), "src")
PACKAGE_NAME = "TessuMod-{0}.zip".format(MOD_VERSION)
SUPPORT_URL = "http://forum.worldoftanks.eu/index.php?/topic/433614-/"

IN_FILES = {
	"build_info.py.in": dict(
		MOD_VERSION = MOD_VERSION,
		SUPPORT_URL = SUPPORT_URL
	),
	"TessuMod.txt.in": dict(
		SUPPORT_URL = SUPPORT_URL
	)
}

QTDIR_X86  = "E:\\Qt\\Qt5.2.1\\5.2.1\\msvc2012"
QTDIR_X64  = "E:\\Qt\\Qt5.2.1\\5.2.1\\msvc2012_64"

def process_in_file(source_dir, filename, params, destination_dir):
	in_path  = os.path.join(source_dir, filename)
	out_path = os.path.join(destination_dir, filename.replace(".in", ""))
	with open(in_path, "r") as in_file, open(out_path, "w") as out_file:
		out_file.write(in_file.read().format(**params))
	return out_path

def create_ts_plugin_installer(output_path):
	proc = subprocess.Popen([
		"python",
		os.path.join(os.getcwd(), "ts_plugin", "package.py"),
		"--version=" + MOD_VERSION,
		"--qtdir86=" + QTDIR_X86,
		"--qtdir64=" + QTDIR_X64,
		"--output=" + output_path
	], cwd=build_dir)
	proc.communicate()
	if proc.returncode != 0:
		raise RuntimeError("TS plugin installer creation failed")
	if not os.path.isfile(output_path):
		raise RuntimeError("Created installer not found")
	return output_path

# compile .py files from src/ and output .pyc files to /build
for root, dirs, files in os.walk(SRC_DIR):
	src_dir = root
	root2 = root[len(SRC_DIR)+1:]
	build_dir = os.path.join(BUILD_DIR, root2) if root2 else BUILD_DIR

	if not os.path.exists(build_dir):
		os.mkdir(build_dir)

	# convert .in-files and compile if necessary
	for filename in IN_FILES:
		if filename in files:
			out_path = process_in_file(src_dir, filename, IN_FILES[filename], build_dir)
			if out_path.endswith(".py"):
				py_compile.compile(file=out_path, cfile=out_path+"c", doraise=True)

	for filename in fnmatch.filter(files, "*.py"):
		# ignore unit test files
		if filename.endswith("_test.py"):
			continue
		py_compile.compile(file=os.path.join(src_dir, filename), cfile=os.path.join(build_dir, filename)+"c", doraise=True)

# remove old archive if one exists
if os.path.exists(PACKAGE_NAME):
	os.remove(PACKAGE_NAME)

# create zip archive and compress TessuMod.txt and files from build/ to the archive
fZip = zipfile.ZipFile(PACKAGE_NAME, "w")
fZip.write(os.path.join(BUILD_DIR, "TessuMod.txt"), "TessuMod.txt")
for root, dirs, files in os.walk(BUILD_DIR):
	source_dir = root
	root2 = root[len(BUILD_DIR)+1:]
	target_dir = os.path.join(CLIENT_PACKAGE_DIR, root2)

	for filename in fnmatch.filter(files, "*.pyc"):
		fZip.write(os.path.join(source_dir, filename), os.path.join(target_dir, filename))
fZip.write(create_ts_plugin_installer(os.path.join(BUILD_DIR, "TessuModPlugin.ts3_plugin")), "TessuModPlugin.ts3_plugin")
fZip.close()
