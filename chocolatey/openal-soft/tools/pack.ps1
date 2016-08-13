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

# Returns the current environment.
# From http://windowsitpro.com/powershell/take-charge-environment-variables-powershell
function Get-Environment {
    get-childitem Env:
}

# Restores the environment to a previous state.
# From http://windowsitpro.com/powershell/take-charge-environment-variables-powershell
function Restore-Environment([System.Collections.DictionaryEntry[]]$oldEnv) {
    # Removes any added variables.
    Compare-Object $oldEnv $(Get-Environment) -property Key -passthru |
        Where-Object { $_.SideIndicator -eq "=>" } |
            Foreach-Object { Remove-Item Env:$($_.Name) }
    # Reverts any changed variables to original values.
    Compare-Object $oldEnv $(Get-Environment) -property Value -passthru |
        Where-Object { $_.SideIndicator -eq "<=" } |
            Foreach-Object { Set-Item Env:$($_.Name) $_.Value }
}

function Compile-OpenAL([string]$BuildPath, [string]$LibName, [string]$Architecture) {
    Write-Host "Setting up build environment for '$Architecture' architecture"
    $oldEnv = Get-Environment
    Push-Location $MSVCPATH
    cmd /c "vcvarsall.bat $Architecture & set" |
        foreach {
            if ($_ -match "=") {
                $v = $_.split("="); Set-Item -Force -Path "ENV:\$($v[0])" -Value "$($v[1])"
            }
        }
    Pop-Location

    Write-Host "Building OpenAL Soft..."
    Push-Location $BuildPath
    cmake -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=RelWithDebInfo "-DLIBNAME=$LibName" -DALSOFT_BACKEND_WINMM=OFF -DALSOFT_BACKEND_MMDEVAPI=OFF -DALSOFT_BACKEND_WAVE=OFF $SOURCEPATH
    nmake
    Pop-Location

    Write-Host "Tearing down build environment"
    Restore-Environment -oldEnv $oldEnv
}

function Cleanup {
    Remove-Item $SOURCEPATH -Recurse -ErrorAction SilentlyContinue
    Remove-Item $BUILDPATH32 -Recurse -ErrorAction SilentlyContinue
    Remove-Item $BUILDPATH64 -Recurse -ErrorAction SilentlyContinue
    Remove-Item $ARCHIVEFILEPATH -ErrorAction SilentlyContinue
}

$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

# pre-cleanup to make sure no build artifacts remain from previous build run
Cleanup

New-Item -ItemType Directory -Path $SOURCEPATH
New-Item -ItemType Directory -Path $BUILDPATH32
New-Item -ItemType Directory -Path $BUILDPATH64

# Get sources and apply patch
git clone $GITURL $SOURCEPATH
Push-Location $SOURCEPATH
git checkout openal-soft-1.16.0
git apply "$ROOTPATH\changes.patch"
Remove-Item "$SOURCEPATH\.git" -Recurse -Force -ErrorAction SilentlyContinue
Pop-Location

# Compile OpenAL
Compile-OpenAL -BuildPath $BUILDPATH32 -LibName OpenAL32 -Architecture x86
Compile-OpenAL -BuildPath $BUILDPATH64 -LibName OpenAL64 -Architecture x86_amd64

# Create release archive which will be included within the nupkg file
Compress-Archive -Path "$INSTALLPATH\*" -CompressionLevel Fastest -DestinationPath $ARCHIVEFILEPATH

# Create nupkg file
Push-Location $ROOTPATH
choco pack
Pop-Location

# Move resulting nupkg file to local chocolatey repo
New-Item -ItemType Directory -Path $CHOCOREPOPATH -Force | Out-Null
Move-Item "$ROOTPATH\*.nupkg" "$CHOCOREPOPATH" -Force

# Final cleanup
Cleanup
