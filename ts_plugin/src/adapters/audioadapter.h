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
#include <QObject>
#include <QSet>

namespace Interfaces
{
class AudioDriver;
}

namespace Adapter
{

class AudioAdapter : public QObject, public Interfaces::AudioAdapter
{
	Q_OBJECT

public:
	AudioAdapter( Interfaces::AudioDriver* driver, QObject *parent );

	void positionUser( const Entity::User &user );
	void removeUser( const Entity::User &user );
	void positionCamera( const Entity::Camera &camera );

	void setPlaybackDeviceName( const QString &name );
	void setPlaybackVolume( float volume );

	void reset();

private:
	Interfaces::AudioDriver* driver;
	QSet<quint16> userIds;
};

}
