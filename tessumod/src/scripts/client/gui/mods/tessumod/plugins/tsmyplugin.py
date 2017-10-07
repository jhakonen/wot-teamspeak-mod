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

from gui.mods.tessumod import database
from gui.mods.tessumod.lib import logutils, sharedmemory, timer, gameapi
from gui.mods.tessumod.lib import pydash as _
from gui.mods.tessumod.lib.timer import TimerMixin
from gui.mods.tessumod.messages import UserMessage, PairingMessage, VehicleMessage
from gui.mods.tessumod.plugintypes import Plugin, VoiceClientListener, SettingsProvider, SettingsUIProvider

import functools
import os
import sys
import struct
import subprocess
import threading
import time

logger = logutils.logger.getChild("tsmyplugin")

def build_plugin():
	"""
	Called by plugin manager to build the plugin's object.
	"""
	return TSMyPluginPlugin()

class TSMyPluginPlugin(Plugin, VoiceClientListener, SettingsProvider, SettingsUIProvider, TimerMixin):
	"""
	This plugin ...
	"""

	SUPPORTED_PLUGIN_VERSIONS = [1]

	def __init__(self):
		super(TSMyPluginPlugin, self).__init__()
		self.__advertisement_ignored = False
		self.__positional_data_api = PositionalDataAPI()
		self.__clid_vehicle_ids = {}

	@logutils.trace_call(logger)
	def initialize(self):
		gameapi.events.on("battle_started", self.__on_battle_started)
		gameapi.events.on("battle_finished", self.__on_battle_finished)
		self.messages.subscribe(UserMessage, self.__on_user_event)
		self.messages.subscribe(PairingMessage, self.__on_pairing_event)
		self.messages.subscribe(VehicleMessage, self.__on_vehicle_event)

	@logutils.trace_call(logger)
	def deinitialize(self):
		gameapi.events.off("battle_started", self.__on_battle_started)
		gameapi.events.off("battle_finished", self.__on_battle_finished)
		self.messages.unsubscribe(UserMessage, self.__on_user_event)
		self.messages.unsubscribe(PairingMessage, self.__on_pairing_event)
		self.messages.unsubscribe(VehicleMessage, self.__on_vehicle_event)

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "General":
			if name == "tsplugin_opt_out":
				self.__advertisement_ignored = value

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"General": {
				"help": "",
				"variables": [
					{
						"name": "tsplugin_opt_out",
						"default": False,
						"help": "Do not show TessuMod TeamSpeak plugin install advertisement"
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def get_settingsui_content(self):
		"""
		Implemented from SettingsUIProvider.
		"""
		return {
			"Ignored Notifications": [
				{
					"label": "Ignore plugin advertisement",
					"help": "Do not show TessuMod TeamSpeak plugin install advertisement",
					"type": "checkbox",
					"variable": ("General", "tsplugin_opt_out")
				}
			]
		}

	@logutils.trace_call(logger)
	def on_voice_client_connected(self):
		"""
		Implemented from VoiceClientListener.
		"""
		# Check is plugin file included with mod, and offer to install it
		mods_dirpath = gameapi.find_res_mods_version_path()
		self.__installer_path = os.path.normpath(os.path.join(mods_dirpath, "tessumod.ts3_plugin"))
		# plugin doesn't work in WinXP so check that we are running on
		# sufficiently recent Windows OS
		if not self.__is_vista_or_newer():
			return
		if not os.path.isfile(self.__installer_path):
			return
		if self.__get_plugin_version() in self.SUPPORTED_PLUGIN_VERSIONS:
			return
		if self.__advertisement_ignored:
			return
		gameapi.show_notification({
			"icon": "scripts/client/gui/mods/tessumod/assets/ts_notification_icon.png",
			"message": [
				"Would you like to install TessuMod plugin for TeamSpeak?",
				"With the plugin TessuMod supports 3D audio, positioning users voice in " +
				"TeamSpeak so that their voices appear to come from their vehicle's " +
				"direction on battlefield. <a href=\"event:moreinfo\">More info</a>"
			],
			"ignorable": "tsplugin_api_version_1",
			"ignore_action": self.__on_notification_ignored,
			"buttons": [
				{
					"label": "Install",
					"action": "install"
				}
			],
			"actions": {
				"moreinfo": self.__on_notification_moreinfo_clicked,
				"install": self.__on_notification_install_clicked
			}
		})

	def __is_vista_or_newer(self):
		'''
		Returns True if the game is running on Windows Vista or newer OS.
		'''
		try:
			return sys.getwindowsversion()[0] >= 6
		except:
			logger.warning("Failed to get current Windows OS version")
			return True

	def __get_plugin_version(self):
		"""
		Returns plugin's API version from shared memory. Returns zero if plugin is not present.
		"""
		with InfoAPI() as api:
			return api.get_api_version()

	def __on_notification_moreinfo_clicked(self):
		url = "https://github.com/jhakonen/wot-teamspeak-mod/wiki/TeamSpeak-Plugins#tessumod-plugin"
		subprocess.call(["start", url], shell=True)

	def __on_notification_install_clicked(self):
		self.__installer_path
		threading.Thread(
			target = functools.partial(
				subprocess.call,
				args  = [self.__installer_path],
				shell = True
			)
		).start()

	def __on_notification_ignored(self, ignored):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("Settings"):
			plugin_info.plugin_object.set_settings_value("General", "tsplugin_opt_out", ignored)

	@logutils.trace_call(logger)
	def on_current_voice_server_changed(self, server_id):
		"""
		Implemented from VoiceClientListener.
		"""
		self.__update_client_lookup()

	@logutils.trace_call(logger)
	def __on_battle_started(self):
		self.__positional_data_api.open()
		self.on_timeout(0.1, self.__write_positional_data, repeat=True)

	@logutils.trace_call(logger)
	def __on_battle_finished(self):
		self.__positional_data_api.close()
		self.off_timeout(self.__write_positional_data)

	@logutils.trace_call(logger)
	def __on_user_event(self, action, data):
		self.__update_client_lookup()

	@logutils.trace_call(logger)
	def __on_pairing_event(self, action, data):
		self.__update_client_lookup()

	@logutils.trace_call(logger)
	def __on_vehicle_event(self, action, data):
		self.__update_client_lookup()

	def __update_client_lookup(self):
		self.__clid_vehicle_ids.clear()
		connection_id = (self.plugin_manager.getPluginsOfCategory("VoiceClientProvider")[0]
			.plugin_object.get_my_connection_id())
		for user_id, vehicle_id in database.get_user_id_vehicle_id_pairs():
			if user_id[0] != connection_id:
				continue
			self.__clid_vehicle_ids[user_id[1]] = vehicle_id

	def __write_positional_data(self):
		if not self.__positional_data_api.is_open():
			logger.debug("__write_positional_data: data api is not open")
			return

		client_positions = {}
		for clid, vehicle_id in self.__clid_vehicle_ids.iteritems():
			pos = gameapi.get_vehicle_position(vehicle_id)
			if not pos:
				continue
			client_positions[clid] = pos
		if not client_positions:
			logger.debug("__write_positional_data: no client positions")
			return
		self.__positional_data_api.set_data(
			camera_position = gameapi.get_camera_position(),
			camera_direction = gameapi.get_camera_direction(),
			positions = client_positions
		)


class InfoAPI(sharedmemory.SharedMemory):

	NAME = "TessuModTSPluginInfo"
	SIZE = 1
	ACCESS_TYPE = sharedmemory.ACCESS_READ

	def get_api_version(self):
		self.seek(0)
		return struct.unpack("=B", self.read(1))[0]


class PositionalDataAPI(sharedmemory.SharedMemory):

	NAME = "TessuModTSPlugin3dAudio"
	SIZE = 1024
	ACCESS_TYPE = sharedmemory.ACCESS_WRITE

	def __init__(self):
		super(PositionalDataAPI, self).__init__()
		self.__previous_camera_position = None
		self.__previous_camera_direction = None
		self.__previous_positions = None
		self.__previous_timestamp = None

	def close(self):
		# reset timestamp to notify teamspeak to stop positioning right away
		if self.is_open():
			self.seek(0)
			self.write(struct.pack("I", 0))
		super(PositionalDataAPI, self).close()

	def set_data(self, camera_position, camera_direction, positions):
		timestamp = int(time.time())
		if self.__has_data_updated(timestamp, camera_position, camera_direction, positions):
			self.seek(0)
			self.write(struct.pack("I", timestamp))
			self.write(self.__pack_float_vector(camera_position))
			self.write(self.__pack_float_vector(camera_direction))
			self.write(struct.pack("B", len(positions)))
			for clid, position in positions.iteritems():
				self.write(struct.pack("h", clid))
				self.write(self.__pack_float_vector(position))
			self.__previous_timestamp = timestamp
			self.__previous_camera_position = camera_position
			self.__previous_camera_direction = camera_direction
			self.__previous_positions = positions

	def __has_data_updated(self, timestamp, camera_position, camera_direction, positions):
		return (
			self.__previous_timestamp != timestamp
			or self.__previous_camera_position != camera_position
			or self.__previous_camera_direction != camera_direction
			or self.__previous_positions != positions
		)

	def __pack_float_vector(self, vector):
		return struct.pack("3f", vector[0], vector[1], vector[2])
