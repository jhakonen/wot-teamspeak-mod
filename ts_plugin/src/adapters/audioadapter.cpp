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
#include "../utils/positionrotator.h"
#include "../utils/logging.h"

#include <QTimer>
#include <QStandardPaths>
#include <QDir>
#include <QFile>

#include <cmath>

namespace Adapter
{

AudioAdapter::AudioAdapter( Interfaces::AudioDriver *driver, QObject *parent )
	: QObject( parent ), driver( driver ), rotator( new PositionRotator( this ) )
{
	connect( rotator, SIGNAL(started()), this, SLOT(onStartTestSound()) );
	connect( rotator, SIGNAL(positionChanged(Entity::Vector)), this, SLOT(onPositionTestSound(Entity::Vector)) );
	connect( rotator, SIGNAL(finished()), this, SLOT(onFinishTestSound()) );
}

void AudioAdapter::removeUser( const Entity::User &user )
{
	userIds.remove( user.id );
	driver->removeUser( user.id );
}

void AudioAdapter::positionUser( const Entity::User &user )
{
	userIds.insert( user.id );
	driver->positionUser( user.id, user.position );
}

void AudioAdapter::positionCamera( const Entity::Camera &camera )
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

void AudioAdapter::setPlaybackDeviceName( const QString &name )
{
	driver->setPlaybackDeviceName( name );
}

void AudioAdapter::setPlaybackVolume( float volume )
{
	driver->setPlaybackVolume( volume );
}

void AudioAdapter::setEnabled( bool enabled )
{
	if( enabled && !driver->isEnabled() )
	{
		driver->setEnabled( true );
	}
	else if( !enabled && driver->isEnabled() )
	{
		driver->setEnabled( false );
	}
}

void AudioAdapter::setHrtfEnabled( bool enabled )
{
	driver->setHrtfEnabled( enabled );
}

void AudioAdapter::setHrtfDataSet( const QString &name )
{
	driver->setHrtfDataSet( name );
}

void AudioAdapter::playTestSound( Entity::RotateMode mode )
{
	rotator->start( mode );
}

void AudioAdapter::onStartTestSound()
{
	QString tempPath = QStandardPaths::writableLocation( QStandardPaths::TempLocation ) + "/TessuMod";
	if( !QDir().mkpath( tempPath ) )
	{
		Log::error() << "Failed to create folder for test sound: " + QDir::toNativeSeparators( tempPath );
		return;
	}

	QString testSoundPath = tempPath + "/testsound.wav";
	QFile testSoundFile( testSoundPath );
	testSoundFile.setPermissions( testSoundFile.permissions() | QFile::WriteUser );
	testSoundFile.remove( testSoundPath );

	if( !QFile::copy( ":/audio/testsound.wav", testSoundPath ) )
	{
		Log::error() << "Failed to save test sound file to path: " + QDir::toNativeSeparators( testSoundPath );
		return;
	}

	driver->playTestSound( testSoundPath );
}

void AudioAdapter::onPositionTestSound( const Entity::Vector &position )
{
	driver->positionTestSound( position );
}

void AudioAdapter::onFinishTestSound()
{
	driver->stopTestSound();
}

}
