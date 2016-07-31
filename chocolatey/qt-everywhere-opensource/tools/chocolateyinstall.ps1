$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

$packageArgs = @{
  FileFullPath = $OUTARCHIVEPATH
  Destination = $QTROOTPATH
}

Get-ChocolateyUnzip @packageArgs
Install-ChocolateyEnvironmentVariable "QT32PATH" $QT32PATH
Install-ChocolateyEnvironmentVariable "QT64PATH" $QT64PATH
