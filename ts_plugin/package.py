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
	target           = "tessumod_plugin_" + arch
	build_dir        = os.path.join(BUILD_DIR, arch)
	batch_path       = os.path.join(build_dir, "build.bat")
	binary_file_path = os.path.join(build_dir, target + ".dll")
	debug_file_path  = os.path.join(build_dir, target + ".pdb")
	# create empty build dir
	if os.path.isdir(build_dir):
		shutil.rmtree(build_dir)
	os.makedirs(build_dir)
	# create build batch file
	with open(batch_path, "w") as file:
		file.write("@echo off\r\n")
		file.write("call \"{0}\" {1} \r\n".format(get_vcvarsall_path(), arch_to_vcvars_arg(arch)))
		file.write("\"{qtdir}\\bin\qmake.exe\" {source_dir} -after \"DLLDESTDIR={build_dir}\" \"TARGET={target}\" \"QMAKE_CXXFLAGS_RELEASE+=/Fd{target}.pdb\"\r\n".format(
			qtdir      = qtdir,
			source_dir = SOURCE_DIR,
			build_dir  = build_dir,
			target     = target
		))
		file.write("nmake\r\n")
	# execute the batch file
	proc = subprocess.Popen([batch_path], cwd=build_dir)
	proc.communicate()
	# verify results
	if proc.returncode != 0:
		raise RuntimeError("Build failed")
	if not os.path.isfile(binary_file_path):
		raise RuntimeError("Build binary file not found")
	if not os.path.isfile(debug_file_path):
		raise RuntimeError("Build debug file not found")
	return binary_file_path, debug_file_path

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

def build_debug_archive(archive_path, files):
	archive = zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, False)
	for file_archive_path, source_path in files.iteritems():
		archive.write(source_path, file_archive_path)
	archive.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--version", nargs=1, help="version of the TS plugin", required=True)
	parser.add_argument("--qtdir86", nargs=1, help="path to 32bit QT dir", required=True)
	parser.add_argument("--qtdir64", nargs=1, help="path to 64bit QT dir", required=True)
	parser.add_argument("--installerpath", nargs=1, help="path to installer file", required=True)
	parser.add_argument("--debugarchivepath", nargs=1, help="path to debug archive file", required=True)
	args = parser.parse_args()

	x86_bin_path, x86_dbg_path = build_ts_plugin_binary(args.qtdir86[0], "x86")
	x64_bin_path, x64_dbg_path = build_ts_plugin_binary(args.qtdir64[0], "x64")

	build_ts_installer(
		installer_name = args.installerpath[0],
		name = "TessuMod Plugin",
		type = "Plugin",
		author = "Janne Hakonen (jhakonen @ WOT EU server)",
		version = args.version[0],
		platforms = ["win32", "win64"],
		description = "This plugin provides positional audio support for World of Tanks.",
		files = {
			"plugins\\" + os.path.basename(x86_bin_path): x86_bin_path,
			"plugins\\" + os.path.basename(x64_bin_path): x64_bin_path,
			"plugins\\tessumod_plugin\\OpenAL32.dll": os.path.join(SOURCE_DIR, "libs", "OpenAL32.dll"),
			"plugins\\tessumod_plugin\\OpenAL64.dll": os.path.join(SOURCE_DIR, "libs", "OpenAL64.dll")
		}
	)

	build_debug_archive(
		archive_path = args.debugarchivepath[0],
		files = {
			os.path.basename(x86_dbg_path): x86_dbg_path,
			os.path.basename(x64_dbg_path): x64_dbg_path,
			"OpenAL32.pdb": os.path.join(SOURCE_DIR, "libs", "OpenAL32.pdb"),
			"OpenAL64.pdb": os.path.join(SOURCE_DIR, "libs", "OpenAL64.pdb")
		}
	)
