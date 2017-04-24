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
from .eventloop import EventLoop
from .. import logutils

from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

logger = logutils.logger.getChild("gameapi")
g_sessionProvider = dependency.instance(IBattleSessionProvider)

class MinimapMarkerAnimation(object):

	def __init__(self, vehicle_id, interval, action, on_done):
		self.__interval   = interval
		self.__action     = action
		self.__vehicle_id = vehicle_id
		self.__on_done    = on_done
		self.__timer      = EventLoop.create_callback_repeater(self.__updateMinimap)

	def start(self):
		if not self.__timer.is_active():
			self.__timer.start(self.__interval)
			self.__updateMinimap()

	def stop(self):
		self.__timer.stop()

	def __updateMinimap(self):
		if self.__timer.is_active():
			try:
				if g_sessionProvider.shared.feedback:
					g_sessionProvider.shared.feedback.onMinimapFeedbackReceived(
						FEEDBACK_EVENT_ID.MINIMAP_SHOW_MARKER, self.__vehicle_id, self.__action)
			except AttributeError:
				logger.exception("Updating minimap failed")
		else:
			self.__on_done(self.__vehicle_id)
