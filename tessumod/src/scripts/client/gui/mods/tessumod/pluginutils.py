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

import models

def get_player_model(plugin_manager, names):
	models_list = []
	for plugin_info in plugin_manager.getPluginsOfCategory("PlayerModelProvider"):
		plugin = plugin_info.plugin_object
		for name in names:
			if plugin.has_player_model(name):
				models_list.append(plugin.get_player_model(name))
	if len(models_list) > 1:
		return models.CompositeModel(player_combiner, models_list)
	elif len(models_list) == 1:
		return models_list[0]
	else:
		raise KeyError("Unable to return player model with name(s): {0}".format(names))

def player_combiner(player_1, player_2):
	new_player = player_1.copy()
	new_player.update(player_2)
	return new_player

def get_user_model(plugin_manager, names):
	models_list = []
	for plugin_info in plugin_manager.getPluginsOfCategory("UserModelProvider"):
		plugin = plugin_info.plugin_object
		for name in names:
			if plugin.has_user_model(name):
				models_list.append(plugin.get_user_model(name))
	if len(models_list) > 1:
		return models.CompositeModel(user_combiner, models_list)
	elif len(models_list) == 1:
		return models_list[0]
	else:
		raise KeyError("Unable to return user model with name(s): {0}".format(names))

def user_combiner(user_1, user_2):
	new_user = user_1.copy()
	new_user["client_ids"] |= user_2["client_ids"]
	new_user["names"] |= user_2["names"]
	new_user["game_names"] |= user_2["game_names"]
	new_user["is_speaking"] |= user_2["is_speaking"]
	new_user["is_me"] |= user_2["is_me"]
	return new_user
