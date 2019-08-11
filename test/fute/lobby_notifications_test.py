from unittest import mock

from nose.plugins.attrib import attr

from .test_helpers.testcasebase import TestCaseBase
from .test_helpers.utils import *

class LobbyNotifications(TestCaseBase):
	'''
	This fute test tests that notifications are shown in lobby.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		from helpers import dependency
		from skeletons.gui.system_messages import ISystemMessages
		self.__system_messages = dependency.instance(ISystemMessages)
		self.__system_messages.pushMessage = mock.Mock()
		self.disconnected_from_ts_client = False
		self.on_event("on_disconnected_from_ts_client", lambda: setattr(self, "disconnected_from_ts_client", True))

	def __is_system_notification_sent(self, message, type):
		import gui.SystemMessages
		if type == "info":
			sm_type = gui.SystemMessages.SM_TYPE.Information
		if type == "warning":
			sm_type = gui.SystemMessages.SM_TYPE.Warning
		if type == "error":
			sm_type = gui.SystemMessages.SM_TYPE.Error
		return mock_was_called_with(self.__system_messages.pushMessage, message, sm_type)

	@use_event_loop
	def test_notification_connected_to_teamspeak_server_is_shown(self):
		self.start_ts_client(connected_to_server=True)
		self.start_game(mode="lobby")
		self.assert_finally_true(lambda: self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info"))

	@attr("slow")
	@use_event_loop
	def test_notification_connected_to_teamspeak_server_is_not_shown(self):
		# TODO: Slow test, replace with a unit test
		self.start_ts_client(connected_to_server=False)
		self.start_game(mode="lobby")
		self.assert_finally_false(lambda: self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info"))
		self.wait_at_least(secs=5)

	@use_event_loop
	def test_notification_disconnected_from_teamspeak_client_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.on_event("on_connected_to_ts_client", lambda: self.change_ts_client_state(running=False))
		self.assert_finally_true(lambda: self.__is_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning"))

	@use_event_loop
	def test_notifications_not_shown_in_battle(self):
		self.start_ts_client()
		self.start_game(mode="battle")
		self.on_event("on_connected_to_ts_client", lambda: self.change_ts_client_state(running=False))
		self.assert_finally_true(lambda: self.disconnected_from_ts_client)
		self.assert_finally_false(lambda: self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info"))
		self.assert_finally_false(lambda: self.__is_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning"))

	@use_event_loop
	def test_notification_user_cache_error_is_shown(self):
		self.change_mod_user_cache(
			# undefined TS user and player paired together
			UserPlayerPairings = {
				"Erkki Meikalainen": "TuhoajaErkki"
			}
		)
		self.start_game(mode="lobby")
		self.assert_finally_true(lambda: self.__is_system_notification_sent(message=contains_match("Failed to read file"), type="error"))
