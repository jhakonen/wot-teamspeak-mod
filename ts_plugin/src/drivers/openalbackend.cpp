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

#include "openalbackend.h"
#include "../entities/vector.h"
#include "../entities/enums.h"
#include "../utils/logging.h"
#include "../utils/wavfile.h"
#include "../utils/async.h"
#include "../openal/openal.h"
#include "../openal/structures.h"

#include <AL/alext.h>

#include <QStandardPaths>
#include <QRegularExpression>
#include <QDir>
#include <QVector>
#include <QPointer>
#include <QSet>

#include <iostream>

namespace
{
QMutex mutex;

const int AUDIO_FREQUENCY = 44100;
const int SOURCE_ID_TEST = 1;
const int SOURCE_ID_USER = 1000;

QString getAppdataPath()
{
	QString targetPath = QStandardPaths::standardLocations( QStandardPaths::GenericDataLocation )[0];
	return targetPath.replace( QRegularExpression( "Local$" ), "Roaming" );
}

QString getOALHRTFPath()
{
	QString targetPath = getAppdataPath() + "/openal/hrtf";
	QDir().mkpath( targetPath );
	return QDir::cleanPath( targetPath );
}

ALfloat tsVolumeModifierToOALGain( float tsVolumeModifier )
{
	return 1.0 / ( pow( 2.0, tsVolumeModifier / -6.0 ) );
}

}

namespace Driver
{

class OpenALBackendPrivate
{
public:
	OpenALBackendPrivate()
		: isEnabled( false ), playbackVolume( 0 ), hrtfEnabled( false ), initNeeded( false )
	{
	}

	void writeSilence( short *samples, int sampleCount, int channels )
	{
		// write silence back to teamspeak
		int sampleDataLength = sampleCount * channels * 2;
		memset( samples, 0, sampleDataLength );
	}

	Entity::Vector switchHandness( const Entity::Vector &vector ) const
	{
		Entity::Vector result = vector;
		result.z = -result.z;
		return result;
	}

	OpenAL::OutputInfo getOutputInfo() const
	{
		return OpenAL::OutputInfo( playbackDeviceName, AUDIO_FREQUENCY, hrtfEnabled );
	}

	OpenAL::SourceInfo getUserSourceInfo( quint16 userId ) const
	{
		return OpenAL::SourceInfo( getOutputInfo(), SOURCE_ID_USER + userId, switchHandness( userPositions[userId] ), 0, false, true );
	}

	OpenAL::SourceInfo getTestSourceInfo() const
	{
		return OpenAL::SourceInfo( getOutputInfo(), SOURCE_ID_TEST, switchHandness( testSourcePosition ), 0, true, false );
	}

	OpenAL::ListenerInfo getListenerInfo() const
	{
		return OpenAL::ListenerInfo( getOutputInfo(),
										switchHandness( cameraForward ),
										switchHandness( cameraUp ),
										Entity::Vector(),
										switchHandness( cameraPosition ),
										tsVolumeModifierToOALGain( playbackVolume ) );
	}

public:
	QMap<quint16, Entity::Vector> userPositions;
	bool isEnabled;
	Entity::Vector cameraPosition;
	Entity::Vector cameraForward;
	Entity::Vector cameraUp;
	Entity::Vector testSourcePosition;
	QString playbackDeviceName;
	float playbackVolume;
	bool hrtfEnabled;
	bool initNeeded;
};

OpenALBackend::OpenALBackend( QObject *parent )
	: QObject( parent ), d_ptr( new OpenALBackendPrivate() )
{
}

OpenALBackend::~OpenALBackend()
{
	Q_D( OpenALBackend );
	delete d;
}

void OpenALBackend::setEnabled( bool enabled )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setEnabled(" << enabled << "), state: " << d->isEnabled;
	d->isEnabled = enabled;
}

bool OpenALBackend::isEnabled() const
{
	Q_D( const OpenALBackend );
	QMutexLocker locker( &mutex );
	return d->isEnabled;
}

void OpenALBackend::removeUser( quint16 id )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::removeUser(" << id << ")";
	if( d->userPositions.contains( id ) )
	{
		d->userPositions.remove( id );
	}
}

void OpenALBackend::positionUser( quint16 id, const Entity::Vector &position )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	//Log::debug() << "OpenALBackend::positionUser(" << id << ", " << position << ")";
	d->userPositions[id] = position;
}

void OpenALBackend::positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::positionCamera(" << position << ", " << forward << ", " << up << ")";
	d->cameraPosition = position;
	d->cameraForward = forward;
	d->cameraUp = up;

	try
	{
		OpenAL::updateListener( d->getListenerInfo() );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to position camera, reason: " << error.what();
	}
}

void OpenALBackend::setPlaybackDeviceName( const QString &name )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setPlaybackDeviceName('" << name << "')";
	d->playbackDeviceName = name;
}

void OpenALBackend::setPlaybackVolume( float volume )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setPlaybackVolume(" << volume << ")";
	d->playbackVolume = volume;

	try
	{
		OpenAL::updateListener( d->getListenerInfo() );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to change playback volume, reason: " << error.what();
	}
}

void OpenALBackend::setHrtfEnabled( bool enabled )
{
	Q_D( OpenALBackend );
	d->hrtfEnabled = enabled;
}

void OpenALBackend::setHrtfDataSet( const QString &name )
{
	Log::debug() << "OpenALBackend::setHrtfDataSet(): " << name;
	QFile hrtfFile( getOALHRTFPath() + QDir::separator() + "default-44100.mhr" );
	if( hrtfFile.exists() )
	{
		hrtfFile.setPermissions( hrtfFile.permissions() | QFile::WriteUser );
		hrtfFile.remove();
	}
	if( !QFile::copy( name, hrtfFile.fileName() ) )
	{
		Log::error() << "Failed to save HRTF data set '" << name << "'"
					 << " to path '" << QDir::toNativeSeparators( hrtfFile.fileName() ) << "'";
		return;
	}

	try
	{
		OpenAL::reset();
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to reset OpenAL, reason: " << error.what();
	}
}

QStringList OpenALBackend::getHrtfDataPaths() const
{
	QDir dir( ":/etc/hrtfs/" );
	QStringList paths;
	foreach( QString entry, dir.entryList( QStringList() << "*.mhr", QDir::Files ) )
	{
		paths.append( dir.filePath( entry ) );
	}
	return paths;
}

void OpenALBackend::playTestSound( const QString &filePath )
{
	Q_D( OpenALBackend );
	try
	{
		WavFile file( filePath );
		if( !file.open( WavFile::ReadOnly ) )
		{
			Log::error() << "Failed to open test sound file, reason: " << file.errorString();
			return;
		}
		QByteArray audioData = file.readAll();

		OpenAL::playAudio( d->getTestSourceInfo(),
						   OpenAL::AudioData(
							   file.getChannels(), file.getBitsPerSample(),
							   audioData.size(), file.getSampleRate(),
							   audioData.data() ) );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to start test sound playback, reason: " << error.what();
	}
}

void OpenALBackend::positionTestSound( const Entity::Vector &position )
{
	Q_D( OpenALBackend );
	d->testSourcePosition = position;
	try
	{
		OpenAL::updateSource( d->getTestSourceInfo() );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to position test sound, reason: " << error.what();
	}
}

void OpenALBackend::stopTestSound()
{
	Q_D( OpenALBackend );
	try
	{
		OpenAL::stopAudio( d->getTestSourceInfo() );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to stop test sound, reason: " << error.what();
	}
}

void OpenALBackend::onEditPlaybackVoiceDataEvent( quint16 id, short *samples, int sampleCount, int channels )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	if( d->userPositions.contains( id ) )
	{
		try
		{
			OpenAL::playAudio( d->getUserSourceInfo( id ),
							   OpenAL::AudioData(
								   channels,
								   sizeof(short) * 8,
								   channels * sampleCount * sizeof(short),
								   48000,
								   samples ) );
			d->writeSilence( samples, sampleCount, channels );
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to feed audio data to OpenAL, reason: " << error.what();
		}
	}
}

}
