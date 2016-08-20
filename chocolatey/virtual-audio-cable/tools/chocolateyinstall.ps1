$ErrorActionPreference = 'Stop'; # stop on all errors

Import-module $PSScriptRoot\constants -Force

Get-ChocolateyUnzip `
    -FileFullPath $ARCHIVEPATH `
    -Destination $TEMPINSTALLPATH

New-Item -ItemType Directory -Path $INSTALLPATH -Force

Copy-Item "$TEMPINSTALLPATH\vac.chm" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\readme.txt" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\homepage.url" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\license.txt" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\x64\vcctlpan.exe" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\x64\audiorepeater.exe" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\x64\audiorepeater_ks.exe" $INSTALLPATH -Force
Copy-Item "$TEMPINSTALLPATH\x64\vrtaucbl.sys" $DRIVERSPATH -Force

Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\Readme.lnk" -TargetPath "$INSTALLPATH\readme.txt"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\Control panel.lnk" -TargetPath "$INSTALLPATH\vcctlpan.exe"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\Audio Repeater (MME).lnk" -TargetPath "$INSTALLPATH\audiorepeater.exe"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\Audio Repeater (KS).lnk" -TargetPath "$INSTALLPATH\audiorepeater_ks.exe"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\User manual.lnk" -TargetPath "$INSTALLPATH\vac.chm"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\Homepage.lnk" -TargetPath "$INSTALLPATH\homepage.url"
Install-ChocolateyShortcut -ShortcutFilePath "$STARTMENUPATH\License Agreement.lnk" -TargetPath "$INSTALLPATH\license.txt"

# Trust to be installed device drivers (needed for silent installation)
# publisher.cer has been exported from vrtaucbl.cat
certutil.exe -f -addstore "TrustedPublisher" "$ROOTPATH\publisher.cer"

# Install device driver
& "$ROOTPATH\devcon.exe" install "$TEMPINSTALLPATH\vrtaucbl.inf" EuMusDesign_VAC_WDM

# Cleanup
certutil.exe -delstore "TrustedPublisher" "Muzychenko Evgenii Viktorovich"
Remove-Item $TEMPINSTALLPATH -Recurse
