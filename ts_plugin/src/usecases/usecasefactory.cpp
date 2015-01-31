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

#include "usecasefactory.h"
#include "usecases.h"

namespace UseCase
{

UseCaseFactory::UseCaseFactory( QObject *parent )
	: QObject( parent )
{
}

void UseCaseFactory::applicationInitialize()
{
	createUseCases()->applicationInitialize();
}

void UseCaseFactory::positionUser( quint16 id, const Entity::Vector& position )
{
	createUseCases()->positionUser( id, position );
}

void UseCaseFactory::positionCamera( const Entity::Vector& position, const Entity::Vector& direction )
{
	createUseCases()->positionCamera( position, direction );
}

void UseCaseFactory::addGameUser( quint16 id )
{
	createUseCases()->addGameUser( id );
}

void UseCaseFactory::removeGameUser( quint16 id )
{
	createUseCases()->removeGameUser( id );
}

void UseCaseFactory::addChatUser( quint16 id )
{
	createUseCases()->addChatUser( id );
}

void UseCaseFactory::removeChatUser( quint16 id )
{
	createUseCases()->removeChatUser( id );
}

void UseCaseFactory::changePlaybackDevice()
{
	createUseCases()->changePlaybackDevice();
}

void UseCaseFactory::changePlaybackVolume()
{
	createUseCases()->changePlaybackVolume();
}

void UseCaseFactory::showSettingsUi( QWidget *parent )
{
	createUseCases()->showSettingsUi( parent );
}

void UseCaseFactory::saveSettings( const Entity::Settings &settings )
{
	createUseCases()->saveSettings( settings );
}

void UseCaseFactory::playTestAudioWithSettings( const Entity::Settings &settings )
{
	createUseCases()->playTestAudioWithSettings( settings );
}

UseCases *UseCaseFactory::createUseCases() const
{
	UseCases* cases = new UseCases();
	cases->adapterStorage = adapterStorage;
	cases->cameraStorage = cameraStorage;
	cases->userStorage = userStorage;
	cases->settingsStorage = settingsStorage;
	return cases;
}

}
