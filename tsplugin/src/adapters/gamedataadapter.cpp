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

#include "gamedataadapter.h"

namespace Adapter
{

GameDataAdapter::GameDataAdapter( Interfaces::GameDataDriver* driver, Interfaces::UseCaseFactory *useCaseFactory, QObject *parent )
	: QObject( parent ), useCaseFactory( useCaseFactory )
{
	connect( driver->qtObj(), SIGNAL(gameUserAdded(quint16)),
			 this, SLOT(onGameUserAdded(quint16)) );
	connect( driver->qtObj(), SIGNAL(gameUserRemoved(quint16)),
			 this, SLOT(onGameUserRemoved(quint16)) );
	connect( driver->qtObj(), SIGNAL(gameUserPositionChanged(quint16, Entity::Vector)),
			 this, SLOT(onGameUserPositionChanged(quint16, Entity::Vector)) );
	connect( driver->qtObj(), SIGNAL(gameCameraPositionChanged(Entity::Vector)),
			 this, SLOT(onGameCameraPositionChanged(Entity::Vector)) );
	connect( driver->qtObj(), SIGNAL(gameCameraDirectionChanged(Entity::Vector)),
			 this, SLOT(onGameCameraDirectionChanged(Entity::Vector)) );
}

void GameDataAdapter::onGameUserAdded( quint16 id )
{
	useCaseFactory->addGameUser( id );
}

void GameDataAdapter::onGameUserRemoved( quint16 id )
{
	useCaseFactory->removeGameUser( id );
}

void GameDataAdapter::onGameUserPositionChanged( quint16 id, const Entity::Vector &position )
{
	useCaseFactory->positionUser( id, position );
}

void GameDataAdapter::onGameCameraPositionChanged( const Entity::Vector &position )
{
	cameraPosition = position;
	if( isCameraValid() )
	{
		useCaseFactory->positionCamera( cameraPosition, cameraDirection );
	}
}

void GameDataAdapter::onGameCameraDirectionChanged( const Entity::Vector &direction )
{
	cameraDirection = direction;
	if( isCameraValid() )
	{
		useCaseFactory->positionCamera( cameraPosition, cameraDirection );
	}
}

bool GameDataAdapter::isCameraValid() const
{
	return cameraDirection != Entity::Vector();
}

}
