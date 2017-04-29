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
import json

from gui import InputHandler
from gui.app_loader import g_appLoader
from gui.shared import g_eventBus, events
from gui.shared.utils.key_mapping import getBigworldNameFromKey
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings
from gui.Scaleform.framework import ViewTypes, ScopeTemplates

from .. import logutils

logger = logutils.logger.getChild("gameapi")

class SettingsUIWindow(LobbySubView, WindowViewMeta):

	NAME = "SettingsUIWindow"

	def __init__(self):
		super(SettingsUIWindow, self).__init__()

	def _populate(self):
		super(SettingsUIWindow, self)._populate()

		# insert some example data to ActionScript window
		self.as_setSettingsS(json.dumps({
			"foo": "bar",
			"baz": False
		}, sort_keys=True, indent=4, separators=(",", ": ")))

	def as_setSettingsS(self, data):
		'''Sets given settings to window at ActionScript code.
		The 'data' argument is expected to be a string.
		'''
		if self._isDAAPIInited():
			self.flashObject.as_setSettings(data)

	def onWindowClose(self):
		self.destroy()

	def onTryClosing(self):
		return True

	def onOkClicked(self):
		'''Called from ActionScript by DAAPI when user clicks ok button.'''
		logger.info("PYTHON: onOkClicked() called")

	def onCancelClicked(self):
		'''Called from ActionScript by DAAPI when user clicks cancel button.'''
		logger.info("PYTHON: onCancelClicked() called")

g_entitiesFactories.addSettings(
	ViewSettings(
		SettingsUIWindow.NAME,
		SettingsUIWindow,
		'tessu_mod/SettingsUI.swf',
		ViewTypes.WINDOW,
		None,
		ScopeTemplates.DEFAULT_SCOPE
	)
)

# HACK: get the settings ui window open somehow
def onhandleKeyEvent(event):
	key = getBigworldNameFromKey(event.key)
	if key == "KEY_F10":
		g_appLoader.getApp().loadView(SettingsUIWindow.NAME, SettingsUIWindow.NAME)
	return None
InputHandler.g_instance.onKeyDown += onhandleKeyEvent

# HACK: get GUI debug messages to appear to python.log
log_handlers = {
	"WARNING": logger.warning
}

def onAppInitialized(event):
	from gui.app_loader import g_appLoader
	app = g_appLoader.getDefLobbyApp()
	app.addExternalCallback('debug.LOG_GUI', on_log_gui)
	app.addExternalCallback('debug.LOG_GUI_FORMAT', on_log_gui_format)

def on_log_gui(type, msg, *args):
	if "tessumod" in msg.lower():
		log_handlers[type](msg, *args)

def on_log_gui_format(type, msg, *args):
	if "tessumod" in msg.lower():
		log_handlers[type](msg % args)

g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZED, onAppInitialized)
