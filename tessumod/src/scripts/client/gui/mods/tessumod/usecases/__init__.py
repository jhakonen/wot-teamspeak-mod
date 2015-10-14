# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2015  Janne Hakonen
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

import interactors

_provided_dependencies = {}

def provide_dependency(name, obj):
	_provided_dependencies[name] = obj

def _execute(interactor, *args, **kwargs):
	return _inject_dependencies(interactor).execute(*args, **kwargs)

def _inject_dependencies(target):
	for attr in target.__class__.__dict__:
		if attr in _provided_dependencies:
			setattr(target, attr, _provided_dependencies[attr])
	return target

def usecase_insert_chat_user(client_id, nick, game_nick, unique_id, channel_id, speaking):
	_execute(interactors.InsertChatUser(), client_id, nick, game_nick, unique_id, channel_id, speaking)

def usecase_remove_chat_user(client_id):
	_execute(interactors.RemoveChatUser(), client_id)

def usecase_change_chat_channel(channel_id):
	_execute(interactors.ChangeChatChannel(), channel_id)

def usecase_is_voice_chat_speak_allowed():
	return _execute(interactors.CheckIsVoiceChatAllowed())

def usecase_clear_speak_statuses():
	_execute(interactors.ClearSpeakStatuses())

def usecase_notify_chat_client_disconnected():
	_execute(interactors.NotifyChatClientDisconnected())

def usecase_show_chat_client_plugin_install_message():
	_execute(interactors.ShowChatClientPluginInstallMessage())

def usecase_install_chat_client_plugin():
	_execute(interactors.InstallChatClientPlugin())

def usecase_ignore_chat_client_plugin_install_message(ignored):
	_execute(interactors.IgnoreChatClientPluginInstallMessage(), ignored)

def usecase_show_chat_client_plugin_info_url(url):
	_execute(interactors.ShowChatClientPluginInfoUrl(), url)
