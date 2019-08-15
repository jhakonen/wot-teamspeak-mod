import pytest

'''
These futes test that player's metadata is updated and contains player's nickname in it.
'''

pytestmark = [pytest.mark.asyncio]

@pytest.fixture(autouse=True)
async def test_setup(game, cq_tsplugin):
	cq_tsplugin.load(connected_to_server=True)
	game.start(mode="battle", player_name="TuhoajaErkki", players=[{"name": "TuhoajaErkki"}])


async def test_nickname_is_updated_to_metadata(game, cq_tsplugin):
	await cq_tsplugin.wait_until_user_metadata_equals("Testinukke",
		"<wot_nickname_start>TuhoajaErkki<wot_nickname_end>")

async def test_nickname_is_reapplied_to_metadata_if_it_is_overwritten(game, cq_tsplugin):
	await cq_tsplugin.wait_until_user_metadata_equals("Testinukke",
		"<wot_nickname_start>TuhoajaErkki<wot_nickname_end>")
	cq_tsplugin.set_user_metadata("Testinukke", "Version: 2.5.1.982\nArma Connected: No")
	await cq_tsplugin.wait_until_user_metadata_equals("Testinukke",
		"Version: 2.5.1.982\nArma Connected: No<wot_nickname_start>TuhoajaErkki<wot_nickname_end>")
