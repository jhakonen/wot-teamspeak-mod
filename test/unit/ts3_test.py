# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from nose.tools import assert_equal
from tessumod import ts3

class TestCQParameterParsing(object):

	def test_can_parse_arg(self):
		assert 3 == int(ts3.parse_client_query_parameters("clid=3")[0]["clid"])

	def test_can_parse_two_args(self):
		[params] = ts3.parse_client_query_parameters("clid=3 cid=173")
		assert 3 == int(params["clid"])
		assert 173 == int(params["cid"])

	def test_can_parse_two_args(self):
		[params] = ts3.parse_client_query_parameters("clid=3 cid=173")
		assert 3 == int(params["clid"])
		assert 173 == int(params["cid"])

	def test_can_parse_empty_arg1(self):
		[params] = ts3.parse_client_query_parameters("clid=24 client_meta_data")
		assert 24 == int(params["clid"])
		assert "" == params["client_meta_data"]

	def test_can_parse_empty_arg2(self):
		[params] = ts3.parse_client_query_parameters("client_meta_data clid=24")
		assert 24 == int(params["clid"])
		assert "" == params["client_meta_data"]

	def test_can_parse_escaped_value(self):
		[params] = ts3.parse_client_query_parameters(r"clid=24 client_meta_data=Weird\sName:\s\\\/\p\a\b\f\n\r\t\v")
		assert 24 == int(params["clid"])
		assert "Weird Name: \\/|\a\b\f\n\r\t\v" == params["client_meta_data"]

	def test_can_parse_multiple_entries(self):
		[p1, p2, p3] = ts3.parse_client_query_parameters("clid=3|clid=1|clid=2")
		assert 3 == int(p1["clid"])
		assert 1 == int(p2["clid"])
		assert 2 == int(p3["clid"])

class TestCommandStringBuilding(object):

	def test_builds_command_without_args(self):
		cmd_str = ts3.build_command_string("whoami", [], {})
		assert_equal(cmd_str, "whoami")

	def test_builds_command_with_arg(self):
		cmd_str = ts3.build_command_string("clientlist", ["-uid"], {})
		assert_equal(cmd_str, "clientlist -uid")

	def test_builds_command_with_two_arg(self):
		cmd_str = ts3.build_command_string("clientlist", ["-uid", "-voice"], {})
		assert_equal(cmd_str, "clientlist -uid -voice")

	def test_builds_command_with_int_keyword_arg(self):
		cmd_str = ts3.build_command_string("use", [], {"schandlerid": 0})
		assert_equal(cmd_str, "use schandlerid=0")

	def test_builds_command_with_escaped_keyword_arg(self):
		cmd_str = ts3.build_command_string("clientupdate", [], {"client_meta_data": "Weird Name: \\/|\a\b\f\n\r\t\v"})
		assert_equal(cmd_str, r"clientupdate client_meta_data=Weird\sName:\s\\\/\p\a\b\f\n\r\t\v")

	def test_can_set_nickname_with_acre2_data_included(self):
		client_meta_data = "Version: 2.5.1.982\nArma Connected: No<wot_nickname_start>Testinukke<wot_nickname_end>"
		cmd_str = ts3.build_command_string("clientupdate", [], {"client_meta_data": client_meta_data})
		[params] = ts3.parse_client_query_parameters(cmd_str.split(" ", 1)[1])
		assert_equal(params["client_meta_data"], client_meta_data)
