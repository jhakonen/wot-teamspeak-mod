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

import logutils

import importlib

logger = logutils.logger.getChild("pluginmanager")

class PluginManager(object):

	def __init__(self, plugins_list, import_path, category_classes):
		self.__plugins_list = plugins_list
		self.__import_path = import_path
		self.__categories_filter = self.get_categories(category_classes)
		self.__plugin_infos_by_category = {name: [] for name in self.__categories_filter.iterkeys()}
		self.__plugin_infos_all = []

	def get_categories(self, category_classes):
		"""
		Collects all classes in 'category_classes' which has CATEGORY class member.
		Returns categories as map of CATEGORY as key and the class as value.
		"""
		categories = {}
		for cls in category_classes:
			if hasattr(cls, "CATEGORY"):
				categories[getattr(cls, "CATEGORY")] = cls
		return categories

	def collectPlugins(self):
		for plugin_name in self.__plugins_list:
			try:
				plugin_module = importlib.import_module(self.__import_path + "." + plugin_name)
			except ImportError:
				logger.error("No such plugin: %s" % plugin_name)
				continue
			if not hasattr(plugin_module, "build_plugin"):
				logger.error("Plugin does not implement build_plugin(): %s" % plugin_name)
				continue
			plugin_info = PluginInfo(plugin_module.build_plugin(), plugin_name)
			self.__plugin_infos_all.append(plugin_info)
			for category_name, category_cls in self.__categories_filter.iteritems():
				if issubclass(plugin_info.plugin_cls, category_cls):
					self.__plugin_infos_by_category[category_name].append(plugin_info)
			logger.info("Plugin loaded: %s" % plugin_name)

	def getAllPlugins(self):
		return list(self.__plugin_infos_all)

	def getPluginsOfCategory(self, name):
		return list(self.__plugin_infos_by_category[name])

class PluginInfo(object):
	def __init__(self, plugin_object, name):
		self.name = name
		self.plugin_object = plugin_object
		self.plugin_cls = plugin_object.__class__
		self.__initialized = False

	def initialize(self):
		self.plugin_object.initialize()
		self.__initialized = True

	def deinitialize(self):
		# Do not deinitialize if initialize() was not called or had raised an error
		if self.__initialized:
			self.plugin_object.deinitialize()
