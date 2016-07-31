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

$ROOTPATH         = "$PSScriptRoot\.."
$REPOPATH         = "$ROOTPATH\..\..\chocolatey-repo"
$PACKAGENAME      = "qt-everywhere-opensource.5.5.1.nupkg"
$PACKAGEBUILDPATH = "$ROOTPATH\$PACKAGENAME"
$PACKAGEREPOPATH  = "$REPOPATH\$PACKAGENAME"
$OUTARCHIVEPATH   = "$ROOTPATH\archive.zip"
$QTARCHIVEURL     = "http://download.qt.io/archive/qt/5.5/5.5.1/single/qt-everywhere-opensource-src-5.5.1.7z"
$MSVCPATH         = "C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC"
$JOMPATH          = "$env:ChocolateyInstall\lib\jom\tools\jom.exe"
$7ZIPPATH         = "C:\Program Files\7-Zip\7z.exe"
$BUILDPATH        = "$env:TEMP\build"
$QTROOTPATH       = "C:\Qt"
$QTSOURCEPATH     = "$QTROOTPATH\src"
$QT32PATH         = "$QTROOTPATH\bin-32"
$QT64PATH         = "$QTROOTPATH\bin-64"

Export-ModuleMember -Variable *
