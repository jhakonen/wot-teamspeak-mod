from test_helpers.testcasebase import TestCaseBase
from test_helpers.utils import *
from messenger.proto.events import g_messengerEvents
from skeletons.gui.battle_session import IBattleSessionProvider
from helpers import dependency
from VOIP.VOIPManager import getVOIPManager

import mock
from nose.tools import assert_equal, assert_false, assert_true

import mod_tessumod

class SpeakStatusChanges(TestCaseBase):
	'''
	This fute test tests that changes in TeamSpeak user's speaking status is shown in-game.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		self.speak_feedback_state = {}
		self.ts_speak_state = {}
		session_provider = dependency.instance(IBattleSessionProvider)
		self.onMinimapFeedbackReceived_mock = mock.Mock()
		g_messengerEvents.voip.onPlayerSpeaking += self.__on_onPlayerSpeaking
		mod_tessumod.on_player_speaking += self.__on_player_speaking_in_ts
		self.original_onMinimapFeedbackReceived = session_provider.shared.feedback.onMinimapFeedbackReceived
		session_provider.shared.feedback.onMinimapFeedbackReceived = self.onMinimapFeedbackReceived_mock
		self.start_ts_client(connected_to_server=True)

	def tearDown(self):
		session_provider = dependency.instance(IBattleSessionProvider)
		g_messengerEvents.voip.onPlayerSpeaking -= self.__on_onPlayerSpeaking
		mod_tessumod.on_player_speaking -= self.__on_player_speaking_in_ts
		session_provider.shared.feedback.onMinimapFeedbackReceived = self.original_onMinimapFeedbackReceived
		TestCaseBase.tearDown(self)

	def __on_onPlayerSpeaking(self, id, speaking):
		self.speak_feedback_state[id] = speaking

	def __on_player_speaking_in_ts(self, id, speaking):
		self.ts_speak_state[id] = speaking

	def create_user(self, name):
		self.change_ts_client_state(users={name: {}})

	def insert_player_name_to_user_metadata(self, player_name, user_name):
		metadata = "<wot_nickname_start>%s<wot_nickname_end>" % player_name
		self.change_ts_client_state(users={user_name: {"metadata": metadata}})

	def wait_minimap_feedback(self, name, action):
		self.wait_until(lambda: self.has_minimap_feedback(name, action))

	def wait_speak_feedback(self, name, speaking):
		self.wait_until(lambda: speaking == self.get_speak_feedback_state(name))

	def get_speak_feedback_state(self, name):
		received = self.speak_feedback_state.get(self.get_player_id(name), None)
		queried = getVOIPManager().isParticipantTalking(self.get_player_id(name))
		assert_equal(received, queried, "Speak feedback state from event (%s) does not match queried value (%s)" % (received, queried))
		return received

	def has_minimap_feedback(self, name, action):
		from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
		return mock_was_called_with(self.onMinimapFeedbackReceived_mock, FEEDBACK_EVENT_ID.MINIMAP_SHOW_MARKER,
			self.get_vehicle_id(name), action)

	def set_ts_user_speaking(self, name, speaking):
		self.change_ts_client_state(users={name: {"speaking": speaking}})

	def wait_player_speaking(self, name, speaking):
		self.wait_until(lambda: self.ts_speak_state.get(self.get_player_id(name), None) == speaking)

	def set_game_voice_chat_speaking(self, name, speaking):
		getVOIPManager().fake_talkers[self.get_player_id(name)] = speaking
		g_messengerEvents.voip.onPlayerSpeaking(self.get_player_id(name), speaking)

	def test_speak_feedback_starts_for_player_with_tessumod_installed(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "attack")
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_speak_feedback_ends_for_player_with_tessumod_installed(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)
		self.set_ts_user_speaking("Erkki Meikalainen", False)
		self.wait_player_speaking("TuhoajaErkki", False)
		self.wait_speak_feedback("TuhoajaErkki", False)

	def test_speak_feedback_starts_for_player_with_matching_name(self):
		self.create_user("TuhoajaERKKI [DUMMY]")
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "help_me"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("TuhoajaERKKI [DUMMY]", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "help_me")
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_speak_feedback_starts_for_player_with_extract_rule(self):
		self.create_user("TuhoajaErkki / Erkki Meikalainen [DUMMY]")
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
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("TuhoajaErkki / Erkki Meikalainen [DUMMY]", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "negative")
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_speak_feedback_starts_for_player_with_mapping_rule(self):
		self.create_user("Erkki Meikalainen")
		self.change_mod_settings(
			NameMappings = {
				"Erkki Meikalainen": "TuhoajaErkki"
			},
			MinimapNotifications = {
				"action": "positive"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "positive")
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_speak_feedback_starts_for_player_with_combined_extract_and_mapping_rules(self):
		self.create_user("Erkki Meikalainen [DUMMY]")
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
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen [DUMMY]", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "stop")
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_starting_speech_in_game_voice_chat_shows_speak_feedback(self):
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.set_game_voice_chat_speaking("TuhoajaErkki", True)
		assert_equal(self.get_speak_feedback_state("TuhoajaErkki"), True)

	def test_ending_speech_in_game_voice_chat_shows_speak_feedback(self):
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.set_game_voice_chat_speaking("TuhoajaErkki", True)
		self.set_game_voice_chat_speaking("TuhoajaErkki", False)
		assert_equal(self.get_speak_feedback_state("TuhoajaErkki"), False)

	def test_starting_speech_in_both_chats_shows_speak_feedback(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.set_game_voice_chat_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_ending_speech_in_game_chat_but_not_in_ts_does_not_end_feedback(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.set_game_voice_chat_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)
		self.set_game_voice_chat_speaking("TuhoajaErkki", False)
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_ending_speech_in_ts_but_not_in_game_chat_does_not_end_feedback(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.set_game_voice_chat_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)
		self.set_ts_user_speaking("Erkki Meikalainen", False)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)

	def test_no_speak_feedback_with_chat_notifications_disabled(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.change_mod_settings(
			VoiceChatNotifications = {
				"enabled": "off"
			},
			MinimapNotifications = {
				"action": "attack"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_minimap_feedback("TuhoajaErkki", "attack")
		self.wait_speak_feedback("TuhoajaErkki", False)

	def test_no_speak_feedback_with_minimap_notifications_disabled(self):
		self.create_user("Erkki Meikalainen")
		self.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
		self.change_mod_settings(
			MinimapNotifications = {
				"action": "attack",
				"enabled": "off"
			}
		)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_event("on_connected_to_ts_server")
		self.set_ts_user_speaking("Erkki Meikalainen", True)
		self.wait_player_speaking("TuhoajaErkki", True)
		self.wait_speak_feedback("TuhoajaErkki", True)
		assert_false(self.has_minimap_feedback(name="TuhoajaErkki", action="attack"))
