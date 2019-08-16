import asyncio

import pytest

from .test_helpers.tools import contains_match, wait_until_true

'''
These fute test tests that notifications are shown in lobby.
'''

pytestmark = [pytest.mark.asyncio]

async def test_notification_connected_to_teamspeak_server_is_shown(game, cq_tsplugin):
	await cq_tsplugin.load(connected_to_server=True)
	game.start(mode="lobby")
	await game.wait_until_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info")

@pytest.mark.slow
async def test_notification_connected_to_teamspeak_server_is_not_shown(game, cq_tsplugin):
	await cq_tsplugin.load(connected_to_server=False)
	game.start(mode="lobby")
	await asyncio.sleep(2)
	assert not game.is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info")

async def test_notification_disconnected_from_teamspeak_client_is_shown(tessumod, game, cq_tsplugin):
	await cq_tsplugin.load()
	game.start(mode="lobby")
	await tessumod.wait_until_connected_to_ts_client()
	await cq_tsplugin.unload()
	await game.wait_until_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning")

async def test_notifications_not_shown_in_battle(tessumod, game, cq_tsplugin):
	await cq_tsplugin.load()
	game.start(mode="battle")
	await tessumod.wait_until_connected_to_ts_client()
	await cq_tsplugin.unload()
	await tessumod.wait_until_disconnected_from_ts_client()
	assert not game.is_system_notification_sent(message=contains_match("Connected to TeamSpeak client"), type="info")
	assert not game.is_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning")

async def test_notification_user_cache_error_is_shown(tessumod, game):
	game.start(mode="lobby")
	tessumod.change_user_cache(
		# undefined TS user and player paired together
		UserPlayerPairings = {
			"Erkki Meikalainen": "TuhoajaErkki"
		}
	)
	await game.wait_until_system_notification_sent(message=contains_match("Failed to read file"), type="error")
