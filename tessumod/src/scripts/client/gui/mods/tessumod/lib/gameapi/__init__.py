# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

from __future__ import absolute_import

from .. import eventemitter as _eventemitter
from . import hookutils as _hookutils
from . import voip as _voip
from . import battle as _battle
from . import notificationscenter as _notificationscenter
from . import myplayerid as _myplayerid
from . import playersinbattle as _playersinbattle
from . import playersinprebattle as _playersinprebattle
from . import eventloop as _eventloop
from . import minimap as _minimap
from . import log as _log
from . import paths as _paths
from . import settingsuiwindow
from . import resources as _resources

events = _eventemitter.EventEmitterMixin()

def init():
	_hookutils.install_hooks()
	_battle.init(events)
	_myplayerid.init(events)
	_playersinbattle.init(events)
	_playersinprebattle.init(events)

def deinit():
	_battle.deinit()
	_myplayerid.deinit()
	_playersinbattle.deinit()
	_playersinprebattle.deinit()
	_hookutils.uninstall_hooks()

def get_camera_position():
	return _battle.get_camera_position()

def get_camera_direction():
	return _battle.get_camera_direction()

def get_vehicle_position(vehicle_id):
	return _battle.get_vehicle_position(vehicle_id)

def create_event_loop():
	return _eventloop.EventLoop()

def create_log_redirection_handler():
	return _log.LogRedirectionHandler()

def create_minimap_animation(vehicle_id, interval, action, on_done):
	return _minimap.MinimapMarkerAnimation(vehicle_id, interval, action, on_done)

def show_notification(data):
	_notificationscenter.show_notification(data)

def find_mods_version_path():
	return _paths.find_mods_version_path()

def set_player_speaking(player_id, speaking):
	_voip.set_player_speaking(player_id, speaking)

def resources_read_file(vfs_path, read_as_binary=True):
	return _resources.read_file(vfs_path, read_as_binary)

def resources_list_directory(vfs_directory):
	return _resources.list_directory(vfs_directory)

def resources_file_copy(vfs_from, realfs_to):
	return _resources.file_copy(vfs_from, realfs_to)
