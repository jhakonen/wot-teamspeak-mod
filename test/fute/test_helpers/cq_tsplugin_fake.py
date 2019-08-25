import asyncio

import copy
from queue import Queue, Empty
import random
import re
import socket
import threading
import time
import weakref

from tessumod.ts3 import parse_client_query_parameters, escape_client_query_value

_SELF_USER_NAME = "Testinukke"
_NO_RESPONSE = (None, None)


class TSClientQueryDataModel(object):
	def __init__(self):
		self._clids = []
		self._event_queue = Queue()
		self._connected_to_server = False
		self._users = {}
		self.set_schandler_id(random.uniform(1, 10))

	def get_event(self):
		return self._event_queue.get(block=False)

	def send_event(self, event):
		self._event_queue.put(event)

	def is_connected_to_server(self):
		return self._connected_to_server

	def set_connected_to_server(self, connected):
		self._connected_to_server = connected

	def get_my_user(self):
		for clid in self._users:
			user = self._users[clid]
			if user.name == _SELF_USER_NAME:
				return user

	def get_user(self, name=None, clid=None):
		user = self._get_user(name, clid)
		if user is None:
			raise RuntimeError("User not found")
		return user

	def _get_user(self, name, clid):
		if clid is not None:
			return self._users.get(str(clid), None)
		elif name is not None:
			for user in self.get_users():
				if user.name == name:
					return user
			return None
		else:
			raise RuntimeError("Parameter missing")

	def get_users(self):
		return self._users.values()

	def set_user(self, name, **kwargs):
		if name not in self._clids:
			self._clids.append(name)
		clid = str(self._clids.index(name))
		if clid not in self._users:
			self._users[clid] = User(service=self, name=name, clid=clid)
		if "schandlerid" not in kwargs:
			kwargs["schandlerid"] = self.get_schandler_id()
		self._users[clid].set(**kwargs)

	def get_schandler_id(self):
		return self._schandler_id

	def set_schandler_id(self, schandler_id):
		self._schandler_id = int(schandler_id)


class TSClientQueryService(object):

	def __init__(self, model):
		self._server = None
		self._model = model
		self.set_user(_SELF_USER_NAME)
		self.handler = None

	async def start(self):
		if self._server:
			return
		self._server = await asyncio.start_server(self.handle_accept, "127.0.0.1", 25639)
		await self._server.start_serving()

	def handle_accept(self, reader, writer):
		self.handler = TSClientQueryConnection(self._model, reader, writer)

	async def stop(self):
		if self._server:
			self._server.close()
			await self._server.wait_closed()
		if self.handler:
			await self.handler.close()

	def send_event(self, event):
		self._model.send_event(event)

	def set_connected_to_server(self, connected):
		self._model.set_connected_to_server(connected)

	def set_user(self, name, **kwargs):
		self._model.set_user(name, **kwargs)

	def get_user(self, name=None, clid=None):
		return self._model.get_user(name, clid)


class TSClientQueryConnection:
	def __init__(self, data, reader, writer):
		self._model = data
		self._reader = reader
		self._writer = writer
		self._registered_events = []
		self._closed = False
		self._handler_task = asyncio.create_task(self._handle())

	async def close(self):
		self._closed = True
		self._writer.close()
		try:
			await self._writer.wait_closed()
		except ConnectionResetError:
			pass
		except BrokenPipeError:
			pass
		await self._handler_task

	async def _handle(self):
		try:
			await self._send_welcome_message()
			await asyncio.gather(self._handle_commands(), self._handle_events())
		except ConnectionResetError:
			pass
		except asyncio.IncompleteReadError:
			pass

	async def _send_welcome_message(self):
		await self._write_line("TS3 Client")
		await self._write_line(
			"Welcome to the TeamSpeak 3 ClientQuery interface, type \"help\" "
			"for a list of commands and \"help <command>\" for information on "
			"a specific command."
		)
		await self._write_line(f"selected schandlerid={self._model.get_schandler_id()}")

	async def _handle_commands(self):
		while not self._closed:
			cmd_data = await self._read_line()
			cmd_type, cmd_options, cmd_params = self._parse_command_data(cmd_data)

			if cmd_type == "auth":
				await self._write_status()

			elif cmd_type == "clientnotifyunregister":
				if self._registered_events:
					self._registered_events.clear()
					await self._write_status()

			elif cmd_type == "clientnotifyregister":
				event = cmd_params["event"]
				if event not in self._registered_events:
					self._registered_events.append(event)
					await self._write_status()

			elif cmd_type == "whoami":
				if self._model.is_connected_to_server():
					user = self._model.get_my_user()
					await self._write_line(f"clid={user.clid} cid={user.cid}")
					await self._write_status()
				else:
					await self._write_status(1794, "not connected")

			elif cmd_type == "clientgetuidfromclid":
				clid = cmd_params["clid"]
				user = self._model.get_user(clid=clid)
				self._model.send_event(
					"notifyclientuidfromclid "
					f"schandlerid={user.schandlerid} "
					f"clid={user.clid} "
					f"cluid={user.cluid} "
					f"nickname={escape_client_query_value(user.name)}"
				)
				await self._write_status()

			elif cmd_type == "clientvariable":
				clid = cmd_params["clid"]
				client_meta_data = cmd_params.get("client_meta_data", None)
				user = self._model.get_user(clid=clid)
				if client_meta_data is not None:
					await self._write_line(f"clid={clid} client_meta_data={escape_client_query_value(user.metadata)}")
				else:
					await self._write_line(f"clid={clid}")
				await self._write_status()

			elif cmd_type == "clientlist":
				entries = []
				for user in self._model.get_users():
					res_params = [
						f"clid={user.clid}",
						f"cid={user.cid}",
						f"client_database_id=DBID{user.clid}",
						f"client_nickname={user.name}",
						"client_type=0",
						f"client_flag_talking={1 if user.speaking else 0}"
					]
					if "uid" in cmd_options:
						res_params.append(f"client_unique_identifier={user.cluid}")
					entries.append(" ".join(escape_client_query_value(param) for param in res_params))
				await self._write_line(("|".join(entries)))
				await self._write_status()

			elif cmd_type == "clientupdate":
				if "client_meta_data" in cmd_params:
					self._model.get_my_user().metadata = cmd_params["client_meta_data"]
				await self._write_status()

			elif cmd_type == "currentschandlerid":
				await self._write_line(f"schandlerid={self._model.get_schandler_id()}")
				await self._write_status()

			elif cmd_type == "use":
				self._model.set_schandler_id(cmd_params["schandlerid"])
				await self._write_status()

			elif cmd_type == "servervariable":
				if "virtualserver_name" in cmd_params:
					await self._write_line("virtualserver_name=Dummy\sServer")
				await self._write_status()

			else:
				await self._write_status(256, "command not found")
				print("ERROR: Response missing for command:", repr(cmd_data))

	def _parse_command_data(self, cmd_data):
		cmd_type, params_str = re.match("^([\S]+)\s?(.*)", cmd_data).groups()
		cmd_params = {}
		cmd_options = []
		entries = parse_client_query_parameters(params_str)
		for entry in entries:
			for key, value in entry.items():
				if key.startswith("-"):
					cmd_options.append(key[1:])
				elif key != "":
					cmd_params[key] = value
		return cmd_type, cmd_options, cmd_params

	async def _handle_events(self):
		while not self._closed:
			try:
				event = self._model.get_event()
				if event.split(None, 1)[0] in self._registered_events:
					await self._write_line(event)
				else:
					self._model.send_event(event)
			except Empty:
				pass
			await asyncio.sleep(0.001)

	async def _read_line(self):
		line = await self._reader.readuntil(b"\n\r")
		return line.decode("utf8").strip()

	async def _write_line(self, line):
		self._writer.write(line.encode('utf8') + b"\n\r")
		await self._writer.drain()

	async def _write_status(self, code=0, message="ok"):
		if code is None or message is None:
			return
		message = message.replace(" ", "\\s")
		await self._write_line(f"error id={code} msg={message}")


class User(object):

	def __init__(self, service, name, clid):
		self._service = service
		self._name = name
		self._clid = str(clid)
		self._cid = None
		self._cluid = None
		self._schandlerid = None
		self._metadata = None
		self._speaking = None
		self.set()

	def set(self, **kwargs):
		self.cid = str(kwargs["cid"] if "cid" in kwargs else 1)
		self.cluid = str(kwargs["cluid"] if "cluid" in kwargs else "BAADF00D" + self._clid)
		self.schandlerid = str(kwargs["schandlerid"] if "schandlerid" in kwargs else 1)
		self.metadata = str(kwargs["metadata"] if "metadata" in kwargs else "")
		self.speaking = kwargs["speaking"] if "speaking" in kwargs else False

	@property
	def name(self):
		return self._name

	@property
	def clid(self):
		return self._clid

	@property
	def cid(self):
		return self._cid
	@cid.setter
	def cid(self, value):
		self._cid = value

	@property
	def cluid(self):
		return self._cluid
	@cluid.setter
	def cluid(self, value):
		self._cluid = value

	@property
	def schandlerid(self):
		return self._schandlerid
	@schandlerid.setter
	def schandlerid(self, value):
		self._schandlerid = value

	@property
	def metadata(self):
		return self._metadata
	@metadata.setter
	def metadata(self, value):
		if self._metadata is not None and self._metadata != value:
			self._service.send_event(f"notifyclientupdated schandlerid={self._schandlerid} clid={self._clid} client_meta_data={value}")
		self._metadata = value

	@property
	def speaking(self):
		return self._speaking
	@speaking.setter
	def speaking(self, value):
		if self._speaking is not None and self._speaking != value:
			self._service.send_event(f"notifytalkstatuschange status={1 if value else 0} clid={self._clid}")
		self._speaking = value
