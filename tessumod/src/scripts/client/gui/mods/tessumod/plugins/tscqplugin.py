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

from gui.mods.tessumod import plugintypes, logutils
from gui.mods.tessumod.models import g_player_model, g_user_model, UserItem, FilterModel
from gui.mods.tessumod.infrastructure import clientquery
from gui.mods.tessumod.thirdparty.promise import Promise
import re
import collections
import itertools

logger = logutils.logger.getChild("tscqplugin")
UserTuple = collections.namedtuple('UserTuple', ('client_id', 'name', 'game_name', 'id', 'is_speaking', 'is_me', 'my_channel'))

class TSCQPlugin(plugintypes.ModPlugin, plugintypes.SettingsProvider):
	"""
	This plugin ...
	"""

	NS = "voice"

	def __init__(self):
		super(TSCQPlugin, self).__init__()
		self.__host = None
		self.__port = None
		self.__ts = TeamSpeakClient()
		self.__ts.on("authenticated", self.__on_authenticated_to_ts)
		self.__ts.on("authentication-required", self.__on_authentication_required)
		self.__ts.on("disconnected", self.__on_disconnected_from_ts)
		self.__ts.on("connected-server", self.__on_connected_to_ts_server)
		self.__ts.on("disconnected-server", self.__on_disconnected_from_ts_server)
		self.__ts.on("server-tab-changed", self.__on_server_tab_changed)
		self.__ts.on("user-added", self.__on_user_added)
		self.__ts.on("user-changed-client-nickname", self.__on_user_name_changed)
		self.__ts.on("user-changed-game-nickname", self.__on_user_game_name_changed)
		self.__ts.on("user-changed-talking", self.__on_user_speaking_changed)
		self.__ts.on("user-changed-my-channel", self.__on_user_my_channel_changed)
		self.__ts.on("user-removed", self.__on_user_removed)
		self.__users = {}
		g_user_model.add_namespace(self.NS)
		player_model = FilterModel(g_player_model)
		player_model.add_filter(lambda player: player.has_attribute("name"))
		player_model.add_filter(lambda player: player.is_me)
		player_model.on("added", self.__on_me_player_added)
		self.__server_names = {}

	@logutils.trace_call(logger)
	def initialize(self):
		self.__connect()

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsProvider.
		"""
		if section == "TSClientQueryService":
			if name == "api_key":
				self.__ts.api_key = value
			elif name == "host":
				self.__host = value
				self.__connect()
			elif name == "port":
				self.__port = value
				self.__connect()
			elif name == "polling_interval":
				self.__ts.start_event_checking(value)

	@logutils.trace_call(logger)
	def get_settings_content(self):
		"""
		Implemented from SettingsProvider.
		"""
		return {
			"TSClientQueryService": {
				"help": "",
				"variables": [
					{
						"name": "api_key",
						"default": "",
						"help": "Clientquery plugin's API key"
					},
					{
						"name": "host",
						"default": "localhost",
						"help": "Host of the TeamSpeak clientquery plugin"
					},
					{
						"name": "port",
						"default": 25639,
						"help": "Port of the TeamSpeak clientquery plugin"
					},
					{
						"name": "polling_interval",
						"default": 0.1,
						"help": """
							Interval (as seconds) to poll clientquery's socket
							 - high value causes reaction delay to speak notifications
							 - low value may have negative impact to game performance
							Changing this value requires game restart
						"""
					}
				]
			}
		}

	@logutils.trace_call(logger)
	def __connect(self):
		if self.__host and self.__port:
			self.__ts.connect(self.__host, self.__port)

	@logutils.trace_call(logger)
	def __on_authenticated_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client and the connection is
		authenticated. However, this doesn't mean that the client is connected to any TeamSpeak
		server yet.
		'''
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_voice_client_connected()
		for plugin_info in self.plugin_manager.getPluginsOfCategory("Notifications"):
			plugin_info.plugin_object.show_notification({
				"type": "info",
				"message": [ "Connected to TeamSpeak client" ]
			})

	@logutils.trace_call(logger)
	def __on_authentication_required(self):
		'''Called when ClientQuery's API key is not set or is wrong.
		Asks user to provide the key.'''
		# TODO: Ask API key from user, some kind of UI dialog is needed
		# TODO: Modify TSClientQueryService.api_key option in settings
		logger.error("Not Implemented: Query API key from user")

	@logutils.trace_call(logger)
	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		for plugin_info in self.plugin_manager.getPluginsOfCategory("Notifications"):
			plugin_info.plugin_object.show_notification({
				"type": "warning",
				"message": [ "Disconnected from TeamSpeak client" ]
			})

	@logutils.trace_call(logger)
	def __on_connected_to_ts_server(self, schandlerid):
		(self.__ts.command_servervariable("virtualserver_name", schandlerid=schandlerid)
			.then(lambda res: self.__set_server_name(schandlerid, res))
			.then(lambda res: self.__notify_connected_to_server(schandlerid))
			.catch(lambda err: logger.error("servervariable command failed", err)))

	def __set_server_name(self, schandlerid, name):
		self.__server_names[schandlerid] = name

	def __notify_connected_to_server(self, schandlerid):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("Notifications"):
			plugin_info.plugin_object.show_notification({
				"type": "info",
				"message": [ "Connected to TeamSpeak server '{0}'".format(self.__server_names[schandlerid]) ]
			})

	@logutils.trace_call(logger)
	def __on_disconnected_from_ts_server(self, schandlerid):
		if schandlerid in self.__server_names:
			for plugin_info in self.plugin_manager.getPluginsOfCategory("Notifications"):
				plugin_info.plugin_object.show_notification({
					"type": "info",
					"message": [ "Disconnected from TeamSpeak server '{0}'".format(self.__server_names[schandlerid]) ]
				})
			del self.__server_names[schandlerid]

	@logutils.trace_call(logger)
	def __on_me_player_added(self, player):
		self.__ts.set_my_game_nick(player.name)

	@logutils.trace_call(logger)
	def __on_user_added(self, schandlerid, clid):
		self.__users[(schandlerid, clid)] = UserTuple._make((
			(schandlerid, clid),
			self.__ts.get_user_parameter(schandlerid, clid, "client-nickname"),
			self.__ts.get_user_parameter(schandlerid, clid, "game-nickname"),
			self.__ts.get_user_parameter(schandlerid, clid, "client-unique-identifier"),
			self.__ts.get_user_parameter(schandlerid, clid, "talking"),
			self.__ts.get_user_parameter(schandlerid, clid, "is-me"),
			self.__ts.get_user_parameter(schandlerid, clid, "my-channel")
		))
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_removed(self, schandlerid, clid):
		del self.__users[(schandlerid, clid)]
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_name_changed(self, schandlerid, clid, old_value, new_value):
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(name=new_value)
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_game_name_changed(self, schandlerid, clid, old_value, new_value):
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(game_name=new_value)
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_speaking_changed(self, schandlerid, clid, old_value, new_value):
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(is_speaking=new_value)
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_my_channel_changed(self, schandlerid, clid, old_value, new_value):
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(my_channel=new_value)
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_server_tab_changed(self, schandlerid):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_current_voice_server_changed(schandlerid)

	def __update_model(self):
		# Discard users which do not have id yet, may occur if user's speak
		# status has come before 'clientlist' command has finished
		users = itertools.ifilter(lambda user: user.id is not None, self.__users.itervalues())
		g_user_model.set_all(self.NS, reduce(self.__combine_by_identity, users, {}).values())

	def __combine_by_identity(self, combined_users, user_tuple):
		kwargs = {
			"id": user_tuple.id,
			"client_ids": [user_tuple.client_id],
			"is_speaking": user_tuple.is_speaking,
			"is_me": user_tuple.is_me,
			"my_channel": user_tuple.my_channel
		}
		if user_tuple.name:
			kwargs["names"] = [user_tuple.name]
		if user_tuple.game_name:
			kwargs["game_names"] = [user_tuple.game_name]
		new_user = UserItem(**kwargs)
		if new_user.id in combined_users:
			combined_users[new_user.id] = combined_users[new_user.id].get_updated(new_user)
		else:
			combined_users[new_user.id] = new_user
		return combined_users

class TeamSpeakClient(clientquery.ClientQuery):

	NICK_META_PATTERN = "<wot_nickname_start>(.+)<wot_nickname_end>"

	def __init__(self):
		super(TeamSpeakClient, self).__init__()
		self.__connect_requested = False
		self.__game_nicknames = {}
		self.__my_game_nick = None
		self.on("connected", self.__on_connected)
		self.on("connected-server", self.__on_connected_server)
		self.on("notifycurrentserverconnectionchanged", self.__on_notifycurrentserverconnectionchanged)
		self.on("user-added", self.__on_user_added)
		self.on("user-changed-client-meta-data", self.__on_user_changed_client_meta_data)
		self.on("user-removed", self.__on_user_removed)
		self.on("error", self.__on_error)

	def get_user_parameter(self, schandlerid, clid, parameter):
		if parameter == "game-nickname":
			client_id = (schandlerid, clid)
			return self.__game_nicknames.get(client_id, None)
		else:
			return super(TeamSpeakClient, self).get_user_parameter(schandlerid, clid, parameter)

	def set_my_game_nick(self, game_nick):
		self.__my_game_nick = game_nick
		self.update_game_nick_to_servers(self.get_connected_schandlerids())

	def update_game_nick_to_servers(self, schandlerids):
		if not self.__my_game_nick:
			return
		for schandlerid in schandlerids:
			clid = self.get_my_clid(schandlerid)
			metadata = self.get_user_parameter(schandlerid, clid, "client_meta_data")
			if not metadata:
				metadata = ""
			new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(self.__my_game_nick)
			if re.search(self.NICK_META_PATTERN, metadata):
				new_metadata = re.sub(self.NICK_META_PATTERN, new_tag, metadata)
			else:
				new_metadata = metadata + new_tag
			if metadata != new_metadata:
				(self.command_clientupdate("client_meta_data", new_metadata, schandlerid)
					.catch(lambda err: logger.error("Failed to update metadata", err)))

	def __on_connected(self):
		(Promise.resolve(None)
			.then(lambda res: self.register_notify("notifycurrentserverconnectionchanged"))
			.catch(lambda err: logger.error("connect failed", err)))

	def __on_connected_server(self, schandlerid):
		self.update_game_nick_to_servers([schandlerid])

	def __on_notifycurrentserverconnectionchanged(self, args):
		self.emit("server-tab-changed", args[0]["schandlerid"])

	def __on_user_added(self, schandlerid, clid):
		metadata = self.get_user_parameter(schandlerid, clid, "client-meta-data")
		if metadata:
			game_nickname = self.__extract_game_nick_from_metadata(metadata)
			if game_nickname:
				client_id = (schandlerid, clid)
				self.__game_nicknames[client_id] = game_nickname

	def __on_user_changed_client_meta_data(self, schandlerid, clid, old_value, new_value):
		client_id = (schandlerid, clid)
		old_nickname = self.__game_nicknames.get(client_id, None)
		new_nickname = self.__extract_game_nick_from_metadata(new_value)
		if old_nickname != new_nickname:
			self.__game_nicknames[client_id] = new_nickname
			self.emit("user-changed-game-nickname", schandlerid=schandlerid, clid=clid, old_value=old_nickname, new_value=new_nickname)

	def __on_user_removed(self, schandlerid, clid):
		client_id = (schandlerid, clid)
		self.__game_nicknames.pop(client_id, None)

	def __extract_game_nick_from_metadata(self, metadata):
		matches = re.search(self.NICK_META_PATTERN, metadata)
		if matches:
			return matches.group(1)
		return None

	def __on_error(self, error):
		logger.error("An error occured", error)
