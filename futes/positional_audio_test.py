from helpers.testcasebase import TestCaseBase
from helpers.utils import *
import mock
import nosepipe
import mmap
import struct

@nosepipe.isolate
class PositionalAudioTest(TestCaseBase):
	'''
	This fute test tests that positional audio data is passed to TS plugin.
	To execute, use command:
		$ nosetests --with-process-isolation
	'''

	def setUp(self):
		TestCaseBase.setUp(self)

	@use_event_loop
	def test_camera_position_is_written_to_shared_memory(self):
		self.start_ts_client(connected_to_server=True)
		self.enable_ts_client_tessumod_plugin()
		self.start_game(mode="battle", camera={"position": (100, 200, 50)})
		self.assert_finally_equal((100, 200, 50), lambda: self.get_shared_memory_contents("TessuModTSPlugin3dAudio")["camera"]["position"])

	@use_event_loop
	def test_camera_direction_is_written_to_shared_memory(self):
		self.start_ts_client(connected_to_server=True)
		self.enable_ts_client_tessumod_plugin()
		self.start_game(mode="battle", camera={"direction": (10, 20, 30)})
		self.assert_finally_equal((10, 20, 30), lambda: self.get_shared_memory_contents("TessuModTSPlugin3dAudio")["camera"]["direction"])

	@use_event_loop
	def test_positions_are_written_to_shared_memory(self):
		self.start_ts_client(connected_to_server=True, users={
			"TuhoajaErkki": {},
			"KaapuKalle": {}
		})
		self.enable_ts_client_tessumod_plugin()
		self.start_game(mode="battle", players=[
			dict(name="TuhoajaErkki", position=(100, 100, 10)),
			dict(name="KaapuKalle", position=(150, 150, 20))
		])
		self.on_event("on_connected_to_ts_server", lambda: self.change_ts_client_state(users={
			"TuhoajaErkki": {"speaking": True},
			"KaapuKalle": {"speaking": True}
		}))
		self.assert_finally_equal((100, 100, 10), lambda: self.get_shared_memory_contents("TessuModTSPlugin3dAudio")["clients"]["TuhoajaErkki"]["position"])
		self.assert_finally_equal((150, 150, 20), lambda: self.get_shared_memory_contents("TessuModTSPlugin3dAudio")["clients"]["KaapuKalle"]["position"])
