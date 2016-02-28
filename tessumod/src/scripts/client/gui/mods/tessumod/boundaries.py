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

def usecase_initialize():
	_execute(interactors.Initialize())

def usecase_load_settings(setting_vars):
	_execute(interactors.LoadSettings(), setting_vars)

def usecase_cache_chat_user(client_id, **client_data):
	_execute(interactors.CacheChatUser(), client_id, **client_data)

def usecase_pair_chat_user_to_player(client_id):
	_execute(interactors.PairChatUserToPlayer(), client_id)

def usecase_update_chat_user_speak_state(client_id):
	_execute(interactors.UpdateChatUserSpeakState(), client_id)

def usecase_remove_chat_user(client_id):
	_execute(interactors.RemoveChatUser(), client_id)

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

def usecase_notify_connected_to_chat_server(server_name):
	_execute(interactors.NotifyConnectedToChatServer(), server_name)

def usecase_publish_game_nick_to_chat_server():
	_execute(interactors.PublishGameNickToChatServer())

def usecase_show_cache_error_message(error_message):
	_execute(interactors.ShowCacheErrorMessage(), error_message)

def usecase_enable_positional_data_to_chat_client(enabled):
	_execute(interactors.EnablePositionalDataToChatClient(), enabled)

def usecase_provide_positional_data_to_chat_client():
	_execute(interactors.ProvidePositionalDataToChatClient())

def usecase_battle_replay_start():
	_execute(interactors.BattleReplayStart())

def usecase_populate_user_cache_with_players():
	_execute(interactors.PopulateUserCacheWithPlayers())
