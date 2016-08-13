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

# Constants
$Username = "vagrant"
$Password = "vagrant"
$ComputerName = "localhost"
$Port = 55985

# Construct credentials
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$Credential = new-object System.Management.Automation.PSCredential("$ComputerName\$Username", $SecurePassword)

# Connect to remote Powershell session within the VM
$Session = New-PSSession -ComputerName $ComputerName -Credential $Credential -Port $Port

# Change remote session working directory to repo's root
Invoke-Command -Session $Session -ScriptBlock { Set-Location C:\Vagrant }

# Start interactive session
Enter-PSSession -Session $Session
