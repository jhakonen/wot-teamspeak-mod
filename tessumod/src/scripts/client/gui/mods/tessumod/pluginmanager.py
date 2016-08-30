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

import os
script_dir_path = os.path.dirname(os.path.realpath(__file__))

import sys
sys.path.append(u"scripts/client/gui/mods/tessumod/thirdparty")
from thirdparty.yapsy import log
from thirdparty.yapsy import NormalizePluginNameForModuleName
from thirdparty.yapsy.PluginFileLocator import PluginFileLocator
from thirdparty.yapsy.PluginManager import PluginManager
sys.path.remove(u"scripts/client/gui/mods/tessumod/thirdparty")

import plugintypes
from infrastructure.gameapi import Environment

import os
import imp
import traceback


class ModPluginManager(PluginManager):

	def __init__(self):
		plugins_dir_path = os.path.join(Environment.find_res_mods_version_path(), "scripts/client/gui/mods/tessumod/plugins")
		super(ModPluginManager, self).__init__(
			categories_filter = {
				"Plugin": plugintypes.ModPlugin,
				"PlayerNotifications": plugintypes.PlayerNotificationsMixin,
				"VoiceUserNotifications": plugintypes.VoiceUserNotificationsMixin,
				"Settings": plugintypes.SettingsMixin,
				"UserMatching": plugintypes.UserMatchingMixin
			},
			directories_list = [plugins_dir_path],
			plugin_locator = ModPluginFileLocator()
		)

	def loadPlugins(self, callback=None):
		"""
		Load the candidate plugins that have been identified through a
		previous call to locatePlugins.  For each plugin candidate
		look for its category, load it and store it in the appropriate
		slot of the ``category_mapping``.

		If a callback function is specified, call it before every load
		attempt.  The ``plugin_info`` instance is passed as an argument to
		the callback.
		"""
# 		print "%s.loadPlugins" % self.__class__
		if not hasattr(self, '_candidates'):
			raise ValueError("locatePlugins must be called before loadPlugins")

		processed_plugins = []
		for candidate_infofile, candidate_filepath, plugin_info in self._candidates:
			# make sure to attribute a unique module name to the one
			# that is about to be loaded
			plugin_module_name_template = NormalizePluginNameForModuleName("yapsy_loaded_plugin_" + plugin_info.name) + "_%d"
			for plugin_name_suffix in range(len(sys.modules)):
				plugin_module_name =  plugin_module_name_template % plugin_name_suffix
				if plugin_module_name not in sys.modules:
					break

			# if a callback exists, call it before attempting to load
			# the plugin so that a message can be displayed to the
			# user
			if callback is not None:
				callback(plugin_info)
			try:
				if os.path.isfile(candidate_filepath+".py"):
					with open(candidate_filepath+".py","r") as plugin_file:
						candidate_module = imp.load_module(plugin_module_name,plugin_file,candidate_filepath+".py",("py","r",imp.PY_SOURCE))
				elif os.path.isfile(candidate_filepath+".pyc"):
					with open(candidate_filepath+".pyc","rb") as plugin_file:
						candidate_module = imp.load_module(plugin_module_name,plugin_file,candidate_filepath+".pyc",("pyc","rb",imp.PY_COMPILED))
				else:
					raise RuntimeError("No matching module file found")
			except Exception:
				log.error("Unable to import plugin: %s\n%s" % (candidate_filepath, traceback.format_exc()))
				plugin_info.error = sys.exc_info()
				processed_plugins.append(plugin_info)
				continue
			processed_plugins.append(plugin_info)
			# now try to find and initialise the first subclass of the correct plugin interface
			for element in (getattr(candidate_module,name) for name in dir(candidate_module)):
				plugin_info_reference = None
				for category_name in self.categories_interfaces:
					try:
						is_correct_subclass = issubclass(element, self.categories_interfaces[category_name])
					except Exception:
						continue
					if is_correct_subclass and element is not self.categories_interfaces[category_name]:
							current_category = category_name
							if candidate_infofile not in self._category_file_mapping[current_category]:
								# we found a new plugin: initialise it and search for the next one
								if not plugin_info_reference:
									try:
										plugin_info.plugin_object = self.instanciateElement(element)
										plugin_info_reference = plugin_info
									except Exception:
										log.error("Unable to create plugin object: %s\n%s" % (candidate_filepath, traceback.format_exc()))
										plugin_info.error = sys.exc_info()
										break # If it didn't work once it wont again
								plugin_info.categories.append(current_category)
								self.category_mapping[current_category].append(plugin_info_reference)
								self._category_file_mapping[current_category].append(candidate_infofile)
		# Remove candidates list since we don't need them any more and
		# don't need to take up the space
		delattr(self, '_candidates')
		return processed_plugins

class ModPluginFileLocator(PluginFileLocator):

	def locatePlugins(self):
		"""
		Walk through the plugins' places and look for plugins.

		Return the candidates and number of plugins found.
		"""
# 		print "%s.locatePlugins" % self.__class__
		_candidates = []
		_discovered = {}
		self.recursive = False
		for directory in map(os.path.abspath, self.plugins_places):
			# first of all, is it a directory :)
			if not os.path.isdir(directory):
				log.debug("%s skips %s (not a directory)" % (self.__class__.__name__, directory))
				continue
			if self.recursive:
				debug_txt_mode = "recursively"
				walk_iter = os.walk(directory, followlinks=True)
			else:
				debug_txt_mode = "non-recursively"
				walk_iter = [(directory,[],os.listdir(directory))]
			# iteratively walks through the directory
			log.debug("%s walks (%s) into directory: %s" % (self.__class__.__name__, debug_txt_mode, directory))
			for item in walk_iter:
				dirpath = item[0]
				for filename in item[2]:
					#print "testing candidate file %s" % filename
					for analyzer in self._analyzers:
						# print("... with analyzer %s" % analyzer.name)
						# eliminate the obvious non plugin files
						if not analyzer.isValidPlugin(filename):
							log.debug("%s is not a valid plugin for strategy %s" % (filename, analyzer.name))
							continue
						candidate_infofile = os.path.join(dirpath, filename)
						if candidate_infofile in _discovered:
							log.debug("%s (with strategy %s) rejected because already discovered" % (candidate_infofile, analyzer.name))
							continue
						log.debug("%s found a candidate:\n    %s" % (self.__class__.__name__, candidate_infofile))
#						print candidate_infofile
						plugin_info = self._getInfoForPluginFromAnalyzer(analyzer, dirpath, filename)
						if plugin_info is None:
							log.debug("Plugin candidate '%s'  rejected by strategy '%s'" % (candidate_infofile, analyzer.name))
							break # we consider this was the good strategy to use for: it failed -> not a plugin -> don't try another strategy
						# now determine the path of the file to execute,
						# depending on wether the path indicated is a
						# directory or a file
#					print plugin_info.path
						# Remember all the files belonging to a discovered
						# plugin, so that strategies (if several in use) won't
						# collide
						if any(os.path.isfile(plugin_info.path + "." + ext) for ext in ("py", "pyc")):
							candidate_filepath = plugin_info.path
							# it is a file, adds it
							self._discovered_plugins[plugin_info.path] = candidate_filepath
						else:
							log.error("Plugin candidate rejected: cannot find the file module for '%s'" % (candidate_infofile))
							break
#					print candidate_filepath
						_candidates.append((candidate_infofile, candidate_filepath, plugin_info))
						# finally the candidate_infofile must not be discovered again
						_discovered[candidate_infofile] = candidate_filepath
						self._discovered_plugins[candidate_infofile] = candidate_filepath
#						print "%s found by strategy %s" % (candidate_filepath, analyzer.name)
		return _candidates, len(_candidates)
