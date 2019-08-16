import pytest

from .test_helpers.tools import *

'''
These futes test that changes in TeamSpeak user's speaking status is shown in-game.
'''

pytestmark = [pytest.mark.asyncio]

@pytest.fixture()
async def test_setup(game, tessumod, cq_tsplugin):
	await cq_tsplugin.load(connected_to_server=True)
	game.start(mode="battle", players=[{"name": "TuhoajaErkki"}])
	yield SpeakStateFixture(game, tessumod, cq_tsplugin)

class SpeakStateFixture:

	def __init__(self, game, tessumod, cq_tsplugin):
		self._game = game
		self._tessumod = tessumod
		self._cq_tsplugin = cq_tsplugin

	def create_user(self, name):
		self._cq_tsplugin.change_state(users={name: {}})

	def set_player_speaking(self, name, speaking):
		self._cq_tsplugin.change_state(users={name: {"speaking": speaking}})

	def insert_player_name_to_user_metadata(self, player_name, user_name):
		metadata = "<wot_nickname_start>%s<wot_nickname_end>" % player_name
		self._cq_tsplugin.change_state(users={user_name: {"metadata": metadata}})

	def get_speak_feedback_state(self, name):
		return self._game.is_player_speaking(self._game.get_player_id(name))

	def set_game_voice_chat_speaking(self, name, speaking):
		self._game.set_game_voice_chat_speaking(self._game.get_player_id(name), speaking)

	def has_minimap_feedback(self, name, action):
		return self._game.has_minimap_feedback(self._game.get_vehicle_id(name), action)

	async def wait_until_player_speaking(self, name, speaking):
		await self._tessumod.wait_player_speaking_in_ts(self._game.get_player_id("TuhoajaErkki"), True)

	async def wait_minimap_feedback(self, name, action):
		await wait_until_true(lambda: self.has_minimap_feedback(name, action))

	async def wait_speak_feedback(self, name, speaking):
		await wait_until_true(lambda: speaking == self._game.is_player_speaking(self._game.get_player_id(name)))


async def test_speak_feedback_starts_for_player_with_tessumod_installed(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	tessumod.change_settings(
		MinimapNotifications = {
			"action": "attack"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "attack")
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_speak_feedback_ends_for_player_with_tessumod_installed(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)
	test_setup.set_player_speaking("Erkki Meikalainen", False)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", False)
	await test_setup.wait_speak_feedback("TuhoajaErkki", False)

async def test_speak_feedback_starts_for_player_with_matching_name(test_setup, tessumod):
	test_setup.create_user("TuhoajaERKKI [DUMMY]")
	tessumod.change_settings(
		MinimapNotifications = {
			"action": "help_me"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("TuhoajaERKKI [DUMMY]", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "help_me")
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_speak_feedback_starts_for_player_with_extract_rule(test_setup, tessumod):
	test_setup.create_user("TuhoajaErkki / Erkki Meikalainen [DUMMY]")
	tessumod.change_settings(
		General = {
			"ts_nick_search_enabled": "off",
			"nick_extract_patterns": "([a-z0-9_]+)"
		},
		MinimapNotifications = {
			"action": "negative"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("TuhoajaErkki / Erkki Meikalainen [DUMMY]", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "negative")
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_speak_feedback_starts_for_player_with_mapping_rule(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	tessumod.change_settings(
		NameMappings = {
			"Erkki Meikalainen": "TuhoajaErkki"
		},
		MinimapNotifications = {
			"action": "positive"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "positive")
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_speak_feedback_starts_for_player_with_combined_extract_and_mapping_rules(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen [DUMMY]")
	tessumod.change_settings(
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
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen [DUMMY]", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "stop")
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_starting_speech_in_game_voice_chat_shows_speak_feedback(test_setup):
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", True)
	assert test_setup.get_speak_feedback_state("TuhoajaErkki") == True

async def test_ending_speech_in_game_voice_chat_shows_speak_feedback(test_setup):
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", True)
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", False)
	assert test_setup.get_speak_feedback_state("TuhoajaErkki") == False

async def test_starting_speech_in_both_chats_shows_speak_feedback(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_ending_speech_in_game_chat_but_not_in_ts_does_not_end_feedback(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", False)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_ending_speech_in_ts_but_not_in_game_chat_does_not_end_feedback(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	test_setup.set_game_voice_chat_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)
	test_setup.set_player_speaking("Erkki Meikalainen", False)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)

async def test_no_speak_feedback_with_chat_notifications_disabled(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	tessumod.change_settings(
		VoiceChatNotifications = {
			"enabled": "off"
		},
		MinimapNotifications = {
			"action": "attack"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_minimap_feedback("TuhoajaErkki", "attack")
	await test_setup.wait_speak_feedback("TuhoajaErkki", False)

async def test_no_speak_feedback_with_minimap_notifications_disabled(test_setup, tessumod):
	test_setup.create_user("Erkki Meikalainen")
	test_setup.insert_player_name_to_user_metadata("TuhoajaErkki", "Erkki Meikalainen")
	tessumod.change_settings(
		MinimapNotifications = {
			"action": "attack",
			"enabled": "off"
		}
	)
	await tessumod.wait_until_connected_to_ts_server()
	test_setup.set_player_speaking("Erkki Meikalainen", True)
	await test_setup.wait_until_player_speaking("TuhoajaErkki", True)
	await test_setup.wait_speak_feedback("TuhoajaErkki", True)
	assert not test_setup.has_minimap_feedback(name="TuhoajaErkki", action="attack")
