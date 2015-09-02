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
import glob
import sys

BUILD_DIR  = os.getcwd()
SOURCE_DIR = os.path.dirname(os.path.realpath(__file__))
PLUGIN_INSTALLER_PATH  = os.path.join(BUILD_DIR, "tessumod.ts3_plugin")
DEBUG_SYMBOL_FILE_PATH = os.path.join(BUILD_DIR, "debug-symbols.zip")

PACKAGE_INI_TEMPLATE = """
Name = {name}\r
Type = {type}\r
Author = {author}\r
Version = {version}\r
Platforms = {platforms}\r
Description = "{description}"\r
"""

def build_ts_plugin_binary(qtdir, arch, name, description, author, version, **kwargs):
	target           = "tessumod_plugin_" + arch
	build_dir        = os.path.join(BUILD_DIR, arch)
	batch_path       = os.path.join(build_dir, "build.bat")
	binary_file_path = os.path.join(build_dir, target + ".dll")
	debug_file_path  = os.path.join(build_dir, target + ".pdb")
	qmake_defs       = dict(
		DLLDESTDIR             = ("=", build_dir),
		TARGET                 = ("=", target),
		QMAKE_CXXFLAGS_RELEASE = ("+=", "/Fd{0}.pdb".format(target)),
		PLUGIN_NAME            = ("=", name),
		PLUGIN_DESCRIPTION     = ("=", description),
		PLUGIN_AUTHOR          = ("=", author),
		PLUGIN_VERSION         = ("=", version)
	)
	# create empty build dir
	if os.path.isdir(build_dir):
		shutil.rmtree(build_dir)
	os.makedirs(build_dir)
	# create build batch file
	with open(batch_path, "w") as file:
		file.write("@echo off\r\n")
		file.write("call \"{0}\" {1} \r\n".format(get_vcvarsall_path(), arch_to_vcvars_arg(arch)))
		file.write("\"{qtdir}\\bin\qmake.exe\" {source_dir} -after {qmake_defs}\r\n".format(
			qtdir      = qtdir,
			source_dir = SOURCE_DIR,
			qmake_defs = " ".join("\"{0}{1}{2}\"".format(d, *qmake_defs[d]) for d in qmake_defs).replace("'", "\\'")
		))
		file.write("nmake\r\n")
	# execute the batch file
	proc = subprocess.Popen([batch_path], cwd=build_dir, stderr=subprocess.PIPE)
	while proc.poll() is None:
		output = proc.stderr.readline()
		# filter out warnings when compiling in Windows 10
		if "Qt: Untested Windows version 10.0 detected!" in output:
			pass
		else:
			sys.stderr.write(output)
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

def build_ts_installer(installer_path, name, type, author, version, platforms, description, files):
	with zipfile.ZipFile(installer_path, "w", zipfile.ZIP_DEFLATED, False) as archive:
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
		print "Installer file path:", installer_path

def build_debug_archive(archive_path, files):
	with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, False) as archive:
		for file_archive_path, source_path in files.iteritems():
			archive.write(source_path, file_archive_path)
	print "Debug archive file path:", archive_path

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--version", help="version of the TS plugin", required=True)
	args = parser.parse_args()

	if not os.getenv("QTDIR_X86"):
		raise RuntimeError("QTDIR_X86 environment variable not defined!")
	if not os.getenv("QTDIR_X64"):
		raise RuntimeError("QTDIR_X64 environment variable not defined!")

	info = dict(
		name        = "TessuMod Plugin",
		author      = "Janne Hakonen (jhakonen @ WOT EU server)",
		version     = args.version,
		description = "This plugin provides support for 3D audio, with help of TessuMod, it positions users voice in TeamSpeak so that their voices appear to come from their vehicle's direction on battlefield.",
		type        = "Plugin",
		platforms   = ["win32", "win64"]
	)

	x86_bin_path, x86_dbg_path = build_ts_plugin_binary(os.getenv("QTDIR_X86"), "x86", **info)
	x64_bin_path, x64_dbg_path = build_ts_plugin_binary(os.getenv("QTDIR_X64"), "x64", **info)

	files = {
		"plugins\\" + os.path.basename(x86_bin_path): x86_bin_path,
		"plugins\\" + os.path.basename(x64_bin_path): x64_bin_path,
		"plugins\\tessumod_plugin\\alsoft.ini": os.path.join(SOURCE_DIR, "etc", "alsoft.ini"),
		"plugins\\tessumod_plugin\\testsound.wav": os.path.join(SOURCE_DIR, "audio", "testsound.wav")
	}
	files.update({ "plugins\\tessumod_plugin\\" + os.path.basename(filepath): filepath for filepath in glob.glob(os.path.join(SOURCE_DIR, "libs", "OpenAL*.dll")) })
	files.update({ "plugins\\tessumod_plugin\\" + os.path.basename(filepath): filepath for filepath in glob.glob(os.path.join(SOURCE_DIR, "etc", "hrtfs", "*.mhr")) })

	build_ts_installer(
		installer_path = PLUGIN_INSTALLER_PATH,
		files = files,
		**info
	)

	build_debug_archive(
		archive_path = DEBUG_SYMBOL_FILE_PATH,
		files = {
			os.path.basename(x86_dbg_path): x86_dbg_path,
			os.path.basename(x64_dbg_path): x64_dbg_path,
			"OpenAL32.pdb": os.path.join(SOURCE_DIR, "libs", "OpenAL32.pdb"),
			"OpenAL64.pdb": os.path.join(SOURCE_DIR, "libs", "OpenAL64.pdb")
		}
	)
