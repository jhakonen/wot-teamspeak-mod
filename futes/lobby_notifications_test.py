from helpers.testcasebase import TestCaseBase
from helpers.utils import *
import mock
import nosepipe

@nosepipe.isolate
class LobbyNotifications(TestCaseBase):
	'''
	This fute test tests that notifications are shown in lobby.
	To execute, use command:
		$ nosetests --with-process-isolation
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		import gui.SystemMessages
		gui.SystemMessages.pushMessage = mock.Mock()
		self.__seen_events = set()

	def __set_seen_event(self, event):
		self.__seen_events.add(event)

	def __is_event_seen(self, event):
		return event in self.__seen_events

	def __is_system_notification_sent(self, message, type):
		import gui.SystemMessages
		if type == "info":
			sm_type = gui.SystemMessages.SM_TYPE.Information
		if type == "warning":
			sm_type = gui.SystemMessages.SM_TYPE.Warning
		if type == "error":
			sm_type = gui.SystemMessages.SM_TYPE.Error
		return mock_was_called_with(gui.SystemMessages.pushMessage, message, sm_type)

	def test_notification_connected_to_teamspeak_server_is_shown(self):
		self.start_ts_client(connected_to_server=True)
		self.start_game(mode="lobby")
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info")
		])

	def test_notification_connected_to_teamspeak_server_is_not_shown(self):
		self.start_ts_client(connected_to_server=False)
		self.start_game(mode="lobby")
		self.run_in_event_loop(min_wait=5, verifiers=[
			lambda: not self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info")
		])

	def test_notification_disconnected_from_teamspeak_client_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby", on_events={
			"on_connected_to_ts_client": [
				lambda: self.change_ts_client_state(running=False)
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning")
		])

	def test_notifications_not_shown_in_battle(self):
		self.start_ts_client()
		self.start_game(mode="battle", on_events={
			"on_connected_to_ts_client": [
				lambda: self.change_ts_client_state(running=False)
			],
			"on_disconnected_from_ts_client": [
				lambda: self.__set_seen_event("on_disconnected_from_ts_client")
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_event_seen("on_disconnected_from_ts_client"),
			lambda: not self.__is_system_notification_sent(message=contains_match("Connected to TeamSpeak server"), type="info"),
			lambda: not self.__is_system_notification_sent(message="Disconnected from TeamSpeak client", type="warning")
		])

	def test_notification_user_cache_error_is_shown(self):
		self.change_mod_user_cache(
			# undefined TS user and player paired together
			UserPlayerPairings = {
				"Erkki Meikalainen": "TuhoajaErkki"
			}
		)
		self.start_game(mode="lobby")
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_system_notification_sent(message=contains_match("Failed to read file"), type="error")
		])
