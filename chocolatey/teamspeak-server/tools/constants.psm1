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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

$ROOTPATH      = "$PSScriptRoot\.."
$REPOPATH      = "$ROOTPATH\..\..\chocolatey-repo"
$ARCHIVEPATH   = "$ROOTPATH\archive.zip"
$ARCHIVEURL    = "http://dl.4players.de/ts/releases/3.0.13/teamspeak3-server_win64-3.0.13.zip"
$INSTALLPATH   = "C:"
$INSTALLEDPATH = "$INSTALLPATH\teamspeak3-server_win64"

Export-ModuleMember -Variable *
