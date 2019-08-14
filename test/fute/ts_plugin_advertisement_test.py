import asyncio
import copy
import time

import pytest

from .test_helpers import constants
from .test_helpers.v2_tools import *

'''
These futes test that TessuMod Plugin is advertised in lobby.
'''

pytestmark = [
	pytest.mark.asyncio
]

def is_install_advertisement_shown(game):
	return game.is_complex_notification_sent(["Would you like to install TessuMod plugin for TeamSpeak?"])

def is_update_advertisement_shown(game):
	return game.is_complex_notification_sent(["There is a new version of TessuMod plugin available, would you like to download it?"])

def __on_notification(callback):
	self.__get_model().on_addNotification += callback

def __handleAction(**kwargs):
	notification.NotificationMVC.g_instance.handleAction(**kwargs)

async def test_ts_plugin_install_advertisement_is_shown(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	game.start(mode="lobby")
	await wait_until_true(lambda: is_install_advertisement_shown(game))

async def test_ts_plugin_update_advertisement_is_shown(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	new_version = copy.copy(constants.PLUGIN_INFO["versions"][0])
	new_version["plugin_version"] = 2
	plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
	plugin_info["versions"].append(new_version)
	httpserver.set_plugin_info(plugin_info)
	cq_tsplugin.load()
	my_tsplugin.load(version=1)
	game.start(mode="lobby")
	await wait_until_true(lambda: is_update_advertisement_shown(game))

async def test_ts_plugin_too_old_warning_shown(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	httpserver.set_plugin_info({
		"versions": [{
			"plugin_version": 1,
			"supported_mod_versions": ["0.5", "0.6"],
		}, {
			"plugin_version": 2,
			"supported_mod_versions": ["0.6"],
			"download_url": "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"
		}]
	})
	cq_tsplugin.load()
	my_tsplugin.load(version=1)
	tessumod.change_state_variables(ignored_plugin_versions=[2])
	game.start(mode="lobby")
	await game.wait_until_system_notification_sent(
		message=contains_match("TessuMod TeamSpeak plugin you have installed into your TeamSpeak client is too old"),
		type="warning"
	)

async def test_game_mod_too_old_warning_shown(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	httpserver.set_plugin_info({
		"versions": [{
			"plugin_version": 1,
			"supported_mod_versions": ["0.8"],
			"download_url": "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"
		}]
	})
	cq_tsplugin.load()
	my_tsplugin.load(version=1)
	game.start(mode="lobby")
	await game.wait_until_system_notification_sent(
		message=contains_match("Your TessuMod version is older than what your current TessuMod TeamSpeak plugin can support"),
		type="warning"
	)

@pytest.mark.slow
async def test_ts_plugin_advertisement_is_not_shown_if_already_installed(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	my_tsplugin.load(version=1)
	game.start(mode="lobby")
	await asyncio.sleep(2)
	assert not is_install_advertisement_shown(game)

@pytest.mark.slow
async def test_ts_plugin_advertisement_is_not_shown_if_ignored(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	tessumod.change_state_variables(ignored_plugin_versions=[1])
	game.start(mode="lobby")
	await asyncio.sleep(2)
	assert not is_install_advertisement_shown(game)

@pytest.mark.slow
async def test_ts_plugin_advertisement_is_not_shown_if_ignored_deprecated(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	# This tests that ignored_plugin_version state variable (from 0.6.x
	# versions) still works
	cq_tsplugin.load()
	tessumod.change_state_variables(ignored_plugin_version=1)
	game.start(mode="lobby")
	await asyncio.sleep(2)
	assert not is_install_advertisement_shown(game)

async def test_download_button_opens_download_page_to_web_browser(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	game.start(mode="lobby")
	await wait_until_true(lambda: is_install_advertisement_shown(game))
	msg = game.get_latest_complex_notification()
	game.send_notification_action(msg, "TessuModTSPluginDownload")
	await game.wait_until_url_opened_to_web_browser("https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed")

async def test_ignore_link_saves_ignore_state(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	game.start(mode="lobby")
	await wait_until_true(lambda: is_install_advertisement_shown(game))
	msg = game.get_latest_complex_notification()
	assert tessumod.get_state_variable("ignored_plugin_versions") != [1]
	game.send_notification_action(msg, "TessuModTSPluginIgnore")
	assert tessumod.get_state_variable("ignored_plugin_versions") == [1]

async def test_plugin_info_is_cached(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	cq_tsplugin.load()
	with ExecTimer() as t:
		game.start(mode="lobby")
		await wait_until_true(lambda: is_install_advertisement_shown(game))
	cached_plugin_info = tessumod.get_state_variable("plugin_info")
	cached_timestamp = tessumod.get_state_variable("plugin_info_timestamp")
	assert cached_plugin_info == constants.PLUGIN_INFO
	assert cached_timestamp > t.start and cached_timestamp < t.end

async def test_plugin_info_is_read_from_cache(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	await httpserver.stop()
	tessumod.change_state_variables(
		plugin_info=constants.PLUGIN_INFO,
		plugin_info_timestamp=time.time()
	)
	cq_tsplugin.load()
	game.start(mode="lobby")
	await wait_until_true(lambda: is_install_advertisement_shown(game))

async def test_cached_plugin_info_becomes_stale_after_a_week(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	old_plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
	old_plugin_info["versions"][0]["download_url"] = "http://old.url/"
	tessumod.change_state_variables(
		plugin_info=old_plugin_info,
		plugin_info_timestamp=time.time() - 60 * 60 * 24 * 7
	)
	cq_tsplugin.load()
	with ExecTimer() as t:
		game.start(mode="lobby")
		await wait_until_true(lambda: is_install_advertisement_shown(game))
	new_plugin_info = tessumod.get_state_variable("plugin_info")
	new_timestamp = tessumod.get_state_variable("plugin_info_timestamp")
	assert new_plugin_info == constants.PLUGIN_INFO
	assert new_plugin_info != old_plugin_info
	assert new_timestamp > t.start and new_timestamp < t.end

async def test_cached_plugin_info_becomes_stale_if_timestamp_is_set_in_future_by_a_week(game, tessumod, cq_tsplugin, my_tsplugin, httpserver):
	old_plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
	old_plugin_info["versions"][0]["download_url"] = "http://old.url/"
	tessumod.change_state_variables(
		plugin_info=old_plugin_info,
		plugin_info_timestamp=time.time() + 60 * 60 * 24 * 7 + 60
	)
	cq_tsplugin.load()
	with ExecTimer() as t:
		game.start(mode="lobby")
		await wait_until_true(lambda: is_install_advertisement_shown(game))
	new_plugin_info = tessumod.get_state_variable("plugin_info")
	new_timestamp = tessumod.get_state_variable("plugin_info_timestamp")
	assert new_plugin_info == constants.PLUGIN_INFO
	assert new_plugin_info != old_plugin_info
	assert new_timestamp > t.start and new_timestamp < t.end
