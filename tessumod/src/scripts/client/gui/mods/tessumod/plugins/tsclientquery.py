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

from gui.mods.tessumod import plugintypes, logutils, models
from gui.mods.tessumod.models import g_user_model, UserItem
from gui.mods.tessumod.infrastructure import clientquery, gameapi
import re
import collections

logger = logutils.logger.getChild("tsclientquery")
UserTuple = collections.namedtuple('UserTuple', ('client_id', 'name', 'game_name', 'id', 'is_speaking', 'is_me', 'my_channel'))

class TSClientQueryPlugin(plugintypes.ModPlugin, plugintypes.SettingsMixin):
	"""
	This plugin ...
	"""

	NS = "voice"

	def __init__(self):
		super(TSClientQueryPlugin, self).__init__()
		self.__host = None
		self.__port = None
		self.__ts = TeamSpeakClient()
		self.__ts.on("connected", self.__on_connected_to_ts)
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
		self.__selected_schandlerid = None
		self.__users = {}
		g_user_model.add_namespace(self.NS)

	@logutils.trace_call(logger)
	def initialize(self):
		self.__connect()

	@logutils.trace_call(logger)
	def on_settings_changed(self, section, name, value):
		"""
		Implemented from SettingsMixin.
		"""
		if section == "TSClientQueryService":
			if name == "host":
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
		Implemented from SettingsMixin.
		"""
		return {
			"TSClientQueryService": {
				"help": "",
				"variables": [
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
	def __on_connected_to_ts(self):
		'''Called when TessuMod manages to connect TeamSpeak client. However, this
		doesn't mean that the client is connected to any TeamSpeak server.
		'''
		# TODO: send notification center message
		# TODO: show teamspeak-plugin install message
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_voice_client_connected()

	@logutils.trace_call(logger)
	def __on_disconnected_from_ts(self):
		'''Called when TessuMod loses connection to TeamSpeak client.'''
		# TODO: send notification center message
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_voice_client_disconnected()

	@logutils.trace_call(logger)
	def __on_connected_to_ts_server(self, schandlerid):
		# TODO: send notification center message
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_voice_server_connected()

	@logutils.trace_call(logger)
	def __on_disconnected_from_ts_server(self, schandlerid):
		for plugin_info in self.plugin_manager.getPluginsOfCategory("VoiceClientListener"):
			plugin_info.plugin_object.on_voice_server_disconnected()

	@logutils.trace_call(logger)
	def __on_user_added(self, schandlerid, clid):
		self.__users[(schandlerid, clid)] = UserTuple._make((
			(schandlerid, clid),
			self.__ts.get_user_parameter(schandlerid, clid, "client-nickname"),
			self.__ts.get_user_parameter(schandlerid, clid, "game-nickname"),
			self.__ts.get_user_parameter(schandlerid, clid, "client-unique-identifier"),
			bool(self.__ts.get_user_parameter(schandlerid, clid, "talking")),
			bool(self.__ts.get_user_parameter(schandlerid, clid, "is-me")),
			bool(self.__ts.get_user_parameter(schandlerid, clid, "my-channel"))
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
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(is_speaking=bool(new_value))
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_user_my_channel_changed(self, schandlerid, clid, old_value, new_value):
		self.__users[(schandlerid, clid)] = self.__users[(schandlerid, clid)]._replace(my_channel=bool(new_value))
		self.__update_model()

	@logutils.trace_call(logger)
	def __on_server_tab_changed(self, schandlerid):
		self.__selected_schandlerid = schandlerid
		# TODO: inform audio positioning the currently selected tab (since
		# client_id of current server is passed via shared memory)

	def __update_model(self):
		g_user_model.set_all(self.NS, reduce(self.__combine_by_identity, self.__users.itervalues(), {}).values())

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

	def __on_connected(self):
		self.register_notify("notifycurrentserverconnectionchanged")

		def on_currentschandlerid_finish(error, result):
			if error:
				log.LOG_ERROR("currentschandlerid command failed", error)
			else:
				self.emit("server-tab-changed", int(result["schandlerid"]))
		self.command_currentschandlerid(callback=on_currentschandlerid_finish)

	def __on_connected_server(self, schandlerid):
		# TODO: What if game doesn't have player's name yet when this happens?
		clid = self.get_my_clid(schandlerid)
		metadata = self.get_user_parameter(schandlerid, clid, "client_meta_data")
		if not metadata:
			metadata = ""
		new_tag = "<wot_nickname_start>{0}<wot_nickname_end>".format(gameapi.Player.get_my_name())
		if re.search(self.NICK_META_PATTERN, metadata):
			metadata = re.sub(self.NICK_META_PATTERN, new_tag, metadata)
		else:
			metadata += new_tag
		self.command_clientupdate("client_meta_data", metadata, schandlerid)

	def __on_notifycurrentserverconnectionchanged(self, args):
		self.emit("server-tab-changed", int(args[0]["schandlerid"]))

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
		log.LOG_ERROR("An error occured", error)
