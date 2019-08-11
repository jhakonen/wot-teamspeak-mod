import copy
import os
import time
from unittest import mock

from nose.plugins.attrib import attr

import BigWorld
from gui import SystemMessages
from helpers import dependency
import notification
from skeletons.gui.system_messages import ISystemMessages

from .test_helpers import constants
from .test_helpers.testcasebase import TestCaseBase
from .test_helpers.utils import *

BigWorld_wg_openWebBrowser = BigWorld.wg_openWebBrowser

class TSPluginAdvertisement(TestCaseBase):
	'''
	This fute test tests TessuMod Plugin is advertised in lobby.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		self.addNotification_mock = mock.Mock()
		self.__get_model().on_addNotification += self.addNotification_mock
		BigWorld.wg_openWebBrowser = mock.Mock()
		dependency.instance(ISystemMessages).pushMessage = mock.Mock()

	def tearDown(self):
		self.__get_model().on_addNotification.clear()
		BigWorld.wg_openWebBrowser = BigWorld_wg_openWebBrowser
		TestCaseBase.tearDown(self)

	def __get_model(self):
		return notification.NotificationMVC.g_instance.getModel()

	def __is_install_advertisement_shown(self):
		return mock_was_called_with(self.addNotification_mock, message_decorator_matches_fragments(
			["Would you like to install TessuMod plugin for TeamSpeak?"]))

	def __is_update_advertisement_shown(self):
		return mock_was_called_with(self.addNotification_mock, message_decorator_matches_fragments(
			["There is a new version of TessuMod plugin available, would you like to download it?"]))

	def __is_warning_shown(self, message_fragment):
		return mock_was_called_with(
			dependency.instance(ISystemMessages).pushMessage,
			contains_match(message_fragment),
			SystemMessages.SM_TYPE.Warning,
		)

	def __on_notification(self, callback):
		self.__get_model().on_addNotification += callback

	def __handleAction(self, **kwargs):
		notification.NotificationMVC.g_instance.handleAction(**kwargs)

	def test_ts_plugin_install_advertisement_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_install_advertisement_shown())

	def test_ts_plugin_update_advertisement_is_shown(self):
		new_version = copy.copy(constants.PLUGIN_INFO["versions"][0])
		new_version["plugin_version"] = 2
		plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
		plugin_info["versions"].append(new_version)
		self.set_plugin_info(plugin_info)
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_update_advertisement_shown())

	def test_ts_plugin_too_old_warning_shown(self):
		self.set_plugin_info({
			"versions": [{
				"plugin_version": 1,
				"supported_mod_versions": ["0.5", "0.6"],
			}, {
				"plugin_version": 2,
				"supported_mod_versions": ["0.6"],
				"download_url": "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"
			}]
		})
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.change_mod_state_variables(ignored_plugin_versions=[2])
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_warning_shown("TessuMod TeamSpeak plugin you have installed into your TeamSpeak client is too old"))

	def test_game_mod_too_old_warning_shown(self):
		self.set_plugin_info({
			"versions": [{
				"plugin_version": 1,
				"supported_mod_versions": ["0.8"],
				"download_url": "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"
			}]
		})
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_warning_shown("Your TessuMod version is older than what your current TessuMod TeamSpeak plugin can support"))

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_already_installed(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_install_advertisement_shown())
		self.wait_at_least(secs=5)

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_ignored(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		self.change_mod_state_variables(ignored_plugin_versions=[1])
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_install_advertisement_shown())
		self.wait_at_least(secs=5)

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_ignored_deprecated(self):
		# This tests that ignored_plugin_version state variable (from 0.6.x
		# versions) still works
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		self.change_mod_state_variables(ignored_plugin_version=1)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_install_advertisement_shown())
		self.wait_at_least(secs=5)

	def test_download_button_opens_download_page_to_web_browser(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.__on_notification(lambda msg: self.__handleAction(
			typeID = msg.getType(),
			entityID = msg.getID(),
			action = "TessuModTSPluginDownload"
		))
		self.wait_until(lambda: mock_was_called_with(BigWorld.wg_openWebBrowser, "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"))

	@use_event_loop
	def test_ignore_link_saves_ignore_state(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.__on_notification(lambda msg: self.__handleAction(
			typeID = msg.getType(),
			entityID = msg.getID(),
			action = "TessuModTSPluginIgnore"
		))
		assert self.get_mod_state_variable("ignored_plugin_versions") != [1]
		self.assert_finally_equal([1], lambda: self.get_mod_state_variable("ignored_plugin_versions"))

	def test_plugin_info_is_cached(self):
		start_time = time.time()
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_install_advertisement_shown())
		end_time = time.time()
		cached_plugin_info = self.get_mod_state_variable("plugin_info")
		cached_timestamp = self.get_mod_state_variable("plugin_info_timestamp")
		assert cached_plugin_info == constants.PLUGIN_INFO
		assert cached_timestamp > start_time
		assert cached_timestamp < end_time

	def test_plugin_info_is_read_from_cache(self):
		self.stop_http_server()
		self.change_mod_state_variables(
			plugin_info=constants.PLUGIN_INFO,
			plugin_info_timestamp=time.time()
		)
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_install_advertisement_shown())

	def test_cached_plugin_info_becomes_stale_after_a_week(self):
		old_plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
		old_plugin_info["versions"][0]["download_url"] = "http://old.url/"
		self.change_mod_state_variables(
			plugin_info=old_plugin_info,
			plugin_info_timestamp=time.time() - 60 * 60 * 24 * 7
		)
		start_time = time.time()
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_install_advertisement_shown())
		end_time = time.time()
		new_plugin_info = self.get_mod_state_variable("plugin_info")
		new_timestamp = self.get_mod_state_variable("plugin_info_timestamp")
		assert new_plugin_info == constants.PLUGIN_INFO
		assert new_plugin_info != old_plugin_info
		assert new_timestamp > start_time
		assert new_timestamp < end_time

	def test_cached_plugin_info_becomes_stale_if_timestamp_is_set_in_future_by_a_week(self):
		old_plugin_info = copy.deepcopy(constants.PLUGIN_INFO)
		old_plugin_info["versions"][0]["download_url"] = "http://old.url/"
		self.change_mod_state_variables(
			plugin_info=old_plugin_info,
			plugin_info_timestamp=time.time() + 60 * 60 * 24 * 7 + 60
		)
		start_time = time.time()
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.wait_until(lambda: self.__is_install_advertisement_shown())
		end_time = time.time()
		new_plugin_info = self.get_mod_state_variable("plugin_info")
		new_timestamp = self.get_mod_state_variable("plugin_info_timestamp")
		assert new_plugin_info == constants.PLUGIN_INFO
		assert new_plugin_info != old_plugin_info
		assert new_timestamp > start_time
		assert new_timestamp < end_time
