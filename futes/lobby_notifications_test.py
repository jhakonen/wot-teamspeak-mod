from helpers.testcasebase import TestCaseBase
from helpers.utils import *
import mock

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
		import gui.SystemMessages
		print gui.SystemMessages.pushMessage.call_args_list
		return event in self.__seen_events

	def test_notification_connected_to_teamspeak_server_is_shown(self):
		import gui.SystemMessages
		self.change_ts_client_state(connected_to_server=True)
		self.load_mod()
		self.change_game_state(mode="lobby")
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(gui.SystemMessages.pushMessage, "Connected to TeamSpeak server 'Dummy Server'", gui.SystemMessages.SM_TYPE.Information)
		])

	def test_notification_connected_to_teamspeak_server_is_not_shown(self):
		import gui.SystemMessages
		self.change_ts_client_state(connected_to_server=False)
		self.load_mod()
		self.change_game_state(mode="lobby")
		self.run_in_event_loop(min_wait=5, verifiers=[
			lambda: not mock_was_called_with(gui.SystemMessages.pushMessage, "Connected to TeamSpeak server 'Dummy Server'", gui.SystemMessages.SM_TYPE.Information)
		])

	def test_notification_disconnected_from_teamspeak_client_is_shown(self):
		import gui.SystemMessages
		self.change_ts_client_state(connected_to_server=True)
		self.load_mod(events={
			"on_connected_to_ts_client": [
				lambda: self.change_ts_client_state(running=False)
			]
		})
		self.change_game_state(mode="lobby")
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(gui.SystemMessages.pushMessage, "Disconnected from TeamSpeak client", gui.SystemMessages.SM_TYPE.Warning)
		])

	def test_notifications_not_shown_in_battle(self):
		import gui.SystemMessages
		self.change_ts_client_state(connected_to_server=True)
		self.load_mod(events={
			"on_connected_to_ts_server": [
				lambda: self.change_ts_client_state(running=False)
			],
			"on_disconnected_from_ts_client": [
				lambda: self.__set_seen_event("on_disconnected_from_ts_client")
			]
		})
		self.change_game_state(mode="battle")
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_event_seen("on_disconnected_from_ts_client"),
			lambda: not mock_was_called_with(gui.SystemMessages.pushMessage, "Connected to TeamSpeak server 'Dummy Server'", gui.SystemMessages.SM_TYPE.Information),
			lambda: not mock_was_called_with(gui.SystemMessages.pushMessage, "Disconnected from TeamSpeak client", gui.SystemMessages.SM_TYPE.Warning)
		])
