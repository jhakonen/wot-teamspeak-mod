# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2016  Janne Hakonen
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

from infrastructure.gameapi import Environment
import logutils
import plugintypes

import os
import json
import imp
import inspect

logger = logutils.logger.getChild("pluginmanager")

class ModPluginManager(object):

	def __init__(self, plugin_base_class):
		self.__plugin_base_class = plugin_base_class
		self.__mods_dirpath = os.path.join(Environment.find_res_mods_version_path(), "scripts/client/gui/mods")
		with open(os.path.join(self.__mods_dirpath, "tessumod/config.json"), "rb") as file:
			self.__plugins_list = json.loads(file.read())["plugins"]

		self.__plugins_dir_path = os.path.join(self.__mods_dirpath, "tessumod/plugins")
		self.__categories_filter = self.get_categories(plugintypes)
		self.__plugin_infos_by_category = {name: [] for name in self.__categories_filter.iterkeys()}
		self.__plugin_infos_all = []

	def get_categories(self, module):
		"""
		Collects all classes in 'module' which has CATEGORY class member.
		Returns categories as map of CATEGORY as key and the class as value.
		"""
		categories = {}
		for name in dir(plugintypes):
			attribute = getattr(plugintypes, name)
			if inspect.isclass(attribute) and hasattr(attribute, "CATEGORY"):
				categories[getattr(attribute, "CATEGORY")] = attribute
		return categories

	def collectPlugins(self):
		for plugin_name in self.__plugins_list:
			plugin_path = os.path.join(self.__plugins_dir_path, plugin_name)
			plugin_module = None
			plugin_info = None
			for imp_type in [imp.PY_SOURCE, imp.PY_COMPILED]:
				ext = "py" if imp_type == imp.PY_SOURCE else "pyc"
				full_plugin_path = plugin_path + "." + ext
				if os.path.isfile(full_plugin_path):
					with open(full_plugin_path, "rb") as file:
						plugin_module = imp.load_module("plugin_" + plugin_name, file, full_plugin_path, (ext, "rb", imp_type))
			if not plugin_module:
				logger.error("No such plugin '{}'".format(plugin_name))
				continue
			elements = [getattr(plugin_module, element_name) for element_name in dir(plugin_module)]
			for element in elements:
				is_plugin = False
				try:
					is_plugin = issubclass(element, self.__plugin_base_class)
				except Exception:
					pass
				if is_plugin:
					plugin_info = PluginInfo(element, plugin_name)
					break
			if not plugin_info:
				logger.error("Plugin '{}' has no valid plugin classes".format(plugin_name))
				continue
			self.__plugin_infos_all.append(plugin_info)
			for category_name, category_cls in self.__categories_filter.iteritems():
				if issubclass(plugin_info.plugin_cls, category_cls):
					self.__plugin_infos_by_category[category_name].append(plugin_info)
			logger.info("Plugin '{}' loaded".format(plugin_name))

	def getAllPlugins(self):
		return list(self.__plugin_infos_all)

	def activatePluginByName(self, name):
		pass # DONE

	def getPluginsOfCategory(self, name):
		return list(self.__plugin_infos_by_category[name])

class PluginInfo(object):
	def __init__(self, plugin_cls, name):
		self.plugin_cls = plugin_cls
		self.name = name
		self.plugin_object = plugin_cls()
