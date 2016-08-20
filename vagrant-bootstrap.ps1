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

Param([switch]$FromVagrant=$False)

$REPOPATH               = "C:\vagrant"
$WOTPATH                = "C:\world_of_tanks"
$LOCALCHOCOREPOPATH     = "$REPOPATH\chocolatey-repo"
$PYTHONSCRIPTSPATH      = "C:\tools\python2\Scripts"
$MSVCPATH               = "C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC"
$TSCLIENTPATH           = "C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe"
$TSCLIENTDBPATH         = "$env:appdata\TS3Client\settings.db"
$IDENTITYPATH           = "$env:appdata\TS3Client\ts3clientui_qt.secrets.conf"

$CHOCOLATEYURL          = "https://chocolatey.org/install.ps1"

function Add-EnvPath([string]$path) {
    $paths = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine) -split ";"
    if ($paths -notcontains $path) {
        $paths = $paths + $path | where { $_ }
        [Environment]::SetEnvironmentVariable("Path", $paths -join ";", [EnvironmentVariableTarget]::Machine)
    }
}

function Set-PathExists([string]$path) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}

# From http://stackoverflow.com/questions/3919798/how-to-check-if-a-cmdlet-exists-in-powershell-at-runtime-via-script#3919904
function Test-Command([string]$name) {
    [bool](Get-Command -Name $name -ErrorAction SilentlyContinue)
}

function Test-ChocoLocalPackageExists([string]$name) {
    [bool](choco list $name -r -e --pre -s local)
}

function Test-ChocoIsPackageInstalled([string]$name) {
    [bool](choco list $name -r -e --pre -l)
}

function Run-SqliteQuery([string]$TSCLIENTDBPATH, [string]$Query) {
	& "sqlite3.exe" $TSCLIENTDBPATH $Query
}

# A check to make sure we don't accitentally run this script against our host machine
if (-Not $FromVagrant) {
    Write-Host "This script is meant to be executed only on Vagrant provisioning phase, exiting..."
    Exit
}

$stopWatch = [Diagnostics.Stopwatch]::StartNew()

# Allow execution without any security prompts
Set-ExecutionPolicy -ExecutionPolicy Bypass -Force

# Since we are doing heavy activity in the file system, disabling Windows Defender's realtime
# monitoring speeds up whole bootstrapping
Set-MpPreference -DisableRealtimeMonitoring $true

# Disable automatic Windows updates, since Vagrant will not wait for update to gracefully finish
# if it takes too long to shutdown
Stop-Service wuauserv
Set-Service wuauserv -StartupType disabled

# Enable auto logon
# Required for opening GUI applications from remote powershell session
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name AutoAdminLogon -Value 1
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name DefaultUserName -Value "vagrant"
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name DefaultPassword -Value "vagrant"

# Install Chocolatey package manager
if (-Not (Test-Command "choco")) {
    Write-Host "Installing Chocolatey package manager"
    $env:chocolateyVersion = "0.10.0"
    iex ((new-object net.webclient).DownloadString($CHOCOLATEYURL))
}

# Load functions required for Update-SessionEnvironment.
. C:\ProgramData\chocolatey\helpers\functions\Get-EnvironmentVariable.ps1
. C:\ProgramData\chocolatey\helpers\functions\Get-EnvironmentVariableNames.ps1
. C:\ProgramData\chocolatey\helpers\functions\Update-SessionEnvironment.ps1

# Enable installing locally packaged Chocolatey packages
Set-PathExists $LOCALCHOCOREPOPATH
choco source add --name=local --source=$LOCALCHOCOREPOPATH

Write-Host "Installing packages with Chocolatey..."
# See https://chocolatey.org/packages
choco install visualstudioexpress2013windowsdesktop --version 12.0.21005.1 -y --allow-empty-checksums
choco install jom --version 1.1.1 -y
choco install 7zip --version 16.02 -y --allow-empty-checksums
choco install python2 --version 2.7.11 -y
choco install git --version 2.9.2 -y
choco install cmake --version 3.6.0 -y
choco install teamspeak --version 3.0.19 -y --allow-empty-checksums
choco install vlc --version 2.2.4 -y
choco install sqlite.shell --version 3.10.1 -y

# Add programs to PATH
Add-EnvPath -path $PYTHONSCRIPTSPATH
Add-EnvPath "C:\Program Files\CMake\bin"
Update-SessionEnvironment

# Create Chocolatey package for Qt libraries
if (-Not (Test-ChocoLocalPackageExists qt-everywhere-opensource)) {
    powershell -NoProfile -Command "& $REPOPATH\chocolatey\qt-everywhere-opensource\tools\pack.ps1"
    if (Test-ChocoIsPackageInstalled qt-everywhere-opensource) {
        choco uninstall qt-everywhere-opensource
    }
}

# Install Qt libraries
choco install qt-everywhere-opensource --version 5.5.1 -y

# Create Chocolatey package for OpenAL Soft
if (-Not (Test-ChocoLocalPackageExists openal-soft)) {
    powershell -NoProfile -Command "& $REPOPATH\chocolatey\openal-soft\tools\pack.ps1"
    if (Test-ChocoIsPackageInstalled openal-soft) {
        choco uninstall openal-soft
    }
}

# Install OpenAL Soft
choco install openal-soft --version 1.16.0-fixes1 -y

# Create Chocolatey package for TeamSpeak Server
if (-Not (Test-ChocoLocalPackageExists teamspeak-server)) {
	powershell -NoProfile -Command "& $REPOPATH\chocolatey\teamspeak-server\tools\pack.ps1"
	if (Test-ChocoIsPackageInstalled teamspeak-server) {
		choco uninstall teamspeak-server
	}
}

# Install TeamSpeak Server
choco install teamspeak-server --version 3.0.13 -y

# Create Chocolatey package for Virtual Audio Cable
if (-Not (Test-ChocoLocalPackageExists virtual-audio-cable)) {
	powershell -NoProfile -Command "& $REPOPATH\chocolatey\virtual-audio-cable\tools\pack.ps1"
	if (Test-ChocoIsPackageInstalled virtual-audio-cable) {
		choco uninstall virtual-audio-cable
	}
}

# Install Virtual Audio Cable
choco install virtual-audio-cable --version 4.15 -y

Update-SessionEnvironment

cd $REPOPATH

Write-Host "Installing python dependencies..."
pip install -r requirements.txt

Write-Host "Configuring TessuMod development environment..."
python make.py configure --qmake-x86="$env:QT32PATH\bin\qmake.exe"
python make.py configure --qmake-x64="$env:QT64PATH\bin\qmake.exe"
python make.py configure --openal-x86=$env:OAL32PATH
python make.py configure --openal-x64=$env:OAL64PATH
python make.py configure --msvc-vars="$MSVCPATH\vcvarsall.bat"
python make.py configure --wot-install=$WOTPATH

Write-Host "Add firewall rules for TeamSpeak server"
netsh advfirewall firewall delete rule name=all program="$env:TSSERVERPATH\ts3server.exe" | Out-Null
netsh advfirewall firewall add rule name="TeamSpeak Server (TCP-in)" program="$env:TSSERVERPATH\ts3server.exe" dir=in action=allow protocol=TCP
netsh advfirewall firewall add rule name="TeamSpeak Server (UDP-in)" program="$env:TSSERVERPATH\ts3server.exe" dir=in action=allow protocol=UDP

if (-not ((Test-Path env:\TS_SERVERQUERY_LOGINNAME) `
	-and (Test-Path env:\TS_SERVERQUERY_PASSWORD) `
	-and (Test-Path env:\TS_SERVER_ADMINTOKEN)))
{
	Write-Host "ServerQuery and admin credentials not known"

	Write-Host "Stoping TeamSpeak server and clearing configuration"
	Stop-Process -Name "ts3server" -ErrorAction SilentlyContinue
	Remove-Item -Path "$env:TSSERVERPATH\ts3server.sqlitedb*"

	Write-Host "Starting TeamSpeak server"
	$ServerProcess = Start-Process `
		-FilePath "$env:TSSERVERPATH\ts3server.exe" `
		-WorkingDirectory "$env:TSSERVERPATH" `
		-PassThru `
		-RedirectStandardError "$env:TEMP\tsserver_stderr.log"

	Write-Host "Extracting ServerQuery and admin credentials from server output"
	do {
		$OUTPUT     = Get-Content "$env:TEMP\tsserver_stderr.log"
		$LOGINNAME  = $OUTPUT | Select-String -Pattern 'loginname= "([^"]+)"'
		$PASSWORD   = $OUTPUT | Select-String -Pattern 'password= "([^"]+)"'
		$ADMINTOKEN = $OUTPUT | Select-String -Pattern 'token=(.+)'
	} while (-not ($LOGINNAME -and $PASSWORD -and $ADMINTOKEN))

	[Environment]::SetEnvironmentVariable("TS_SERVERQUERY_LOGINNAME", `
		$LOGINNAME.matches.Groups[1].Value, [EnvironmentVariableTarget]::User)
	[Environment]::SetEnvironmentVariable("TS_SERVERQUERY_PASSWORD", `
		$PASSWORD.matches.Groups[1].Value, [EnvironmentVariableTarget]::User)
	[Environment]::SetEnvironmentVariable("TS_SERVER_ADMINTOKEN", `
		$ADMINTOKEN.matches.Groups[1].Value, [EnvironmentVariableTarget]::User)

	Update-SessionEnvironment

	Write-Host "Stopping TeamSpeak server"
	Stop-Process -InputObject $ServerProcess

	$TIMESTAMP = [int][double]::Parse((Get-Date -UFormat %s))
	$TSSERVERDBPATH = "$env:TSSERVERPATH\ts3server.sqlitedb"
	# Add vagrant user as admin to server
	Run-SqliteQuery $TSSERVERDBPATH "INSERT INTO 'clients' VALUES(2,1,'WD72qAMbBqxmnfhJ18/6+eAjaC4=','vagrant',NULL,NULL,$TIMESTAMP,1,0,0,0,0,'127.0.0.1',NULL);"
	Run-SqliteQuery $TSSERVERDBPATH "INSERT INTO 'group_server_to_client' VALUES(6,1,2,0);"
	# Remove privilege key prompt
	Run-SqliteQuery $TSSERVERDBPATH "UPDATE 'server_properties' SET value='' WHERE ident='virtualserver_autogenerated_privilegekey';"
	Run-SqliteQuery $TSSERVERDBPATH "DELETE FROM 'tokens' WHERE token_description='default serveradmin privilege key';"
}

Write-Host "Add TeamSpeak server to startup"
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:appdata\Microsoft\Windows\Start Menu\Programs\Startup\TeamSpeak Server.lnk")
$Shortcut.TargetPath = "$env:TSSERVERPATH\ts3server.exe"
$Shortcut.WorkingDirectory = "$env:TSSERVERPATH"
$Shortcut.Save()

if (-Not (Test-Path $TSCLIENTDBPATH)) {
	Write-Host "Configuring TeamSpeak client"
	$Process = Start-Process $TSCLIENTPATH -PassThru
	while (-Not (Test-Path $TSCLIENTDBPATH)) {}
	while (((Get-Date) - (Get-Item $TSCLIENTDBPATH).LastWriteTime).TotalSeconds -lt 5) {}
	$Process.Kill()
	$Process.WaitForExit()
	$TIMESTAMP = [int][double]::Parse((Get-Date -UFormat %s))
	# Hide EULA prompt
	Run-SqliteQuery $TSCLIENTDBPATH "INSERT INTO 'General' VALUES($TIMESTAMP, 'LastShownLicense', '1');"
	# Add bookmark for localhost server
	Run-SqliteQuery $TSCLIENTDBPATH "INSERT INTO 'TS3Tables' VALUES('Bookmarks', $TIMESTAMP);"
	Run-SqliteQuery $TSCLIENTDBPATH "CREATE TABLE Bookmarks (timestamp integer unsigned NOT NULL, key varchar NOT NULL UNIQUE, value varchar);"
	Run-SqliteQuery $TSCLIENTDBPATH "CREATE INDEX index_Bookmarks_key ON Bookmarks (key);"
	Run-SqliteQuery $TSCLIENTDBPATH @"
INSERT INTO 'Bookmarks' VALUES($TIMESTAMP,'{b6728837-2014-4802-8b21-382ed9393f0d}','Name=localhost
Address=localhost
Port=9987
CaptureProfile=Default
PlaybackProfile=Default
Identity=Default
Nick=vagrant
PhoneticsNickname=
DefaultChannel=
Autoconnect=false
ShowServerQueryClients=false
Uuid={b6728837-2014-4802-8b21-382ed9393f0d}
ServerUID=
HotkeyProfile=Default
Count=0
Last=
Total=0
Clients=0
Type=0
LastIP=
SoundPack=
ChannelID=
Order=001');
"@.Replace("`r", "")

	# Add identity for vagrant user
	@"
;WARNING!!
;THIS FILE CONTAINS ALL SAVED PASSWORDS AND IDENTITIES FOR TEAMSPEAK 3
;DO NOT SHARE THIS FILE WITH ANYONE, NOT EVEN YOUR HOSTER OR TEAMSPEAK-SYSTEMS.
;DOING SO, CAN RESULT IN UNAUTHORIZED PERSONS GAINING ACCESS TO YOUR SERVERS,
;AND EVEN WORSE, THEY CAN IMPERSONATE YOU AND THE SERVERS WILL NOT BE ABLE
;TO TELL THE DIFFERENCE BETWEEN THEM AND YOU!! YOU HAVE BEEN WARNED!!

[General]

[Identities]
1/id=Default
1/identity=122V/9iKLSlPHwJ+deqs+sGBwtbaidVWAXBlVnZRaRF3Y3wqRF94AGt+OjdcVQseT1FSElZaC3ZcZz9ObG0ie2l0Q3V/ZHZHClhIDFFSMCAWCBJyWlh9DhpaAG83fQ9iAAdEL35QB3dCTWhVQUloQU9aZHdoMDRISFV6N0NZZlpOWVpBL0ZyVTJFcTNqdzJUQ05FdlhURjVKazc=
1/nickname=vagrant
SelectedIdentity=Default
size=1
"@ | Out-File -FilePath "$env:appdata\TS3Client\ts3clientui_qt.secrets.conf"
}

$stopWatch.Stop()
Write-Host ("Bootstrapping took {0:N0} minutes" -f $stopWatch.Elapsed.TotalMinutes)
