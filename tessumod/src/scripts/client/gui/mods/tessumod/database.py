# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

from lib import pydash as _
from lib.littletable.littletable import Table, DataObject
from messages import (PlayerMeMessage, BattlePlayerMessage, VehicleMessage,
					  PrebattlePlayerMessage, PlayerSpeakingMessage,
					  UserMessage, PairingMessage)
from collections import Mapping

messages = None

class DictDataObject(Mapping):
	def __init__(self, data):
		self.__data = data

	def __repr__(self):
		return repr(self.__data)

	def __getattr__(self, name):
		try:
			return self.__data[name.replace('_', '-')]
		except KeyError, e:
			raise AttributeError(e)

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

# HACK: Remove once Item/Message classes attributes are safe to change
def message_data(self):
	return {k.replace('_', '-'): v for k, v in self.__dict__.iteritems()}
DataObject.message_data = message_data
def new__getitem__(self, k):
	return orig__getitem__(self, k.replace('-', '_'))
orig__getitem__ = DataObject.__getitem__
DataObject.__getitem__ = new__getitem__

# ======================
# Me player table
# ======================
_me_player = Table('me_player')
_me_player.create_index('id', unique=True)

def set_me_player(id, name):
	_me_player.remove_many(_me_player)
	player = DataObject(id=id, name=name)
	_me_player.insert(player)
	messages.publish(PlayerMeMessage("added", player.message_data()))

def get_me_players():
	return _me_player.clone()

# ======================
# Battle players table
# ======================
_battle_players = Table('battle_players')
_battle_players.create_index('id', unique=True)

def insert_battle_player(id, name):
	if not _battle_players.where(id=id):
		player = DataObject(id=id, name=name)
		_battle_players.insert(player)
		messages.publish(BattlePlayerMessage("added", player.message_data()))

def remove_battle_player(id):
	player = _.head(_battle_players.where(id=id))
	if player:
		_battle_players.remove(player)
		messages.publish(BattlePlayerMessage("removed", player.message_data()))

def get_all_battle_players():
	return _battle_players.clone()

# ======================
# Vehicles table
# ======================
_vehicles = Table('vehicles')
_vehicles.create_index('id', unique=True)

def insert_vehicle(id, player_id, is_alive):
	if not _vehicles.where(id=id):
		vehicle = DataObject(id=id, player_id=player_id, is_alive=is_alive)
		_vehicles.insert(vehicle)
		messages.publish(VehicleMessage("added", vehicle.message_data()))

def update_vehicle(id, player_id, is_alive):
	if _vehicles.delete(id=id):
		vehicle = DataObject(id=id, player_id=player_id, is_alive=is_alive)
		_vehicles.insert(vehicle)
		messages.publish(VehicleMessage("modified", vehicle.message_data()))

def remove_vehicle(id):
	vehicle = _.head(_vehicles.where(id=id))
	if vehicle:
		_vehicles.remove(vehicle)
		messages.publish(VehicleMessage("removed", vehicle.message_data()))

def get_all_vehicles():
	return _vehicles.clone()

# ======================
# Prebattle players table
# ======================
_prebattle_players = Table('prebattle_players')
_prebattle_players.create_index('id', unique=True)

def insert_prebattle_player(id, name):
	if not _prebattle_players.where(id=id):
		player = DataObject(id=id, name=name)
		_prebattle_players.insert(player)
		messages.publish(PrebattlePlayerMessage("added", player.message_data()))

def remove_prebattle_player(id):
	player = _.head(_prebattle_players.where(id=id))
	if player:
		_prebattle_players.remove(player)
		messages.publish(PrebattlePlayerMessage("removed", player.message_data()))

def get_all_prebattle_players():
	return _prebattle_players.clone()

# ======================
# Speaking players table
# ======================
_speaking_players = Table('speaking_players')
_speaking_players.create_index('id', unique=True)

def set_players_speaking(player_ids, speaking):
	for player_id in player_ids:
		old_player = _.head(_speaking_players.where(id=player_id))
		if speaking and not old_player:
			new_player = DataObject(id=player_id)
			_speaking_players.insert(new_player)
			messages.publish(PlayerSpeakingMessage("added", new_player.message_data()))
		elif not speaking and old_player:
			_speaking_players.remove(old_player)
			messages.publish(PlayerSpeakingMessage("removed", old_player.message_data()))

def get_all_speaking_players():
	return _speaking_players.clone()

# ======================
# Users table
# ======================
_users = Table('users')
_users.create_index('id', unique=True)

def insert_user(id, name, game_name, unique_id, speaking, is_me, my_channel):
	if _users.where(id=id):
		return
	new_user = DataObject(id=id, name=name, game_name=game_name,
		unique_id=unique_id, speaking=speaking, is_me=is_me,
		my_channel=my_channel)
	_users.insert(new_user)
	messages.publish(UserMessage("added", new_user.message_data()))

def update_user(id, name, game_name, unique_id, speaking, is_me, my_channel):
	old_user = _.head(_users.where(id=id))
	if old_user:
		_users.remove(old_user)
		new_user = DataObject(id=id, name=name, game_name=game_name,
			unique_id=unique_id, speaking=speaking, is_me=is_me,
			my_channel=my_channel)
		_users.insert(new_user)
		messages.publish(UserMessage("modified", new_user.message_data()))

def remove_user(id):
	old_user = _.head(_users.where(id=id))
	if not old_user:
		return
	_users.remove(old_user)
	messages.publish(UserMessage("removed", old_user.message_data()))

def get_all_users():
	return _users.clone()

# ======================
# Cached users table
# ======================
_cached_users = Table('cached_users')
_cached_users.create_index('unique_id', unique=True)

def insert_cached_user(unique_id, name):
	_cached_users.insert(DataObject(unique_id=unique_id, name=name))

def remove_cached_user(unique_id):
	_cached_users.delete(unique_id=unique_id)

def get_all_cached_users():
	return _cached_users.clone()

# ======================
# Cached players table
# ======================
_cached_players = Table('cached_players')
_cached_players.create_index('id', unique=True)

def insert_cached_player(id, name):
	_cached_players.insert(DataObject(id=id, name=name))

def remove_cached_player(id):
	_cached_players.delete(id=id)

def get_all_cached_players():
	return _cached_players.clone()

# ======================
# Pairings table
# ======================
_pairings = Table('pairings')
_pairings.create_index('player_id')
_pairings.create_index('user_unique_id')

def insert_pairing(user_unique_id, player_id):
	if not _pairings.where(user_unique_id=user_unique_id, player_id=player_id):
		pairing = DataObject(user_unique_id=user_unique_id, player_id=player_id)
		_pairings.insert(pairing)
		messages.publish(PairingMessage("added" , pairing.message_data()))

def remove_pairing(user_unique_id, player_id):
	pairing = _.head(_pairings.where(user_unique_id=user_unique_id, player_id=player_id))
	if pairing:
		_pairings.remove(pairing)
		messages.publish(PairingMessage("removed" , pairing.message_data()))

def get_all_pairings():
	return _pairings.clone()
