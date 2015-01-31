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

#include "audioadapter.h"
#include "../interfaces/drivers.h"
#include "../entities/camera.h"
#include "../entities/user.h"

namespace Adapter
{

AudioAdapter::AudioAdapter( Interfaces::AudioDriver *driver, QObject *parent )
	: QObject( parent ), driver( driver )
{
}

void AudioAdapter::removeUser( const Entity::User &user )
{
	userIds.remove( user.id );
	driver->removeUser( user.id );
	if( userIds.isEmpty() && driver->isEnabled() )
	{
		driver->setEnabled( false );
	}
}

void AudioAdapter::positionUser( const Entity::User &user )
{
	userIds.insert( user.id );
	if( !driver->isEnabled() )
	{
		driver->setEnabled( true );
	}
	driver->positionUser( user.id, user.position );
}

void AudioAdapter::positionCamera( const Entity::Camera &camera )
{
	if( driver->isEnabled() )
	{
		Entity::Vector forward = camera.direction;
		// cannot calculate up-vector if both x and z are zero
		if( forward.x == 0 && forward.z == 0 )
		{
			return;
		}
		Entity::Vector up = forward.crossProduct( Entity::Vector( forward.z, 0, -forward.x ) ).getUnit();
		driver->positionCamera( camera.position, forward, up );
	}
}

void AudioAdapter::setPlaybackDeviceName( const QString &name )
{
	driver->setPlaybackDeviceName( name );
}

void AudioAdapter::setPlaybackVolume( float volume )
{
	driver->setPlaybackVolume( volume );
}

void AudioAdapter::reset()
{
	if( driver->isEnabled() )
	{
		driver->setEnabled( false );
	}
	driver->removeAllUsers();
	driver->positionCamera( Entity::Vector(), Entity::Vector(), Entity::Vector() );
}

}
