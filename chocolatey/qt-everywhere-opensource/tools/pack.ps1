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

function DownloadToTemp([string]$url) {
    $private:DestinationPath = Join-Path $env:Temp ($url -split "/" | Select-Object -Last 1)
    Remove-Item $private:DestinationPath -ErrorAction SilentlyContinue
    (new-object net.webclient).DownloadFile($url, $private:DestinationPath)
    if (-Not (Test-Path $private:DestinationPath)) {
        Throw "Failed to download '$url'"
    }
    $private:DestinationPath
}

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

function Compress-Archive([string]$source, [string]$destination) {
    & $7ZIPPATH "a" $destination $source "-y" | Out-Null
}

function BuildQt([string]$Architecture, [string]$InstallPrefix, [string]$SourcePath) {

    Remove-Item $BUILDPATH -Recurse -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $BUILDPATH -Force | Out-Null

    Remove-Item $InstallPrefix -Recurse -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $InstallPrefix -Force | Out-Null

    # Sanity checks
    if (-Not(Test-Path $SourcePath)) {
        Throw "Qt sources not available, cannot compile Qt libraries"
    }
    if (-Not(Test-Path $MSVCPATH)) {
        Throw "Visual Studio 2013 not available, cannot compile Qt libraries"
    }
    if (-Not(Test-Path $JOMPATH)) {
        Throw "Jom not available, cannot compile Qt libraries"
    }
    if (-Not(Test-Path $InstallPrefix)) {
        Throw "Install prefix failed to create, cannot compile Qt libraries"
    }

    $oldEnv = Get-Environment

    # Setup Qt environment
    $env:path = "$BUILDPATH\gnuwin32\bin;" + $env:path
    $env:path = "$BUILDPATH\qtbase\bin;" + $env:path
    $env:QMAKESPEC = "win32-msvc2013"

    # Setup VS2013 compiler environment
    pushd $MSVCPATH
    cmd /c "vcvarsall.bat $Architecture & set" |
        foreach {
            if ($_ -match "=") {
                $v = $_.split("="); Set-Item -Force -Path "ENV:\$($v[0])" -Value "$($v[1])"
            }
        }
    popd

    pushd $BUILDPATH
    cmd /c "$SourcePath\configure -prefix $InstallPrefix -opensource -confirm-license -nomake tests -nomake examples -nomake tools -release -force-debug-info -skip qt3d -skip qtactiveqt -skip qtcanvas3d -skip qtconnectivity -skip qtdeclarative -skip qtdoc -skip qtenginio -skip qtgraphicaleffects -skip qtlocation -skip qtmultimedia -skip qtquick1 -skip qtquickcontrols -skip qtscript -skip qtsensors -skip qtserialport -skip qtsvg -skip qtwebchannel -skip qtwebengine -skip qtwebkit -skip qtwebkit-examples -skip qtwebsockets -skip qtxmlpatterns -no-opengl"
    if ($LastExitCode -ne 0) {
        Throw "Qt Configure failed"
    }
    & $JOMPATH "/C"
    if ($LastExitCode -ne 0) {
        Throw "Qt building failed"
    }
    & $JOMPATH "install" "/C"
    if ($LastExitCode -ne 0) {
        Throw "Qt install failed"
    }
    popd

    Remove-Item $BUILDPATH -Recurse -ErrorAction SilentlyContinue
    Restore-Environment -oldEnv $oldEnv
}

# Initial cleanup
Remove-Item $OUTARCHIVEPATH -ErrorAction SilentlyContinue
Remove-Item $PACKAGEBUILDPATH -ErrorAction SilentlyContinue
Remove-Item $QTROOTPATH -Recurse -ErrorAction SilentlyContinue

# Download sources
Write-Host "Downloading '$QTARCHIVEURL'..."
$QtArchivePath = DownloadToTemp($QTARCHIVEURL)

# Extract sources
Write-Host "Extracting '$QtArchivePath'..."
& $7ZIPPATH "x" $QtArchivePath "-o$env:TEMP\archive-contents" "-y" "-bd" 1>$null
Write-Host "Moving sources to '$QTSOURCEPATH'..."
New-Item -ItemType Directory -Path $QTSOURCEPATH -Force | Out-Null
Move-Item -Path "$env:TEMP\archive-contents\*\*" -Destination $QTSOURCEPATH
Remove-Item "$env:TEMP\archive-contents" -Recurse

# Compile sources
Write-Host "Compiling 32 bit Qt libraries..."
BuildQt -SourcePath $QTSOURCEPATH -Architecture "x86" -InstallPrefix $QT32PATH
Write-Host "Compiling 64 bit Qt libraries..."
BuildQt -SourcePath $QTSOURCEPATH -Architecture "x86_amd64" -InstallPrefix $QT64PATH

# Archive $QTROOTPATH
Write-Host "Archiving files to '$OUTARCHIVEPATH'..."
& $7ZIPPATH "a" $OUTARCHIVEPATH "$QTROOTPATH\*" "-y" 1>$null

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
Remove-Item $QtArchivePath
Remove-Item $OUTARCHIVEPATH
Remove-Item $QTROOTPATH -Recurse
