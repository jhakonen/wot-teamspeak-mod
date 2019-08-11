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

	def setUp(self):
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

	def test_sanity_check_inputs(self):
		t = self.sanity_check_inputs
		for version in (None, 0.5, "", "1", "1.0", [1, 2, 0]):
			yield t, dict(mod_version=version)
		for version in (None, "", "1", False, [0]):
			yield t, dict(installed_plugin_version=version)
		for versions in (None, 0, "", "1", False, [0], ["1"], {}):
			yield t, dict(ignored_plugin_versions=versions)
		for plugin_info in (None, [], {}, {"versions": None}, {"versions": {}}):
			yield t, dict(plugin_info=plugin_info)
		for plugin_version in (None, 0.1, "", "1", False, []):
			yield t, dict(plugin_info={"versions": [{
				"plugin_version": plugin_version,
				"supported_mod_versions": ["0.6", "0.7"],
				"download_url": "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0"
			}]})
		for mod_versions in (None, [], "", "1", [""], ["1", "2", "3"]):
			yield t, dict(plugin_info={"versions": [{
				"plugin_version": 1,
				"supported_mod_versions": mod_versions,
				"download_url": "https://github.com/jhakonen/wot-teamspeak-plugin/releases/tag/v0.8.0"
			}]})
		yield t, dict(plugin_info={"versions": [{"plugin_version": 1}]})
		yield t, dict(plugin_info={"versions": [{"supported_mod_versions": ["0.6", "0.7"]}]})

	def sanity_check_inputs(self, kwargs):
		self.input = dict(self.input, **kwargs)
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
