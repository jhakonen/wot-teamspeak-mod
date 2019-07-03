from test_helpers.testcasebase import TestCaseBase
from test_helpers.utils import *
from messenger.proto.events import g_messengerEvents
from skeletons.gui.battle_session import IBattleSessionProvider
from helpers import dependency
import mock

class SpeakStatusChanges(TestCaseBase):
	'''
	This fute test tests that changes in TeamSpeak user's speaking status is shown in-game.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		session_provider = dependency.instance(IBattleSessionProvider)
		self.onPlayerSpeaking_mock = mock.Mock()
		self.onMinimapFeedbackReceived_mock = mock.Mock()
		g_messengerEvents.voip.onPlayerSpeaking += self.onPlayerSpeaking_mock
		self.original_onMinimapFeedbackReceived = session_provider.shared.feedback.onMinimapFeedbackReceived
		session_provider.shared.feedback.onMinimapFeedbackReceived = self.onMinimapFeedbackReceived_mock

	def tearDown(self):
		session_provider = dependency.instance(IBattleSessionProvider)
		g_messengerEvents.voip.onPlayerSpeaking -= self.onPlayerSpeaking_mock
		session_provider.shared.feedback.onMinimapFeedbackReceived = self.original_onMinimapFeedbackReceived
		TestCaseBase.tearDown(self)

	def __has_speaking_state_changed(self, name, speaking):
		return mock_was_called_with(self.onPlayerSpeaking_mock, self.get_player_id(name), speaking)

	def __has_minimap_feedback(self, name, action):
		from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
		return mock_was_called_with(self.onMinimapFeedbackReceived_mock, FEEDBACK_EVENT_ID.MINIMAP_SHOW_MARKER,
			self.get_vehicle_id(name), action)

	@use_event_loop
	def test_speak_feedback_starts_for_player_with_tessumod_installed(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="attack"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))

	@use_event_loop
	def test_speak_feedback_ends_for_player_with_tessumod_installed(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "firstEnemy"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}))
		self.on_event("on_connected_to_ts_server", lambda: self.call_later(lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": False}}), timeout=1))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="firstEnemy"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=False))

	@use_event_loop
	def test_speak_feedback_starts_for_player_with_matching_name(self):
		self.start_ts_client(connected_to_server=True, users={
			"TuhoajaERKKI [DUMMY]": {}
		})
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "help_me"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"TuhoajaERKKI [DUMMY]": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="help_me"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))

	@use_event_loop
	def test_speak_feedback_starts_for_player_with_extract_rule(self):
		self.start_ts_client(connected_to_server=True, users={
			"TuhoajaErkki / Erkki Meikalainen [DUMMY]": {}
		})
		self.change_mod_settings(
			General = {
				"ts_nick_search_enabled": "off",
				"nick_extract_patterns": "([a-z0-9_]+)"
			},
			MinimapNotifications = {
				"action": "negative"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"TuhoajaErkki / Erkki Meikalainen [DUMMY]": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="negative"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))

	@use_event_loop
	def test_speak_feedback_starts_for_player_with_mapping_rule(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen": {}
		})
		self.change_mod_settings(
			NameMappings = {
				"Erkki Meikalainen": "TuhoajaErkki"
			},
			MinimapNotifications = {
				"action": "positive"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="positive"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))

	@use_event_loop
	def test_speak_feedback_starts_for_player_with_combined_extract_and_mapping_rules(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen [DUMMY]": {}
		})
		self.change_mod_settings(
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
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen [DUMMY]": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="stop"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))

	@use_event_loop
	def test_no_speak_feedback_with_chat_notifications_disabled(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.change_mod_settings(
			VoiceChatNotifications = {
				"enabled": "off"
			},
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}))
		self.assert_finally_true(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="attack"))
		self.assert_finally_false(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))
		self.wait_at_least(secs=5)

	@use_event_loop
	def test_no_speak_feedback_with_minimap_notifications_disabled(self):
		self.start_ts_client(connected_to_server=True, users={
			"Erkki Meikalainen": {"metadata": "<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"}
		})
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "attack",
				"enabled": "off"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={"Erkki Meikalainen": {"speaking": True}}))
		self.assert_finally_false(lambda: self.__has_minimap_feedback(name="TuhoajaErkki", action="attack"))
		self.assert_finally_true(lambda: self.__has_speaking_state_changed(name="TuhoajaErkki", speaking=True))
		self.wait_at_least(secs=5)
