import pytest

'''
These futes test tests that positional audio data is passed to TessuMod TS plugin.
'''

pytestmark = [pytest.mark.asyncio]

@pytest.fixture(autouse=True)
async def test_setup(game, cq_tsplugin, my_tsplugin):
	my_tsplugin.load()
	await cq_tsplugin.load(connected_to_server=True)
	game.start(mode="battle")


async def test_tessumod_plugin_receives_camera_position(game, my_tsplugin):
	game.change_state(camera={"position": (100, 200, 50)})
	await my_tsplugin.wait_until_received_data_match("camera.position", (100, 200, 50))

async def test_tessumod_plugin_receives_camera_direction(game, my_tsplugin):
	game.change_state(camera={"direction": (10, 20, 30)})
	await my_tsplugin.wait_until_received_data_match("camera.direction", (10, 20, 30))

async def test_tessumod_plugin_receives_client_positions(tessumod, game, cq_tsplugin, my_tsplugin):
	cq_tsplugin.change_state(users={
		"TuhoajaErkki": {},
		"KaapuKalle": {}
	})
	game.change_state(players=[
		dict(name="TuhoajaErkki", position=(100, 100, 10)),
		dict(name="KaapuKalle", position=(150, 150, 20))
	])
	await tessumod.wait_until_connected_to_ts_server()
	cq_tsplugin.change_state(users={
		"TuhoajaErkki": {"speaking": True},
		"KaapuKalle": {"speaking": True}
	})
	await my_tsplugin.wait_until_received_data_match("clients.TuhoajaErkki.position", (100, 100, 10))
	await my_tsplugin.wait_until_received_data_match("clients.KaapuKalle.position", (150, 150, 20))
