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

import collections
import functools
from gui.mods.tessumod.infrastructure.eventemitter import EventEmitterMixin

class ItemModel(collections.Mapping, EventEmitterMixin):

	def __init__(self):
		super(ItemModel, self).__init__()
		self.__items = {}

	def set(self, item):
		id = item.id
		# determine type of change
		is_new = id not in self.__items
		is_modified = not is_new and id in self.__items and item != self.__items[id]
		# update model and notify of the change
		if is_new:
			self.__items[id] = item
			self.emit("added", item)
		elif is_modified:
			old_item = self.__items[id]
			self.__items[id] = item
			self.emit("modified", old_item, item)

	def remove(self, id):
		if id in self.__items:
			old_item = self.__items[id]
			del self.__items[id]
			self.emit("removed", old_item)

	def clear(self):
		for id in self.__items.keys():
			self.remove(id)

	def __getitem__(self, id):
		return self.__items[id]

	def __iter__(self):
		return iter(self.__items)

	def __len__(self):
		return len(self.__items)


class Priority:
	NORMAL = 0
	LOW = -1


class NamespaceModel(collections.Mapping, EventEmitterMixin):

	def __init__(self, model):
		super(NamespaceModel, self).__init__()
		self.__model = model
		self.__model.on("added", functools.partial(self.emit, "added"))
		self.__model.on("modified", functools.partial(self.emit, "modified"))
		self.__model.on("removed", functools.partial(self.emit, "removed"))
		self.__items_by_ns = {}
		self.__priority_namespaces = []
		self.__namespaces = []

	def add_namespace(self, ns, priority=Priority.NORMAL):
		assert ns not in self.__namespaces, "Namespace {} already added".format(ns)
		self.__priority_namespaces.append((priority, ns))
		self.__namespaces = sorted(self.__priority_namespaces, lambda p1, p2: cmp(p1[0], p2[0]))
		self.__namespaces = map(lambda p: p[1], self.__namespaces)
		self.__items_by_ns.setdefault(ns, {})

	def set(self, ns, item):
		id = item.id
		item.namespaces = [ns]
		self.__items_by_ns[ns][id] = item
		self.__update_public_item_id(id)

	def set_all(self, ns, items_iter):
		old_ids = set(self.__items_by_ns[ns].iterkeys())
		new_ids = set()
		for item in items_iter:
			new_ids.add(item.id)
			item.namespaces = [ns]
			self.__items_by_ns[ns][item.id] = item
		all_ids = old_ids | new_ids
		for id in all_ids:
			self.__update_public_item_id(id)

	def remove(self, ns, id):
		if id in self.__items_by_ns[ns]:
			del self.__items_by_ns[ns][id]
			self.__update_public_item_id(id)

	def clear(self, ns):
		for id in self.__items_by_ns[ns].keys():
			self.remove(ns, id)

	def __update_public_item_id(self, id):
		# build public item by combining items of 'id' from all namespaces in their priority order
		all_items = []
		public_item = None
		for ns in self.__namespaces:
			if id in self.__items_by_ns[ns]:
				all_items.append(self.__items_by_ns[ns][id])
		if all_items:
			public_item = all_items.pop(0)
			public_item = reduce(lambda public_item, ns_item: public_item.get_updated(ns_item), all_items, public_item)
		if public_item:
			self.__model.set(public_item)
		else:
			self.__model.remove(id)

	def __getitem__(self, id):
		return self.__model[id]

	def __iter__(self):
		return iter(self.__model)

	def __len__(self):
		return len(self.__model)


class FilterModel(collections.Mapping, EventEmitterMixin):

	def __init__(self, source_model):
		super(FilterModel, self).__init__()
		self.__source_model = source_model
		self.__source_model.on("added", self.__on_source_model_added)
		self.__source_model.on("modified", self.__on_source_model_modified)
		self.__source_model.on("removed", self.__on_source_model_removed)
		self.__target_model = ItemModel()
		self.__target_model.on("added", functools.partial(self.emit, "added"))
		self.__target_model.on("modified", functools.partial(self.emit, "modified"))
		self.__target_model.on("removed", functools.partial(self.emit, "removed"))
		self.__filters = []

	def add_filter(self, func):
		self.__filters.append(func)
		self.invalidate()

	def allow_namespaces(self, namespaces):
		self.add_filter(lambda item: any(ns in item.namespaces for ns in namespaces))

	def invalidate(self):
		for item in self.__source_model.itervalues():
			if self.__is_ok(item):
				self.__target_model.set(item)
			elif item.id in self.__target_model:
				self.__target_model.remove(item.id)

	def __on_source_model_added(self, new_item):
		if self.__is_ok(new_item):
			self.__target_model.set(new_item)

	def __on_source_model_modified(self, old_item, new_item):
		if self.__is_ok(new_item):
			self.__target_model.set(new_item)
		elif new_item.id in self.__target_model:
			self.__target_model.remove(new_item.id)

	def __on_source_model_removed(self, old_item):
		if old_item.id in self.__target_model:
			self.__target_model.remove(old_item.id)

	def __is_ok(self, item):
		return all(f(item) for f in self.__filters)

	def __getitem__(self, id):
		return self.__target_model[id]

	def __iter__(self):
		return iter(self.__target_model)

	def __len__(self):
		return len(self.__target_model)


def uniqueify(sequence):
	"""
	Returns a new list constructed from 'sequence' with non-unique items removed and keeps order.
	From:
	    http://stackoverflow.com/a/480227
	"""
	seen = set()
	seen_add = seen.add
	return [x for x in sequence if not (x in seen or seen_add(x))]

class Item(object):

	VALID_KWARGS = set()

	def __init__(self, id, attributes):
		self.__has_attributes = set(attributes)
		unknown_args = self.__has_attributes - self.VALID_KWARGS
		assert not unknown_args, "Unknown arguments: {}".format(unknown_args)
		self.__id         = id
		self.__namespaces = []

	def get_attributes(self):
		attributes = {}
		for arg_name in self.VALID_KWARGS:
			if self.has_attribute(arg_name):
				attributes[arg_name] = getattr(self, arg_name)
		return attributes

	def has_attribute(self, name):
		return name in self.__has_attributes

	@property
	def id(self):
		return self.__id

	@property
	def namespaces(self):
		return self.__namespaces

	@namespaces.setter
	def namespaces(self, namespaces):
		self.__namespaces = namespaces

	def equal(self, other):
		return self.id == other.id and self.namespaces == other.namespaces

	def __eq__(self, other):
		return self.equal(other)

	def __ne__(self, other):
		return not self.equal(other)


class PlayerItem(Item):
	"""
	This class is an interface for getting player models from other plugins.
	Each player is stored into the model with a key which is same as player's "id" value.

	Possible namespaces include:
	 * battle
	 * prebattle
	 * friends
	 * clanmembers
	 * voice
	 * cache

	Each player in the model is dict object which must have at least following key/values:
	 * "id": [int] <player id>
	 * "name": [string] <player name>
	 * "is_me": [bool] <is self player>

	With namespace 'battle' the dict must have following entries:
	 * "vehicle_id": [int] <vehicle id in battle>
	 * "is_alive": [bool] <is player alive in battle>

	With namespace 'voice' the dict must have entry:
	 * "speaking": [bool] <is player speaking>
	"""

	VALID_KWARGS = set(["name", "user_ids", "vehicle_id", "is_alive", "speaking", "is_me"])

	def __init__(self, id, **kwargs):
		super(PlayerItem, self).__init__(id, attributes=kwargs.keys())
		self.__name       = kwargs.get("name", "")
		self.__user_ids   = sorted(kwargs.get("user_ids", []))
		self.__vehicle_id = kwargs.get("vehicle_id", 0)
		self.__is_alive   = kwargs.get("is_alive", False)
		self.__speaking   = kwargs.get("speaking", False)
		self.__is_me      = kwargs.get("is_me", False)
		assert isinstance(self.id, int)
		assert isinstance(self.__user_ids, list)
		assert isinstance(self.__name, basestring)
		assert isinstance(self.__vehicle_id, int)
		assert isinstance(self.__is_alive, bool)
		assert isinstance(self.__speaking, bool)

	def get_updated(self, player):
		assert self.id == player.id
		attributes = self.get_attributes()
		attributes.update(player.get_attributes())
		item = PlayerItem(id=self.id, **attributes)
		item.namespaces = uniqueify(self.namespaces + player.namespaces)
		return item

	def equal(self, other):
		result = super(PlayerItem, self).equal(other)
		result &= self.__name == other.__name
		result &= self.__user_ids == other.__user_ids
		result &= self.__vehicle_id == other.__vehicle_id
		result &= self.__is_alive == other.__is_alive
		result &= self.__speaking == other.__speaking
		result &= self.__is_me == other.__is_me
		return result

	def __repr__(self):
		args = [("id", self.id), ("namespaces", self.namespaces)]
		args.extend(self.get_attributes().iteritems())
		args = [(key, repr(value)) for key, value in args]
		return "PlayerItem({})".format(", ".join("=".join(arg) for arg in args))

	@property
	def name(self):
		return self.__name

	@property
	def user_ids(self):
		return self.__user_ids

	@property
	def vehicle_id(self):
		return self.__vehicle_id

	@property
	def is_alive(self):
		return self.__is_alive

	@property
	def speaking(self):
		return self.__speaking

	@property
	def is_me(self):
		return self.__is_me


class UserItem(Item):
	"""
	This class is an interface for getting voice chat user models from other plugins.
	Each user is stored into the model with a key which is same as user's "id" value.

	Possible model names include:
	 * voice
	 * cache

	Each user in the model is a dict object which must have following key/values:
	 * "id": [string] <id which identifies user, multiple users may have same identity>
	 * "names": [list of strings] <user names>

	With source 'voice' the dict must have following entries:
	 * "game_name": [list of strings] <names in game if available, empty list if not>
	 * "is_speaking": [bool] <is user speaking or not>
	 * "is_me": [bool] <is self user>
	"""

	VALID_KWARGS = set(["client_ids", "names", "game_names", "is_speaking", "is_me", "my_channel"])

	def __init__(self, id, **kwargs):
		super(UserItem, self).__init__(id, attributes=kwargs.keys())
		self.__client_ids  = kwargs.get("client_ids", [])
		self.__names       = kwargs.get("names", [])
		self.__game_names  = kwargs.get("game_names", [])
		self.__is_speaking = kwargs.get("is_speaking", False)
		self.__is_me       = kwargs.get("is_me", False)
		self.__my_channel  = kwargs.get("my_channel", False)
		assert isinstance(self.id, basestring)
		assert isinstance(self.__client_ids, list)
		assert isinstance(self.__names, list)
		assert isinstance(self.__game_names, list)
		assert isinstance(self.__is_speaking, bool)
		assert isinstance(self.__is_me, bool)
		assert isinstance(self.__my_channel, bool)

	def get_updated(self, user):
		assert self.id == user.id
		attributes = self.get_attributes()
		attributes.update(user.get_attributes())
		item = UserItem(id=self.id, **attributes)
		item.namespaces = uniqueify(self.namespaces + user.namespaces)
		return item

	def equal(self, other):
		result = super(UserItem, self).equal(other)
		result &= self.__client_ids == other.__client_ids
		result &= self.__names == other.__names
		result &= self.__game_names == other.__game_names
		result &= self.__is_speaking == other.__is_speaking
		result &= self.__is_me == other.__is_me
		result &= self.__my_channel == other.__my_channel
		return result

	def __repr__(self):
		args = [("id", self.id), ("namespaces", self.namespaces)]
		args.extend(self.get_attributes().iteritems())
		args = [(key, repr(value)) for key, value in args]
		return "UserItem({})".format(", ".join("=".join(arg) for arg in args))

	@property
	def client_ids(self):
		return self.__client_ids

	@property
	def names(self):
		return self.__names

	@property
	def game_names(self):
		return self.__game_names

	@property
	def is_speaking(self):
		return self.__is_speaking

	@property
	def is_me(self):
		return self.__is_me

	@property
	def my_channel(self):
		return self.__my_channel


class PairingItem(Item):

	VALID_KWARGS = set(["player_ids",])

	def __init__(self, id, player_ids):
		super(PairingItem, self).__init__(id, attributes=["player_ids"])
		self.__player_ids = player_ids
		assert isinstance(self.id, basestring)
		assert isinstance(self.__player_ids, list)

	def get_updated(self, pairing):
		assert self.id == pairing.id
		attributes = self.get_attributes()
		attributes.update(pairing.get_attributes())
		item = PairingItem(id=self.id, **attributes)
		item.namespaces = uniqueify(self.namespaces + pairing.namespaces)
		return item

	def equal(self, other):
		result = super(PairingItem, self).equal(other)
		result &= self.__player_ids == other.__player_ids
		return result

	def __repr__(self):
		args = [("id", self.id), ("namespaces", self.namespaces)]
		args.extend(self.get_attributes().iteritems())
		args = [(key, repr(value)) for key, value in args]
		return "PairingItem({})".format(", ".join("=".join(arg) for arg in args))

	@property
	def player_ids(self):
		return self.__player_ids


g_player_model = NamespaceModel(ItemModel())
g_user_model = NamespaceModel(ItemModel())
g_pairing_model = NamespaceModel(ItemModel())
