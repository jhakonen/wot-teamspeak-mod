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

$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

# Initial cleanup
Remove-Item $ARCHIVEPATH -ErrorAction SilentlyContinue

Write-Host "Downloading '$ARCHIVEURL'..."
(new-object net.webclient).DownloadFile($ARCHIVEURL, $ARCHIVEPATH)
if (-Not (Test-Path $ARCHIVEPATH)) {
	Throw "Failed to download '$ARCHIVEURL'"
}

# Create Chocolatey package
Write-Host "Creating Chocolatey package '$PACKAGEBUILDPATH'..."
pushd $ROOTPATH
choco pack
popd
if (-Not (Test-Path $PACKAGEBUILDPATH)) {
	Throw "Failed to pack"
}

# Store new Chocolatey package to local repo
Write-Host "Moving Chocolatey package to '$PACKAGEREPOPATH'..."
New-Item -ItemType Directory -Path $REPOPATH -Force | Out-Null
Move-Item $PACKAGEBUILDPATH $PACKAGEREPOPATH -Force

# Final cleanup
Write-Host "Cleaning up..."
Remove-Item $ARCHIVEPATH
