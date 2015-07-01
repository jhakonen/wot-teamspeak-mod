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

	def test_notification_connected_to_teamspeak_server_is_shown(self):
		import gui.SystemMessages
		self.change_game_state(mode="lobby")
		self.change_ts_client_state(connected_to_server=True)
		self.load_mod()
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(gui.SystemMessages.pushMessage, "Connected to TeamSpeak server 'Dummy Server'", gui.SystemMessages.SM_TYPE.Information)
		])

	def test_notification_connected_to_teamspeak_server_is_not_shown(self):
		import gui.SystemMessages
		self.change_game_state(mode="lobby")
		self.change_ts_client_state(connected_to_server=False)
		self.load_mod()
		self.run_in_event_loop(min_wait=5, verifiers=[
			lambda: not mock_was_called_with(gui.SystemMessages.pushMessage, "Connected to TeamSpeak server 'Dummy Server'", gui.SystemMessages.SM_TYPE.Information)
		])

	def test_notification_disconnected_from_teamspeak_client_is_shown(self):
		import gui.SystemMessages
		self.change_game_state(mode="lobby")
		self.change_ts_client_state(connected_to_server=True)
		self.load_mod(events={
			"on_connected_to_ts_client": [
				lambda: self.change_ts_client_state(running=False)
			]
		})
		self.run_in_event_loop(verifiers=[
			lambda: mock_was_called_with(gui.SystemMessages.pushMessage, "Disconnected from TeamSpeak client", gui.SystemMessages.SM_TYPE.Warning)
		])
