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
	return cameraPosition != Entity::Vector() && cameraDirection != Entity::Vector();
}

}
