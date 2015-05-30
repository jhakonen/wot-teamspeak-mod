/*
 * TessuMod: Mod for integrating TeamSpeak into World of Tanks
 * Copyright (C) 2015  Janne Hakonen
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
 * USA
 */

#include "userstorage.h"

namespace Storage
{

UserStorage::UserStorage( QObject *parent )
	: QObject( parent )
{
}

bool UserStorage::has( quint16 id ) const
{
	return users.contains( id );
}

Entity::User UserStorage::get( quint16 id ) const
{
	if( has( id ) )
	{
		return users[id];
	}
	throw new std::runtime_error( "User not found from storage" );
}

QList<Entity::User> UserStorage::getAll() const
{
	return users.values();
}

void UserStorage::set( const Entity::User &user )
{
	users[user.id] = user;
}

void UserStorage::remove( quint16 id )
{
	users.remove( id );
}

}
