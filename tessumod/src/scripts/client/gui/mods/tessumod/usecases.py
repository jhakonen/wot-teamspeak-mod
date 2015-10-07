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
import BigWorld
import VOIP
from utils import LOG_CURRENT_EXCEPTION

user_cache = None
settings = None
speak_states = None
minimap_ctrl = None

def find_and_pair_teamspeak_user_to_player(user):
	user_cache.add_ts_user(user.nick, user.unique_id)
	player = utils.ts_user_to_player(user,
		use_metadata = settings.get_wot_nick_from_ts_metadata(),
		use_ts_nick_search = settings.is_ts_nick_search_enabled(),
		extract_patterns = settings.get_nick_extract_patterns(),
		mappings = settings.get_name_mappings(),
		# TODO: should we use clanmembers=True, friends=True here too??
		players = utils.get_players(in_battle=True, in_prebattle=True)
	)
	if player:
		user_cache.add_player(player.name, player.id)
		user_cache.pair(player_id=player.id, ts_user_id=user.unique_id)

def set_teamspeak_user_speaking(user):
	for player_id in user_cache.get_paired_player_ids(user.unique_id):
		speak_states[player_id] = user.speaking
		if user.speaking:
			# set speaking state immediately
			_update_player_speak_status(player_id)
		else:
			# keep speaking state for a little longer
			BigWorld.callback(settings.get_speak_stop_delay(), utils.with_args(_update_player_speak_status, player_id))

def is_voice_chat_speak_allowed(player_id):
	if not settings.is_voice_chat_notifications_enabled():
		return False
	if not settings.is_self_voice_chat_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True

def _update_player_speak_status(player_id):
	try:
		talking = is_voice_chat_speak_allowed(player_id) and speak_states.get(player_id)
		VOIP.getVOIPManager().onPlayerSpeaking(player_id, talking)
	except:
		LOG_CURRENT_EXCEPTION()

	try:
		info = utils.get_player_info_by_dbid(player_id)
		talking = (
			speak_states.get(player_id) and
			_is_minimap_speak_allowed(player_id) and
			utils.get_vehicle(info["vehicle_id"])["isAlive"]
		)
		if talking:
			minimap_ctrl.start(info["vehicle_id"], settings.get_minimap_action(), settings.get_minimap_action_interval())
		else:
			minimap_ctrl.stop(info["vehicle_id"])
	except KeyError:
		# not an error, occurs in garage where there are no vehicles and
		# such no "vehicle_id"
		pass
	except:
		LOG_CURRENT_EXCEPTION()

def _is_minimap_speak_allowed(player_id):
	if not settings.is_minimap_notifications_enabled():
		return False
	if not settings.is_self_minimap_notifications_enabled() and utils.get_my_dbid() == player_id:
		return False
	return True