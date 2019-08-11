from Avatar import Avatar

from .test_helpers.testcasebase import TestCaseBase
from .test_helpers.utils import *

class TSMetadataUpdates(TestCaseBase):
	'''
	This fute test tests that player's metadata is updated and contains player's nickname in it.
	'''

	def setUp(self):
		TestCaseBase.setUp(self)

	def get_client_user(self):
		return self.ts_client_query_server.get_user(name="Testinukke")

	def test_nickname_is_updated_to_metadata(self):
		Avatar.name = "TuhoajaErkki"
		self.start_ts_client(connected_to_server=True)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_until_equal(
			lambda: self.get_client_user().metadata,
			"<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"
		)

	def test_nickname_is_reapplied_to_metadata_if_it_is_overwritten(self):
		Avatar.name = "TuhoajaErkki"
		self.start_ts_client(connected_to_server=True)
		self.start_game(mode="battle", players=[{"name": "TuhoajaErkki"}])
		self.wait_until_equal(
			lambda: self.get_client_user().metadata,
			"<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"
		)
		self.get_client_user().metadata = "Version: 2.5.1.982\nArma Connected: No"
		self.wait_until_equal(
			lambda: self.get_client_user().metadata,
			"Version: 2.5.1.982\nArma Connected: No<wot_nickname_start>TuhoajaErkki<wot_nickname_end>"
		)
