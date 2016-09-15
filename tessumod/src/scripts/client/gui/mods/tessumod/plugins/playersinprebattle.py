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

from gui.mods.tessumod import plugintypes, logutils, models, gameutils
from gui.mods.tessumod.infrastructure import gameapi

import BigWorld
from gui.prb_control.dispatcher import _PrbControlLoader
from gui.prb_control.prb_helpers import GlobalListener
from PlayerEvents import g_playerEvents

logger = logutils.logger.getChild("playersinprebattle")

class PlayersInPrebattlePlugin(plugintypes.ModPlugin, plugintypes.PlayerModelProvider):
	"""
	This plugin provides a model for other plugins which contains players in prebattle.
	"""

	singleton = None

	def __init__(self):
		super(PlayersInPrebattlePlugin, self).__init__()
		PlayersInPrebattlePlugin.singleton = self
		self.__model = models.Model()
		self.__model_proxy = models.ImmutableModelProxy(self.__model)
		self.__listener = PrebattleListener(self.__model)

	@property
	def listener(self):
		return self.__listener

	@logutils.trace_call(logger)
	def initialize(self):
		pass

	@logutils.trace_call(logger)
	def deinitialize(self):
		pass

	@logutils.trace_call(logger)
	def has_player_model(self, name):
		"""
		Implemented from PlayerModelProvider.
		"""
		return name == "prebattle"

	@logutils.trace_call(logger)
	def get_player_model(self, name):
		"""
		Implemented from PlayerModelProvider.
		"""
		if self.has_player_model(name):
			return self.__model_proxy


class PrebattleListener(GlobalListener):

	def __init__(self, model):
		self.__model = model

	def onPrbFunctionalFinished(self):
		self.__model.clear()

	def onUnitFunctionalFinished(self):
		self.__model.clear()

	def onPlayerAdded(self, functional, info):
		self.__model.set({
			"id": int(info.dbID),
			"name": info.name
		})

	def onUnitPlayerAdded(self, info):
		self.__model.set({
			"id": int(info.dbID),
			"name": info.name
		})

	def onUnitPlayerInfoChanged(self, info):
		self.__model.set({
			"id": int(info.dbID),
			"name": info.name
		})

def PrbControlLoader_onAccountShowGUI(orig_method):
	def decorator(self, ctx):
		orig_method(self, ctx)
		PlayersInPrebattlePlugin.singleton.listener.startGlobalListening()
	return decorator
_PrbControlLoader.onAccountShowGUI = PrbControlLoader_onAccountShowGUI(_PrbControlLoader.onAccountShowGUI)
