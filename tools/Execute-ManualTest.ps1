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
Param([ValidateSet("Start", "Stop", "Pause")][string]$Action="Start")
$VLCPATH      = "C:\Program Files\VideoLAN\VLC\vlc.exe"
$TSCLIENTPATH = "C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe"
$OUTPUTDEVICE = "Virtual Audio Cable"
$VLCRCPORT    = 5555

if ($Action -eq "Start") {
	# Start TS client and connect local TS server
	if (-Not (Get-Process ts3client_win64 -ErrorAction SilentlyContinue)) {
		& "$PSScriptRoot\Start-GuiProcess.ps1" -Executable $TSCLIENTPATH -Argument "ts3server://localhost"
	}

	# Start VLC playing back audio to Virtual Audio Cable
	if (-Not (Get-Process vlc -ErrorAction SilentlyContinue)) {
		$GUID = & "$PSScriptRoot\GetDirectSoundDriverGUID.exe" $OUTPUTDEVICE
		& "$PSScriptRoot\Start-GuiProcess.ps1" -Executable $VLCPATH `
			-Argument "--aout=directx --directx-audio-device=$GUID $PSScriptRoot\testaudio\playlist.m3u --loop --no-qt-privacy-ask --extraintf=`"rc`" --rc-quiet --rc-host=`"localhost:$VLCRCPORT`""
	}
}
if ($Action -eq "Stop") {
	# Kill VLC and TS client if any
	$Process = Get-Process vlc -ErrorAction SilentlyContinue
	if ($Process) {
		$Process | Where-Object { $_.Kill() }
	}
	$Process = Get-Process ts3client_win64 -ErrorAction SilentlyContinue
	if ($Process) {
		$Process | Where-Object { $_.Kill() }
	}
}
if ($Action -eq "Pause") {
	# Send play/pause toggle command to VLC through its RC port
	if (Get-Process vlc -ErrorAction SilentlyContinue) {
		$Client = New-Object -TypeName "System.Net.Sockets.TcpClient" -ArgumentList "localhost", $VLCRCPORT
		$Stream = $client.GetStream()
		$Command = [System.Text.Encoding]::ASCII.GetBytes("pause");
		$Stream.Write($Command, 0, $Command.Length)
		$Stream.Close()
		$Client.Close()
	}
}
