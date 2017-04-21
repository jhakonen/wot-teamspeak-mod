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

from gui.mods.tessumod import plugintypes
from gui.mods.tessumod.lib import logutils
from gui.mods.tessumod.lib.pluginmanager import Plugin
from gui.mods.tessumod.models import g_player_model, PlayerItem

from gui.prb_control.dispatcher import _PrbControlLoader
from gui.prb_control.entities.listener import IGlobalListener

logger = logutils.logger.getChild("playersinprebattle")

class PlayersInPrebattlePlugin(Plugin):
	"""
	This plugin provides a model for other plugins which contains players in prebattle.
	"""

	def __init__(self):
		super(PlayersInPrebattlePlugin, self).__init__()

	@logutils.trace_call(logger)
	def initialize(self):
		pass

	@logutils.trace_call(logger)
	def deinitialize(self):
		pass

class PrebattleListener(IGlobalListener):

	NS = "prebattle"

	def __init__(self):
		g_player_model.add_namespace(self.NS)

	def onPrbFunctionalFinished(self):
		g_player_model.clear(self.NS)

	def onUnitFunctionalFinished(self):
		g_player_model.clear(self.NS)

	def onPlayerAdded(self, functional, info):
		g_player_model.set(self.NS, PlayerItem(
			id = int(info.dbID),
			name = info.name
		))

	def onUnitPlayerAdded(self, info):
		g_player_model.set(self.NS, PlayerItem(
			id = int(info.dbID),
			name = info.name
		))

	def onUnitPlayerInfoChanged(self, info):
		g_player_model.set(self.NS, PlayerItem(
			id = int(info.dbID),
			name = info.name
		))

g_prebattle_listener = PrebattleListener()

def PrbControlLoader_onAccountShowGUI(orig_method):
	def decorator(self, ctx):
		orig_method(self, ctx)
		g_prebattle_listener.startGlobalListening()
	return decorator
_PrbControlLoader.onAccountShowGUI = PrbControlLoader_onAccountShowGUI(_PrbControlLoader.onAccountShowGUI)
