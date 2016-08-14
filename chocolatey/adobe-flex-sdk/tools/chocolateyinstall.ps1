$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

$packageArgs = @{
  FileFullPath = $ARCHIVEPATH
  Destination = $INSTALLPATH
}

Get-ChocolateyUnzip @packageArgs
Install-ChocolateyEnvironmentVariable "FLEXSDKPATH" $INSTALLPATH
