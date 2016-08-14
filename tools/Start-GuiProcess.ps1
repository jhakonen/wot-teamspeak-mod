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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# =============================================================================
# This script starts any GUI applications by running them through Task Scheduler
# as a single fire task.
# By launching GUI application this way it is possible to start the application
# so that its window will appear to logged in user's desktop and not to current
# remote session's invisible desktop.
# =============================================================================

Param(
    [string]$Executable,
    [string]$Argument
)

$TaskName = "_StartProcessActiveTask"

# Remove any previously created scheduled task (shouldn't happen normally)
try {
    Unregister-ScheduledTask -InputObject (Get-ScheduledTask $TaskName -ErrorAction SilentlyContinue) -Confirm:$False
} catch {}

# Create, start and remove a scheduled task
$Action = New-ScheduledTaskAction -Execute $Executable -Argument $Argument
$Principal = New-ScheduledTaskPrincipal -userid $env:USERNAME
$Task = New-ScheduledTask -Action $Action -Principal $Principal
$RegisteredTask = Register-ScheduledTask $TaskName -InputObject $Task
Start-ScheduledTask -InputObject $RegisteredTask
Unregister-ScheduledTask -InputObject $RegisteredTask -Confirm:$False
