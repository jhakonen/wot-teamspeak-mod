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

import utils
import adapters
import BigWorld
import VOIP
from utils import LOG_CURRENT_EXCEPTION

speak_states = None

def find_and_pair_teamspeak_user_to_player(user):
	adapters.g_user_cache.add_teamspeak_user(user)
	player = utils.ts_user_to_player(user,
		use_metadata = adapters.g_settings.get_wot_nick_from_ts_metadata(),
		use_ts_nick_search = adapters.g_settings.is_ts_nick_search_enabled(),
		extract_patterns = adapters.g_settings.get_nick_extract_patterns(),
		mappings = adapters.g_settings.get_name_mappings(),
		# TODO: should we use clanmembers=True, friends=True here too??
		players = utils.get_players(in_battle=True, in_prebattle=True)
	)
	if player:
		adapters.g_user_cache.add_player(player)
		adapters.g_user_cache.pair(player, user)

def set_teamspeak_user_speaking(user):
	for player_id in adapters.g_user_cache.get_paired_player_ids(user):
		speak_states[player_id] = user.speaking
		if user.speaking:
			# set speaking state immediately
			_update_player_speak_status(player_id)
		else:
			# keep speaking state for a little longer
			BigWorld.callback(adapters.g_settings.get_speak_stop_delay(), utils.with_args(_update_player_speak_status, player_id))

def is_voice_chat_speak_allowed(player_id):
	if not adapters.g_settings.is_voice_chat_notifications_enabled():
		return False
	if not adapters.g_settings.is_self_voice_chat_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def _update_player_speak_status(player_id):
	try:
		speaking = is_voice_chat_speak_allowed(player_id) and speak_states.get(player_id)
		VOIP.getVOIPManager().onPlayerSpeaking(player_id, speaking)
	except:
		LOG_CURRENT_EXCEPTION()

	try:
		player = utils.get_player_by_dbid(player_id)
		speaking = (
			speak_states.get(player.id) and
			_is_minimap_speak_allowed(player.id) and
			player.is_alive
		)
		adapters.g_minimap.set_player_speaking(player, speaking)
	except:
		LOG_CURRENT_EXCEPTION()

def _is_minimap_speak_allowed(player_id):
	if not adapters.g_settings.is_minimap_notifications_enabled():
		return False
	if not adapters.g_settings.is_self_minimap_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True
