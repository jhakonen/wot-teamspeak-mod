from helpers.testcasebase import TestCaseBase
from helpers.utils import *
import mock

class TSPluginAdvertisement(TestCaseBase):
	'''
	This fute test tests TessuMod Plugin is advertised in lobby.
	To execute, use command:
		$ nosetests --with-process-isolation
	'''

	def setUp(self):
		TestCaseBase.setUp(self)
		import notification
		self.mock_addNotification = notification.NotificationMVC.g_instance.getModel().addNotification = mock.Mock()

	def __is_notification_added(self, fragments):
		return mock_was_called_with(self.mock_addNotification, message_decorator_matches_fragments(fragments))

	def test_ts_plugin_advertisement_is_shown(self):
		self.start_ts_client()
		self.start_game(mode="lobby")
		self.run_in_event_loop(verifiers=[
			lambda: self.__is_notification_added(["TessuModTSPluginInstall", "TessuModTSPluginMoreInfo", "TessuModTSPluginIgnore"])
		])
