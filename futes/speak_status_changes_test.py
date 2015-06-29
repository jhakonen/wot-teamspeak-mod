from helpers.testcasebase import TestCaseBase
from helpers.utils import *
import mock

class SpeakStatusChanges(TestCaseBase):
	'''
	This fute test tests that changes in TeamSpeak user's speaking status is shown in-game.
	To execute, use command:
		$ nosetests --with-process-isolation
	'''

	def setUp(self):
		TestCaseBase.setUp(self)

		import VOIP
		from gui.app_loader import g_appLoader
		self.VOIP_onPlayerSpeaking = VOIP.getVOIPManager().onPlayerSpeaking = mock.Mock()
		self.Minimap_showActionMarker = g_appLoader.getApp().minimap.showActionMarker = mock.Mock()

	def test_speak_feedback_starts_for_player_with_tessumod_installed(self):
		self.change_mod_settings_state(
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}})
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "attack"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_speak_feedback_ends_for_player_with_tessumod_installed(self):
		self.change_mod_settings_state(
			MinimapNotifications = {
				"action": "firstEnemy"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}),
				lambda: self.call_later(lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": False}}), timeout=1)
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "firstEnemy"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), False)
		])

	def test_speak_feedback_starts_for_player_with_matching_name(self):
		self.change_mod_settings_state(
			MinimapNotifications = {
				"action": "help_me"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"TuhoajaERKKI [DUMMY]": {}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"TuhoajaERKKI [DUMMY]": {"speaking": True}})
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "help_me"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_speak_feedback_starts_for_player_with_extract_rule(self):
		self.change_mod_settings_state(
			General = {
				"ts_nick_search_enabled": "off",
				"nick_extract_patterns": "([a-z0-9_]+)"
			},
			MinimapNotifications = {
				"action": "negative"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"TuhoajaErkki / Erkki Meikalainen [DUMMY]": {}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"TuhoajaErkki / Erkki Meikalainen [DUMMY]": {"speaking": True}})
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "negative"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_speak_feedback_starts_for_player_with_mapping_rule(self):
		self.change_mod_settings_state(
			NameMappings = {
				"Erkki Meikalainen": "TuhoajaErkki"
			},
			MinimapNotifications = {
				"action": "positive"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen": {}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}})
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "positive"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_speak_feedback_starts_for_player_with_combined_extract_and_mapping_rules(self):
		self.change_mod_settings_state(
			General = {
				"ts_nick_search_enabled": "off",
				"nick_extract_patterns": "(.+)\\[DUMMY\\]"
			},
			NameMappings = {
				"Erkki Meikalainen": "TuhoajaErkki",
			},
			MinimapNotifications = {
				"action": "stop"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen [DUMMY]": {}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen [DUMMY]": {"speaking": True}})
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "stop"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_no_speak_feedback_with_chat_notifications_disabled(self):
		self.change_mod_settings_state(
			VoiceChatNotifications = {
				"enabled": "off"
			},
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}})
			]
		})
		self.run_in_event_loop(min_wait=5, verifiers=[
			lambda: mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "attack"),
			lambda: not mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])

	def test_no_speak_feedback_with_minimap_notifications_disabled(self):
		self.change_mod_settings_state(
			MinimapNotifications = {
				"action": "attack",
				"enabled": "off"
			}
		)
		self.change_game_state(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.change_ts_client_state(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}})
			]
		})
		self.run_in_event_loop(min_wait=5, verifiers=[
			lambda: not mock_was_called_with(self.Minimap_showActionMarker, self.get_vehicle_id("TuhoajaErkki"), "attack"),
			lambda: mock_was_called_with(self.VOIP_onPlayerSpeaking, self.get_player_id("TuhoajaErkki"), True)
		])
