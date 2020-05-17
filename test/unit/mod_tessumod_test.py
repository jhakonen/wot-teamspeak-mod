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
import pytest

import mod_tessumod

class TestPluginAdvertisement:

	@pytest.fixture(autouse=True)
	def setup(self):
		self.input = dict(
			plugin_info = {
				"versions": [
					{
						"plugin_version": 1,
						"supported_mod_versions": ["0.6", "0.7"],
						"download_url": "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0"
					},
					{
						"plugin_version": 2,
						"supported_mod_versions": ["0.7"],
						"download_url": "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed"
					}
				]
			},
			mod_version = "0.6.14",
			installed_plugin_version = 0,
			ignored_plugin_versions = []
		)

	plugin_version_dict = {
		"plugin_version": 1,
		"supported_mod_versions": ["0.6", "0.7"],
		"download_url": "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0"
	}

	insane_inputs = [
		dict(mod_version=None),
		dict(mod_version=0.5),
		dict(mod_version=""),
		dict(mod_version="1"),
		dict(mod_version="1.0"),
		dict(mod_version=[1, 2, 0]),

		dict(installed_plugin_version=None),
		dict(installed_plugin_version=""),
		dict(installed_plugin_version="1"),
		dict(installed_plugin_version=False),
		dict(installed_plugin_version=[0]),

		dict(ignored_plugin_versions=None),
		dict(ignored_plugin_versions=0),
		dict(ignored_plugin_versions=""),
		dict(ignored_plugin_versions="1"),
		dict(ignored_plugin_versions=False),
		dict(ignored_plugin_versions=[0]),
		dict(ignored_plugin_versions=["1"]),
		dict(ignored_plugin_versions={}),

		dict(plugin_info=None),
		dict(plugin_info=[]),
		dict(plugin_info={}),
		dict(plugin_info={"versions": None}),
		dict(plugin_info={"versions": {}}),

		dict(plugin_info={"versions": [{"plugin_version": 1}]}),
		dict(plugin_info={"versions": [{"supported_mod_versions": ["0.6", "0.7"]}]}),

		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version=None)]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version=0.1)]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version="")]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version="1")]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version=False)]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, plugin_version=[])]}),

		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions=None)]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions=[])]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions="")]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions="1")]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions=[""])]}),
		dict(plugin_info={"versions": [dict(plugin_version_dict, supported_mod_versions=["1", "2", "3"])]}),
	]

	@pytest.mark.parametrize("input", insane_inputs)
	def test_sanity_check_inputs(self, input):
		self.input = dict(self.input, **input)
		assert_raises(Exception, mod_tessumod.get_plugin_advertisement_info, self.input)

	def test_returns_none_with_too_old_mod_version_and_no_plugin_installed(self):
		self.input["mod_version"] = "0.5.5"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_returns_none_with_newest_plugin_installed(self):
		self.input["installed_plugin_version"] = 1
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_offers_plugin_install(self):
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")
		assert_equal(output["download_url"], "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0")
		assert_equal(output["plugin_version"], 1)

	def test_offers_update_with_old_plugin_installed(self):
		self.input["mod_version"] = "0.7.1"
		self.input["installed_plugin_version"] = 1
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "update")
		assert_equal(output["download_url"], "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed")
		assert_equal(output["plugin_version"], 2)

	def test_offers_update_with_unsupported_old_plugin_installed(self):
		self.input["mod_version"] = "0.8.0"
		self.input["installed_plugin_version"] = 1
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "update")
		assert_equal(output["download_url"], "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed")
		assert_equal(output["plugin_version"], 2)

	def test_warns_of_unsupported_mod_version(self):
		self.input["mod_version"] = "0.5.5"
		self.input["installed_plugin_version"] = 2
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "unsupported_mod")

	def test_returns_none_with_ignored_plugin_install(self):
		self.input["ignored_plugin_versions"].append(1)
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_returns_none_with_ignored_plugin_update(self):
		self.input["mod_version"] = "0.7.1"
		self.input["installed_plugin_version"] = 1
		self.input["ignored_plugin_versions"].append(2)
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_warns_of_unsupported_plugin_version_with_ad_ignored(self):
		self.input["mod_version"] = "0.8.0"
		self.input["installed_plugin_version"] = 1
		self.input["ignored_plugin_versions"].append(2)
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "unsupported_plugin")

	def test_offers_plugin_install_for_release_candidate(self):
		self.input["mod_version"] = "0.7.0rc1"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")
		assert_equal(output["download_url"], "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed")
		assert_equal(output["plugin_version"], 2)

	def test_offers_install_with_new_and_unspecified_mod_version(self):
		self.input["mod_version"] = "0.8.0"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")
		assert_equal(output["download_url"], "https://www.myteamspeak.com/addons/01a0f828-894c-45b7-a852-937b47ceb1ed")
		assert_equal(output["plugin_version"], 2)

	def test_returns_none_with_too_new_mod_version(self):
		self.input["mod_version"] = "0.9.0"
		self.input["plugin_info"]["versions"][1]["supported_mod_versions"] = ["0.7", "0.8"]
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_returns_none_with_plugin_install_missing_url(self):
		del self.input["plugin_info"]["versions"][0]["download_url"]
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_is_none(output)

	def test_offers_install_with_newest_plugin_install_missing_url(self):
		self.input["mod_version"] = "0.7.1"
		del self.input["plugin_info"]["versions"][1]["download_url"]
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")
		assert_equal(output["download_url"], "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0")
		assert_equal(output["plugin_version"], 1)

	def test_offers_plugin_install_with_not_tagged_version(self):
		self.input["mod_version"] = self.input["mod_version"] + ".post18+gccf7b38.d20200517"
		output = mod_tessumod.get_plugin_advertisement_info(self.input)
		assert_equal(output["offer_type"], "install")
		assert_equal(output["download_url"], "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0")
		assert_equal(output["plugin_version"], 1)
