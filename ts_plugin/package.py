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

import subprocess
import os
import shutil
import _winreg
import argparse
import zipfile

BUILD_DIR  = os.getcwd()
SOURCE_DIR = os.path.dirname(os.path.realpath(__file__))

PACKAGE_INI_TEMPLATE = """
Name = {name}\r
Type = {type}\r
Author = {author}\r
Version = {version}\r
Platforms = {platforms}\r
Description = {description}\r
"""

def build_ts_plugin_binary(qtdir, arch):
	build_dir  = os.path.join(BUILD_DIR, arch)
	batch_path = os.path.join(build_dir, "build.bat")
	output_file_path = os.path.join(build_dir, "tessumod_plugin.dll")
	# create empty build dir
	if os.path.isdir(build_dir):
		shutil.rmtree(build_dir)
	os.makedirs(build_dir)
	# create build batch file
	with open(batch_path, "w") as file:
		file.write("@echo off\r\n")
		file.write("call \"{0}\" {1} \r\n".format(get_vcvarsall_path(), arch_to_vcvars_arg(arch)))
		file.write("\"{qtdir}\\bin\qmake.exe\" {source_dir} -after \"DLLDESTDIR={build_dir}\"\r\n".format(
			qtdir=qtdir,
			source_dir=SOURCE_DIR,
			build_dir=build_dir
		))
		file.write("nmake\r\n")
	# execute the batch file
	proc = subprocess.Popen([batch_path], cwd=build_dir)
	proc.communicate()
	# verify results
	if proc.returncode != 0:
		raise RuntimeError("Build failed")
	if not os.path.isfile(output_file_path):
		raise RuntimeError("Build output file not found")
	return output_file_path

def get_vcvarsall_path():
	key = _winreg.OpenKeyEx(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\VisualStudio\\11.0\\Setup\\VC")
	path = _winreg.QueryValueEx(key, "ProductDir")[0]
	return os.path.abspath(path + "\\" + "vcvarsall.bat")

def arch_to_vcvars_arg(arch):
	if arch == "x86":
		return "x86"
	elif arch == "x64":
		return "x86_amd64"
	raise RuntimeError("Unknown architecture")

def build_ts_installer(installer_name, name, type, author, version, platforms, description, files):
	archive = zipfile.ZipFile(installer_name, "w", zipfile.ZIP_DEFLATED, False)
	archive.writestr("package.ini", PACKAGE_INI_TEMPLATE.format(
		name        = name,
		type        = type,
		author      = author,
		version     = version,
		platforms   = ", ".join(platforms),
		description = description
	))
	for archive_path, source_path in files.iteritems():
		archive.write(source_path, archive_path)
	archive.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--version", nargs=1, help="version of the TS plugin", required=True)
	parser.add_argument("--qtdir86", nargs=1, help="path to 32bit QT dir", required=True)
	parser.add_argument("--qtdir64", nargs=1, help="path to 64bit QT dir", required=True)
	parser.add_argument("--output", nargs=1, help="path to installer file", required=True)
	args = parser.parse_args()

	build_ts_installer(
		installer_name = args.output[0],
		name = "TessuMod Plugin",
		type = "Plugin",
		author = "Janne Hakonen (jhakonen @ WOT EU server)",
		version = args.version[0],
		platforms = ["win32", "win64"],
		description = "This plugin provides positional audio support for World of Tanks.",
		files = {
			"plugins\\tessumod_plugin_x86.dll": build_ts_plugin_binary(args.qtdir86[0], "x86"),
			"plugins\\tessumod_plugin_x64.dll": build_ts_plugin_binary(args.qtdir64[0], "x64"),
			"plugins\\tessumod_plugin\\OpenAL32.dll": os.path.join(SOURCE_DIR, "libs", "OpenAL32.dll"),
			"plugins\\tessumod_plugin\\OpenAL64.dll": os.path.join(SOURCE_DIR, "libs", "OpenAL64.dll")
		}
	)
