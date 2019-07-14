# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2019  Janne Hakonen
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

from nose.tools import *
import mod_tessumod

class TestPluginAdvertisement(object):

	# TODO: sanity check plugin_info contents
	# TODO: check for changelog
	# TODO: newest plugin version shouldn't have max mod version defined

	def setUp(self):
		# The default configuration should offer user to install the plugin
		self.input = dict(
			plugin_info = {
				"plugin_version": 2,
				"supported_mod_versions": ["0.6", "0.8"]
			},
			mod_version = "0.6.14",
			windows_version = 6,
			installed_plugin_version = 0,
			ignored_plugin_versions = []
		)

	def test_offers_plugin_install(self):
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")

	def test_offers_update_with_old_plugin_installed(self):
		self.input["installed_plugin_version"] = 1
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "update")

	def test_returns_none_with_old_windows_os(self):
		for version in range(0, 5):
			yield self.check_returns_none_with_old_windows_os, version

	def check_returns_none_with_old_windows_os(self, version):
		self.input["windows_version"] = version
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_returns_none_with_newest_plugin_installed(self):
		self.input["installed_plugin_version"] = 2
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_warns_of_unsupported_mod_version(self):
		self.input["mod_version"] = "0.5.5"
		self.input["installed_plugin_version"] = 2
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "unsupported_mod")

	def test_returns_none_with_too_old_mod_version(self):
		self.input["mod_version"] = "0.5.5"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_returns_none_with_too_new_mod_version(self):
		self.input["mod_version"] = "0.9.0"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)
