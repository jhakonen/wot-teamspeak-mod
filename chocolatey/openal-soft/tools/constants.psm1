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

$ROOTPATH        = "$PSScriptRoot\.."
$CHOCOREPOPATH   = "$ROOTPATH\..\..\chocolatey-repo"
$INSTALLPATH     = "C:\OpenAL-Soft"
$SOURCEPATH      = "$INSTALLPATH\src"
$BUILDPATH32     = "$INSTALLPATH\bin-32"
$BUILDPATH64     = "$INSTALLPATH\bin-64"
$ARCHIVEFILEPATH = "$ROOTPATH\archive.zip"
$MSVCPATH        = "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC"
$GITURL          = "https://github.com/kcat/openal-soft.git"

Export-ModuleMember -Variable *
