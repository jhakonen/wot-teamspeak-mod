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

import interactors

def execute_initialize():
	_execute(interactors.Initialize())

def execute_load_settings(setting_vars):
	_execute(interactors.LoadSettings(), setting_vars)

def execute_cache_chat_user(client_id, **client_data):
	_execute(interactors.CacheChatUser(), client_id, **client_data)

def execute_pair_chat_user_to_player(client_id):
	_execute(interactors.PairChatUserToPlayer(), client_id)

def execute_update_chat_user_speak_state(client_id):
	_execute(interactors.UpdateChatUserSpeakState(), client_id)

def execute_remove_chat_user(client_id):
	_execute(interactors.RemoveChatUser(), client_id)

def execute_clear_speak_statuses():
	_execute(interactors.ClearSpeakStatuses())

def execute_notify_chat_client_disconnected():
	_execute(interactors.NotifyChatClientDisconnected())

def execute_show_chat_client_plugin_install_message():
	_execute(interactors.ShowChatClientPluginInstallMessage())

def execute_install_chat_client_plugin():
	_execute(interactors.InstallChatClientPlugin())

def execute_ignore_chat_client_plugin_install_message(ignored):
	_execute(interactors.IgnoreChatClientPluginInstallMessage(), ignored)

def execute_show_chat_client_plugin_info_url(url):
	_execute(interactors.ShowChatClientPluginInfoUrl(), url)

def execute_notify_connected_to_chat_server(server_name):
	_execute(interactors.NotifyConnectedToChatServer(), server_name)

def execute_publish_game_nick_to_chat_server():
	_execute(interactors.PublishGameNickToChatServer())

def execute_show_cache_error_message(error_message):
	_execute(interactors.ShowCacheErrorMessage(), error_message)

def execute_enable_positional_data_to_chat_client(enabled):
	_execute(interactors.EnablePositionalDataToChatClient(), enabled)

def execute_provide_positional_data_to_chat_client():
	_execute(interactors.ProvidePositionalDataToChatClient())

def execute_battle_replay_start():
	_execute(interactors.BattleReplayStart())

def execute_populate_user_cache_with_players():
	_execute(interactors.PopulateUserCacheWithPlayers())

def _execute(interactor, *args, **kwargs):
	return _inject_dependencies(interactor).execute(*args, **kwargs)

_injectables = {}

def inject(name, obj):
	_injectables[name] = obj

def get_injected(name):
	return _injectables[name]

def _inject_dependencies(target):
	for attr in target.INJECT:
		if attr in _injectables:
			setattr(target, attr, _injectables[attr])
	return target
