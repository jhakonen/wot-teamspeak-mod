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

def on_talk_status_changed(user, talking):
	'''Called when TeamSpeak user's talk status changes.
	Parameters:
		user: a dict with WOT nickname (empty if not available) and TeamSpeak nickname 
		talking: True if talking, False otherwise
	'''
	player_name = (user["wot"] if user["wot"] else user["ts"]).lower()
	g_talk_states[player_name] = talking
	if talking:
		# set talking state immediately
		update_player_speak_status(player_name)
	else:
		# keep talking state for a little longer
		BigWorld.callback(1, utils.with_args(update_player_speak_status, player_name))

def update_player_speak_status(player_name):
	'''Updates given 'player_name's talking status to VOIP system and minimap.''' 
	player_name = player_name.lower()
	info = utils.get_player_info_by_name(player_name)
	try:
		VOIP.getVOIPManager().setPlayerTalking(info["dbid"], g_talk_states[player_name])
	except:
		pass
	try:
		if g_talk_states[player_name]:
			g_marker_repeater.start(info["vehicle_id"])
		else:
			g_marker_repeater.stop(info["vehicle_id"])
	except:
		pass

def on_connected_to_ts3():
	'''Called when TessuMod manages to connect TeamSpeak client. However, this
	doesn't mean that the client is connected to any TeamSpeak server.
	'''
	LOG_NOTE("Connected to TeamSpeak client")
	utils.push_system_message("Connected to TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_disconnected_from_ts3():
	'''Called when TessuMod loses connection to TeamSpeak client.'''
	LOG_NOTE("Disconnected from TeamSpeak client")
	g_marker_repeater.stop_all()
	utils.push_system_message("Disconnected from TeamSpeak client", SystemMessages.SM_TYPE.Warning)

def on_connected_to_ts3_server():
	LOG_NOTE("Connected to TeamSpeak server")
	g_ts.set_wot_nickname(utils.get_my_name())

def on_disconnected_from_ts3_server():
	LOG_NOTE("Disconnected from TeamSpeak server")

def Player_onBecomePlayer(orig_method):
	def wrapper(self):
		'''Called when BigWorld.player() is available.'''
		orig_method(self)
		g_ts.set_wot_nickname(utils.get_my_name())
	return wrapper

def VOIPManager_isParticipantTalking(orig_method):
	def wrapper(self, dbid):
		'''Called by other game modules to determine current speaking status.'''
		try:
			return g_talk_states[utils.get_player_info_by_dbid(dbid)["player_name"].lower()]
		except:
			pass
		return orig_method(self, dbid)
	return wrapper

try:
	import game
	from tessu_utils.ts3 import TS3Client
	from tessu_utils import utils
	from debug_utils import LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
	import BigWorld
	import Avatar
	import Account
	import VOIP
	from gui import SystemMessages

	# do all intializations here
	g_talk_states = {}
	g_marker_repeater = utils.MarkerRepeater(interval=3.5, action="attackSender")
	g_ts = TS3Client()
	g_ts.connect()
	g_ts.on_connected += on_connected_to_ts3
	g_ts.on_disconnected += on_disconnected_from_ts3
	g_ts.on_connected_to_server += on_connected_to_ts3_server
	g_ts.on_disconnected_from_server += on_disconnected_from_ts3_server
	g_ts.on_talk_status_changed += on_talk_status_changed
	utils.call_in_loop(0.1, g_ts.check_events)

	# if nothing broke so far then it should be safe to patch the needed
	# functions (modified functions have dependencies to g_* global variables)
	Avatar.Avatar.onBecomePlayer = Player_onBecomePlayer(Avatar.Avatar.onBecomePlayer)
	Account.PlayerAccount.onBecomePlayer = Player_onBecomePlayer(Account.PlayerAccount.onBecomePlayer)
	VOIP.VOIPManager.isParticipantTalking = VOIPManager_isParticipantTalking(VOIP.VOIPManager.isParticipantTalking)
except:
	LOG_CURRENT_EXCEPTION()
