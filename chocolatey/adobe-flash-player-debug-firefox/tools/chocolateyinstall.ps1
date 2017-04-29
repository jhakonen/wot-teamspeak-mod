$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

Install-ChocolateyInstallPackage `
	-PackageName "adobe-flash-player-debug-firefox" `
	-FileType "exe" `
	-File $INSTALLERPATH `
	-ValidExitCodes @(0) `
	-SilentArgs "-install" `
	-UseOnlyPackageSilentArguments
