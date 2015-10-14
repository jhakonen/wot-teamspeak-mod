from helpers.testcasebase import TestCaseBase, TS_PLUGIN_INSTALLER_PATH
from helpers.utils import *
import mock
import os
import nosepipe

@nosepipe.isolate
class TSPluginAdvertisement(TestCaseBase):
	'''
	This fute test tests TessuMod Plugin is advertised in lobby.
	To execute, use command:
		$ nosetests --with-process-isolation
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		import notification
		self.mock_addNotification = notification.NotificationMVC.g_instance.getModel().addNotification = mock.Mock(
			wraps=notification.NotificationMVC.g_instance.getModel().addNotification
		)

	def __is_advertisement_shown(self):
		return mock_was_called_with(self.mock_addNotification, message_decorator_matches_fragments(
			["TessuModTSPluginInstall", "TessuModTSPluginMoreInfo", "TessuModTSPluginIgnore"]))

	@use_event_loop
	def test_ts_plugin_advertisement_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.assert_finally_true(lambda: self.__is_advertisement_shown())

	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_already_installed(self):
		self.start_ts_client()
		self.enable_ts_client_tessumod_plugin(version=1)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_advertisement_shown())
		self.wait_at_least(secs=5)

	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_installer_is_missing(self):
		self.start_ts_client()
		os.remove(TS_PLUGIN_INSTALLER_PATH)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_advertisement_shown())
		self.wait_at_least(secs=5)

	@use_event_loop
	def test_ts_plugin_advertisement_is_not_shown_if_ignored(self):
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
		import notification
		def on_notification(msg):
			notification.NotificationMVC.g_instance.handleAction(typeID=msg.getType(), entityID=msg.getID(), action="TessuModTSPluginInstall")
		notification.NotificationMVC.g_instance.futes_on_add_notification += on_notification
		self.assert_finally_true(lambda: mock_was_called_with(subprocess_call_mock, args=[contains_match("tessumod.ts3_plugin")], shell=True))

	@use_event_loop
	def test_ignore_link_saves_ignore_state(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		import notification
		def on_notification(msg):
			notification.NotificationMVC.g_instance.handleAction(typeID=msg.getType(), entityID=msg.getID(), action="TessuModTSPluginIgnore")
		notification.NotificationMVC.g_instance.futes_on_add_notification += on_notification
		assert self.get_mod_state_variable("ignored_plugin_version") != 1
		self.assert_finally_equal(1, lambda: self.get_mod_state_variable("ignored_plugin_version"))
