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
#include "../libs/openal.h"
#include "../utils/logging.h"

#include <AL/alext.h>

#include <QStandardPaths>
#include <QRegularExpression>
#include <QDir>

#include <iostream>

namespace
{
QMutex mutex;

const int AUDIO_FREQUENCY = 48000;

QString getAppdataPath()
{
	QString targetPath = QStandardPaths::standardLocations( QStandardPaths::GenericDataLocation )[0];
	return targetPath.replace( QRegularExpression( "Local$" ), "Roaming" );
}

QString getOALHRTFPath()
{
	QString targetPath = getAppdataPath() + "/openal/hrtf";
	QDir().mkpath( targetPath );
	return QDir::cleanPath( ( targetPath + "/default-%1.mhr" ).arg( AUDIO_FREQUENCY ) );
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
		: isEnabled( false ), playbackVolume( 0 ), device( NULL ), context( NULL )
	{
	}

	void enableAL()
	{
		Log::info() << "Enabling OpenALBackend";
		QString hrtfInstallPath = getOALHRTFPath();
		if( !QFile::exists( hrtfInstallPath ) )
		{
			if( !QFile::copy( QString(":/etc/default-%1.mhr").arg( AUDIO_FREQUENCY ), hrtfInstallPath ) )
			{
				Log::error() << "Failed to install default HRTF file to " << hrtfInstallPath;
			}
		}

		ALCint attrs[6] = { 0 };
		attrs[0] = ALC_FORMAT_TYPE_SOFT;
		attrs[1] = ALC_SHORT_SOFT;
		attrs[2] = ALC_FREQUENCY;
		attrs[3] = AUDIO_FREQUENCY;
		QByteArray deviceNameBytes = playbackDeviceName.toUtf8();

		Log::info() << "OpenALBackend opens device: " << playbackDeviceName;
		try
		{
			OpenAL::loadLib();
			device = OpenAL::alcOpenDevice( deviceNameBytes.data() );
			context = OpenAL::alcCreateContext( device, attrs );
			OpenAL::alcMakeContextCurrent( context );
		}
		catch( ... )
		{
			disableAL();
			throw;
		}

		OpenAL::alListener3f( AL_VELOCITY, 0, 0, 0 );
		OpenAL::alListenerf( AL_GAIN, tsVolumeModifierToOALGain( playbackVolume ) );
		updateCameraToAL();
		foreach( quint16 id, userPositions.keys() )
		{
			updateUserToAL( id );
		}
	}

	void disableAL()
	{
		Log::info() << "Disabling OpenALBackend";
		userSources.clear();
		if( context )
		{
			OpenAL::alcMakeContextCurrent( NULL );
			OpenAL::alcDestroyContext( context );
			context = NULL;
		}
		if( device )
		{
			OpenAL::alcCloseDevice( device );
			device = NULL;
		}
	}

	void updateUserToAL( quint16 id )
	{
		if( userPositions.contains( id ) )
		{
			Entity::Vector position = userPositions[id];
			if( !userSources.contains( id ) )
			{
				ALuint source = 0;
				OpenAL::alGenSources( 1, &source );
				userSources[id] = source;
				OpenAL::alSourcei( source, AL_SOURCE_RELATIVE, AL_FALSE );
				OpenAL::alSourcef( source, AL_ROLLOFF_FACTOR, 0 );
			}
			OpenAL::alSource3f( userSources[id], AL_POSITION, position.x, position.y, -position.z );
		}
		else if( userSources.contains( id ) )
		{
			Log::debug() << "alDeleteSources(): " << userSources[id];
			OpenAL::alDeleteSources( 1, &userSources[id] );
			userSources.remove( id );
		}
	}

	void updateCameraToAL()
	{
		ALfloat orientation[] = { cameraForward.x, cameraForward.y, -cameraForward.z, cameraUp.x, cameraUp.y, -cameraUp.z };
		OpenAL::alListener3f( AL_POSITION, cameraPosition.x, cameraPosition.y, -cameraPosition.z );
		OpenAL::alListenerfv( AL_ORIENTATION, orientation );
	}

	void changeALPlaybackDevice()
	{
		if( isEnabled )
		{
			try
			{
				disableAL();
			}
			catch( const OpenAL::Failure &error )
			{
				Log::warning() << "Failed to disable OpenAL, reason: " << error.what();
			}
			try
			{
				enableAL();
			}
			catch( const OpenAL::Failure &error )
			{
				Log::error() << "Failed to enable OpenAL, reason: " << error.what();
				isEnabled = false;
			}
		}
	}

	void changeALPlaybackVolume()
	{
		if( isEnabled )
		{
			OpenAL::alListenerf( AL_GAIN, tsVolumeModifierToOALGain( playbackVolume ) );
		}
	}

	bool feedUserAudioToAL( quint16 id, const short *samples, int sampleCount, int channels )
	{
		if( !isEnabled )
		{
			return false;
		}
		if( !userSources.contains( id ) )
		{
			return false;
		}
		if( channels != 1 )
		{
			// accept only mono source audio
			return false;
		}

		ALuint source = userSources[id];
		int sampleDataLength = sampleCount * channels * 2;
		ALint state;

		try
		{
			freeProcessedAudioData( source );
		}
		catch( const OpenAL::Failure &error )
		{
			Log::warning() << "Failed to free processed data, reason: " << error.what();
		}
		OpenAL::alGetSourcei( source, AL_SOURCE_STATE, &state );
		try
		{
			// delay start of playback a bit so that we don't starve the playback device
			if( state != AL_PLAYING )
			{
				short silence[AUDIO_FREQUENCY / 10] = {}; // 0.1 seconds worth of silence
				queueAudioData( source, silence, sizeof( silence ) );
			}
		}
		catch( const OpenAL::Failure &error )
		{
			Log::warning() << "Failed to queue audio delay, reason: " << error.what();
		}
		queueAudioData( source, samples, sampleDataLength );
		if( state != AL_PLAYING )
		{
			OpenAL::alSourcePlay( source );
		}
		return true;
	}

	void freeProcessedAudioData( ALuint source )
	{
		ALint processedCount = 0;
		OpenAL::alGetSourcei( source, AL_BUFFERS_PROCESSED, &processedCount );
		if( processedCount > 0 )
		{
			QScopedArrayPointer<ALuint> buffers( new ALuint[processedCount] );
			OpenAL::alSourceUnqueueBuffers( source, processedCount, buffers.data() );
			OpenAL::alDeleteBuffers( processedCount, buffers.data() );
		}
	}

	void queueAudioData( ALuint source, const short *data, int length )
	{
		ALuint buffer;
		OpenAL::alGenBuffers( 1, &buffer );
		OpenAL::alBufferData( buffer, AL_FORMAT_MONO16, data, length, AUDIO_FREQUENCY );
		OpenAL::alSourceQueueBuffers( source, 1, &buffer );
	}

	void writeSilence( short *samples, int sampleCount, int channels )
	{
		// write silence back to teamspeak
		int sampleDataLength = sampleCount * channels * 2;
		memset( samples, 0, sampleDataLength );
	}

	void changeALContext()
	{
		if( isEnabled && context )
		{
			OpenAL::alcMakeContextCurrent( context );
		}
	}

public:
	QMap<quint16, Entity::Vector> userPositions;
	QMap<quint16, ALuint> userSources;
	bool isEnabled;
	Entity::Vector cameraPosition;
	Entity::Vector cameraForward;
	Entity::Vector cameraUp;
	QString playbackDeviceName;
	float playbackVolume;
	ALCdevice *device;
	ALCcontext *context;
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
	try
	{
		if( enabled && !d->isEnabled )
		{
			d->enableAL();
		}
		else if( !enabled && d->isEnabled )
		{
			d->disableAL();
		}
		d->isEnabled = enabled;
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Enabling/disabling OpenAL backend failed, reason: " << error.what();
	}
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
	try
	{
		d->changeALContext();
		d->updateUserToAL( id );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to remove user, reason: " << error.what();
	}
}

void OpenALBackend::removeAllUsers()
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	QList<quint16> existingUsers = d->userPositions.keys();
	d->userPositions.clear();
	try
	{
		d->changeALContext();
		foreach( quint16 id, existingUsers )
		{
			d->updateUserToAL( id );
		}
	}
	catch( const OpenAL::Failure &error )
	{
		std::cout << "Failed to remove users, reason: " << error.what().toStdString() << std::endl;
	}
}

void OpenALBackend::positionUser( quint16 id, const Entity::Vector &position )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	//Log::debug() << "OpenALBackend::positionUser(" << id << ", " << position << ")";
	d->userPositions[id] = position;
	try
	{
		d->changeALContext();
		d->updateUserToAL( id );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to position user, reason: " << error.what();
	}
}

void OpenALBackend::positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::positionCamera(" << position << ", " << forward << ", " << up << ")";
	d->cameraPosition = position;
	d->cameraForward = forward;
	d->cameraUp = up;
	if( d->isEnabled )
	{
		try
		{
			d->changeALContext();
			d->updateCameraToAL();
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to position camera, reason: " << error.what();
		}
	}
}

void OpenALBackend::setPlaybackDeviceName( const QString &name )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setPlaybackDeviceName('" << name << "')";
	if( d->playbackDeviceName != name )
	{
		d->playbackDeviceName = name;
		try
		{
			d->changeALContext();
			d->changeALPlaybackDevice();
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to change playback device, reason: " << error.what();
		}
	}
}

void OpenALBackend::setPlaybackVolume( float volume )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setPlaybackVolume(" << volume << ")";
	d->playbackVolume = volume;
	try
	{
		d->changeALContext();
		d->changeALPlaybackVolume();
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to change playback volume, reason: " << error.what();
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
			d->changeALContext();
			if( d->feedUserAudioToAL( id, samples, sampleCount, channels ) )
			{
				d->writeSilence( samples, sampleCount, channels );
			}
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to feed audio data to OpenAL, reason: " << error.what();
		}
	}
}

}
