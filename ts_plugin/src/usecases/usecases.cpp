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

#include "usecases.h"
#include "../entities/user.h"
#include "../entities/camera.h"
#include "../entities/settings.h"
#include <QList>
#include <QString>

namespace {

bool notInGameOrChat( const Entity::User &user )
{
	return !user.inGame && !user.inChat;
}

}

namespace UseCase
{

void UseCases::applicationInitialize()
{
	Entity::Settings settings = settingsStorage->get();
	if( settings.positioningEnabled )
	{
		updatePlaybackDeviceToBackends( settings.audioBackend );
		updatePlaybackVolumeToBackends( settings.audioBackend );
	}
}

void UseCases::positionUser( quint16 id, const Entity::Vector& position )
{
	Entity::Settings settings = settingsStorage->get();
	if( settings.positioningEnabled && userStorage->has( id ) )
	{
		Entity::User user = userStorage->get( id );
		user.position = position;
		userStorage->set( user );
		if( user.paired() )
		{
			adapterStorage->getAudio( settings.audioBackend )->positionUser( user );
		}
	}
}

void UseCases::positionCamera( const Entity::Vector& position, const Entity::Vector& direction )
{
	Entity::Settings settings = settingsStorage->get();
	if( settings.positioningEnabled )
	{
		Entity::Camera camera = cameraStorage->get();
		camera.position = position;
		camera.direction = direction;
		cameraStorage->set( camera );
		adapterStorage->getAudio( settings.audioBackend )->positionCamera( camera );
	}
}

void UseCases::addGameUser( quint16 id )
{
	if( adapterStorage->getVoiceChat()->getMyUserId() == id )
	{
		return;
	}
	Entity::Settings settings = settingsStorage->get();
	Entity::User user;
	if( userStorage->has( id ) )
	{
		user = userStorage->get( id );
	}
	else
	{
		user.id = id;
	}
	user.inGame = true;
	userStorage->set( user );
	if( user.paired() )
	{
		adapterStorage->getAudio( settings.audioBackend )->positionUser( user );
	}
}

void UseCases::removeGameUser( quint16 id )
{
	if( !userStorage->has( id ) )
	{
		return;
	}
	Entity::Settings settings = settingsStorage->get();
	Entity::User user = userStorage->get( id );
	if( user.paired() )
	{
		adapterStorage->getAudio( settings.audioBackend )->removeUser( user );
	}
	user.inGame = false;
	if( !user.exists() )
	{
		userStorage->remove( id );
	}
}

void UseCases::addChatUser( quint16 id )
{
	Entity::User user;
	Entity::Settings settings = settingsStorage->get();
	if( userStorage->has( id ) )
	{
		user = userStorage->get( id );
	}
	else
	{
		user.id = id;
	}
	user.inChat = true;
	userStorage->set( user );
	if( user.paired() )
	{
		adapterStorage->getAudio( settings.audioBackend )->positionUser( user );
	}
}

void UseCases::removeChatUser( quint16 id )
{
	if( !userStorage->has( id ) )
	{
		return;
	}
	Entity::Settings settings = settingsStorage->get();
	Entity::User user = userStorage->get( id );
	if( user.paired() )
	{
		adapterStorage->getAudio( settings.audioBackend )->removeUser( user );
	}
	user.inChat = false;
	if( !user.exists() )
	{
		userStorage->remove( id );
	}
}

void UseCases::changePlaybackDevice()
{
	Entity::Settings settings = settingsStorage->get();
	updatePlaybackDeviceToBackends( settings.audioBackend );
}

void UseCases::changePlaybackVolume()
{
	Entity::Settings settings = settingsStorage->get();
	updatePlaybackVolumeToBackends( settings.audioBackend );
}

void UseCases::showSettingsUi( QWidget *parent )
{
	Entity::Settings settings = settingsStorage->get();
	adapterStorage->getUi()->showSettingsUi( settings, parent );
}

void UseCases::saveSettings( const Entity::Settings &settings )
{
	Entity::Settings originalSettings = settingsStorage->get();
	settingsStorage->set( settings );
	if( settings.positioningEnabled )
	{
		if( originalSettings.audioBackend != settings.audioBackend )
		{
			adapterStorage->getAudio( originalSettings.audioBackend )->reset();

			updatePlaybackDeviceToBackends( settings.audioBackend );
			updatePlaybackVolumeToBackends( settings.audioBackend );

			adapterStorage->getAudio( settings.audioBackend )->positionCamera( cameraStorage->get() );
			foreach( Entity::User user, userStorage->getAll() )
			{
				if( user.paired() && user.hasPosition() )
				{
					adapterStorage->getAudio( settings.audioBackend )->positionUser( user );
				}
			}
		}
	}
	else
	{
		// positioningEnabled: true --> false ?
		if( originalSettings.positioningEnabled )
		{
			adapterStorage->getAudio( originalSettings.audioBackend )->reset();
		}
	}
}

void UseCases::updatePlaybackDeviceToBackends( int backend )
{
	auto deviceName = adapterStorage->getVoiceChat()->getPlaybackDeviceName();
	adapterStorage->getAudio( backend )->setPlaybackDeviceName( deviceName );
	adapterStorage->getTestAudio( backend )->setPlaybackDeviceName( deviceName );
}

void UseCases::updatePlaybackVolumeToBackends( int backend )
{
	auto volume = adapterStorage->getVoiceChat()->getPlaybackVolume();
	adapterStorage->getAudio( backend )->setPlaybackVolume( volume );
	adapterStorage->getTestAudio( backend )->setPlaybackVolume( volume );
}

}
