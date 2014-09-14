# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
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

import game
from tessu_utils.ts3 import TS3Client
from tessu_utils import utils
from debug_utils import LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
import BigWorld
import Avatar
import VOIP
from gui import SystemMessages

def on_talk_status_changed(user, talking):
	'''Called when TeamSpeak user's talk status changes.
	Parameters:
		user: a dict with WOT nickname (empty if not available) and TeamSpeak nickname 
		talking: True if talking, False otherwise
	'''
	if user["wot"]:
		vehicle = get_vehicle_by_player_name(user["wot"])
	else:
		vehicle = get_vehicle_by_player_name(user["ts"])
	if vehicle is not None:
		dbid = vehicle["accountDBID"]
		g_talk_states[dbid] = talking
		if talking:
			# set talking state immediately
			update_player_speak_status(dbid)
		else:
			# keep talking state for a little longer
			BigWorld.callback(1, utils.with_args(update_player_speak_status, dbid))

def get_vehicle_by_player_name(player_name):
	'''Searches vehicle which has given 'player_name' and returns it.
	Returns None if matching vehicle was not found.
	'''
	player_name = player_name.lower()
	try:
		for vehicle in BigWorld.player().arena.vehicles.values():
			if player_name == vehicle["name"].lower():
				return vehicle
	except AttributeError:
		pass

def update_player_speak_status(dbid):
	VOIP.getVOIPManager().setPlayerTalking(dbid, g_talk_states[dbid])

def on_connected_to_ts3():
	push_system_message("Connected to TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_disconnected_from_ts3():
	push_system_message("Disconnected from TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def push_system_message(message, type):
    try:
        if SystemMessages.g_instance is None:
            BigWorld.callback(1, utils.with_args(push_system_message, message, type))
        else:
            SystemMessages.pushMessage(message, type)
    except:
        LOG_CURRENT_EXCEPTION()
        return

def Avatar_onBecomePlayer(orig_method):
	def wrapper(self):
		orig_method(self)
		# save my WOT nickname to TeamSpeak's meta data so that other TeamSpeak
		# users can match the name to vehicles in battle when I'm speaking
		g_ts.set_wot_nickname(BigWorld.player().name)
	return wrapper

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		if dbid in g_talk_states:
			return g_talk_states[dbid]
		return orig_method(self, dbid)
	return wrapper

Avatar.Avatar.onBecomePlayer = Avatar_onBecomePlayer(Avatar.Avatar.onBecomePlayer)
VOIP.VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIP.VOIPManager.isParticipantTalking)

g_talk_states = {}
g_ts = TS3Client()
g_ts.connect()
g_ts.on_connected += on_connected_to_ts3
g_ts.on_disconnected += on_disconnected_from_ts3
g_ts.on_talk_status_changed += on_talk_status_changed
utils.call_in_loop(0.1, g_ts.check_events)
