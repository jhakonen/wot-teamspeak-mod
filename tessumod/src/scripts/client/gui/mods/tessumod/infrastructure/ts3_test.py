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

import os
import sys
import ConfigParser
base_path  = os.path.dirname(os.path.realpath(__file__))
fakes_path = os.path.realpath(os.path.join(base_path, "..", "..", "..", "..", "..", "..", "..", "..", "futes", "fakes"))
sys.path.append(fakes_path)

import ts3

class TestTS3(object):

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
