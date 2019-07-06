from test_helpers.testcasebase import TestCaseBase, TS_PLUGIN_INSTALLER_PATH
from test_helpers.utils import *

import notification

from nose.plugins.attrib import attr
import mock
import os

class TSPluginAdvertisement(TestCaseBase):
	'''
	This fute test tests TessuMod Plugin is advertised in lobby.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		self.addNotification_mock = mock.Mock()
		self.__get_model().on_addNotification += self.addNotification_mock

	def tearDown(self):
		self.__get_model().on_addNotification.clear()
		TestCaseBase.tearDown(self)

	def __get_model(self):
		return notification.NotificationMVC.g_instance.getModel()

	def __is_advertisement_shown(self):
		return mock_was_called_with(self.addNotification_mock, message_decorator_matches_fragments(
			["TessuModTSPluginInstall", "TessuModTSPluginMoreInfo", "TessuModTSPluginIgnore"]))

	def __on_notification(self, callback):
		self.__get_model().on_addNotification += callback

	def __handleAction(self, **kwargs):
		notification.NotificationMVC.g_instance.handleAction(**kwargs)

	@use_event_loop
	def test_ts_plugin_advertisement_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.assert_finally_true(lambda: self.__is_advertisement_shown())

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_already_installed(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_advertisement_shown())
		self.wait_at_least(secs=5)

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_installer_is_missing(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		os.remove(TS_PLUGIN_INSTALLER_PATH)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_advertisement_shown())
		self.wait_at_least(secs=5)

	@attr("slow")
	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_ignored(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client()
		self.change_mod_state_variables(ignored_plugin_version=1)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_advertisement_shown())
		self.wait_at_least(secs=5)

	@mock.patch("subprocess.call")
	@use_event_loop
	def test_install_button_starts_plugin_installer(self, subprocess_call_mock):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.__on_notification(lambda msg: self.__handleAction(
			typeID = msg.getType(),
			entityID = msg.getID(),
			action = "TessuModTSPluginInstall"
		))
		self.assert_finally_true(lambda: mock_was_called_with(
			subprocess_call_mock,
			args = [contains_match("tessumod.ts3_plugin")],
			shell = True
		))

	@use_event_loop
	def test_ignore_link_saves_ignore_state(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.__on_notification(lambda msg: self.__handleAction(
			typeID = msg.getType(),
			entityID = msg.getID(),
			action = "TessuModTSPluginIgnore"
		))
		assert self.get_mod_state_variable("ignored_plugin_version") != "1"
		self.assert_finally_equal("1", lambda: self.get_mod_state_variable("ignored_plugin_version"))
