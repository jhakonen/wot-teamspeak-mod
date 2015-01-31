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

#pragma once

#include "../interfaces/adapters.h"
#include "../interfaces/usecasefactory.h"
#include "../interfaces/drivers.h"
#include "../entities/vector.h"

namespace Adapter
{

class GameDataAdapter : public QObject, public Interfaces::GameDataAdapter
{
	Q_OBJECT

public:
	GameDataAdapter( Interfaces::GameDataDriver* driver, Interfaces::UseCaseFactory *useCaseFactory, QObject *parent );

private slots:
	void onGameUserAdded( quint16 id );
	void onGameUserRemoved( quint16 id );
	void onGameUserPositionChanged( quint16 id, const Entity::Vector &position );
	void onGameCameraPositionChanged( const Entity::Vector &position );
	void onGameCameraDirectionChanged( const Entity::Vector &direction );

private:
	bool isCameraValid() const;

private:
	Interfaces::UseCaseFactory *useCaseFactory;
	Entity::Vector cameraPosition;
	Entity::Vector cameraDirection;
};

}
