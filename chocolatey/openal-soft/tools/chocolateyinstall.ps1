$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

$packageArgs = @{
  FileFullPath = $ARCHIVEFILEPATH
  Destination = $INSTALLPATH
}

Get-ChocolateyUnzip @packageArgs
Install-ChocolateyEnvironmentVariable "OAL32PATH" $BUILDPATH32
Install-ChocolateyEnvironmentVariable "OAL64PATH" $BUILDPATH64
