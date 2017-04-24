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

from gui.mods.tessumod.lib import logutils, gameapi
from gui.mods.tessumod.lib.pluginmanager import Plugin
from gui.mods.tessumod.models import g_player_model, PlayerItem

logger = logutils.logger.getChild("meplayer")

class MePlayerPlugin(Plugin):
	"""
	This plugin ...
	"""

	NS = "me"

	def __init__(self):
		super(MePlayerPlugin, self).__init__()
		g_player_model.add_namespace(self.NS)

	@logutils.trace_call(logger)
	def initialize(self):
		gameapi.events.on("my_player_id_received", self.__on_my_player_id_received)

	@logutils.trace_call(logger)
	def deinitialize(self):
		gameapi.events.off("my_player_id_received", self.__on_my_player_id_received)

	@logutils.trace_call(logger)
	def __on_my_player_id_received(self, player_id):
		g_player_model.set(self.NS, PlayerItem(id=player_id, is_me=True))
