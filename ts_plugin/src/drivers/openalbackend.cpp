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
#include "../libs/oallibrary.h"
#include "../utils/logging.h"
#include "../utils/wavfile.h"

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
		: isEnabled( false ), playbackVolume( 0 ), hrtfEnabled( false )
	{
	}

	void enableAL()
	{
		if( oalContext )
		{
			return;
		}
		Log::info() << "Enabling OpenALBackend";
		QString hrtfInstallPath = getOALHRTFPath();
		if( !QFile::exists( hrtfInstallPath ) )
		{
			if( !QFile::copy( QString(":/etc/default-%1.mhr").arg( AUDIO_FREQUENCY ), hrtfInstallPath ) )
			{
				Log::error() << "Failed to install default HRTF file to " << hrtfInstallPath;
			}
		}

		Log::info() << "OpenALBackend opens device: " << playbackDeviceName;
		try
		{
			if( !oalLibrary )
			{
				oalLibrary = new OALLibrary();
			}
			auto device = oalLibrary->createDevice( playbackDeviceName );
			oalContext = device->createContext( hrtfEnabled );
		}
		catch( ... )
		{
			disableAL();
			throw;
		}

		oalContext->setListenerVelocity( 0, 0, 0 );
		oalContext->setListenerGain( tsVolumeModifierToOALGain( playbackVolume ) );
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
		delete oalLibrary;
	}

	void updateUserToAL( quint16 id )
	{
		if( userPositions.contains( id ) )
		{
			Entity::Vector position = userPositions[id];
			if( oalContext )
			{
				if( !userSources[id] )
				{
					userSources[id] = oalContext->createSource();
					userSources[id]->setRelative( false );
					userSources[id]->setRolloffFactor( 0 );
				}
				userSources[id]->setPosition( position.x, position.y, -position.z );
			}
		}
		else if( userSources.contains( id ) )
		{
			delete userSources.take( id );
		}
	}

	void updateCameraToAL()
	{
		if( oalContext )
		{
			oalContext->setListenerOrientation( cameraForward.x, cameraForward.y, -cameraForward.z, cameraUp.x, cameraUp.y, -cameraUp.z );
			oalContext->setListenerPosition( cameraPosition.x, cameraPosition.y, -cameraPosition.z );
		}
	}

	void restartAL()
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

		int sampleDataLength = sampleCount * channels * 2;

		if( userSources[id] )
		{
			bool isPlaying = userSources[id]->isPlaying();
			try
			{
				if( !isPlaying )
				{
					// delay start of playback a bit so that we don't starve the playback device
					short silence[AUDIO_FREQUENCY / 10] = {}; // 0.1 seconds worth of silence
					userSources[id]->queueAudioData( AL_FORMAT_MONO16, silence, sizeof( silence ), AUDIO_FREQUENCY );
				}
			}
			catch( const OpenAL::Failure &error )
			{
				Log::warning() << "Failed to queue audio delay, reason: " << error.what();
			}

			userSources[id]->queueAudioData( AL_FORMAT_MONO16, samples, sampleDataLength, AUDIO_FREQUENCY );
			if( !isPlaying )
			{
				userSources[id]->play();
			}
		}
		return true;
	}

	void writeSilence( short *samples, int sampleCount, int channels )
	{
		// write silence back to teamspeak
		int sampleDataLength = sampleCount * channels * 2;
		memset( samples, 0, sampleDataLength );
	}

	ALenum getALFormat( quint16 channels, quint16 samples ) const
	{
		switch( channels )
		{
		case 1:
			switch( samples )
			{
			case 8:
				return AL_MONO8_SOFT;
			case 16:
				return AL_MONO16_SOFT;
			default:
				throw OpenAL::Failure( "Unsupported bits per sample value" );
			}

		case 2:
			switch( samples )
			{
			case 8:
				return AL_STEREO8_SOFT;
			case 16:
				return AL_STEREO16_SOFT;
			default:
				throw OpenAL::Failure( "Unsupported bits per sample value" );
			}

		default:
			throw OpenAL::Failure( "Unsupported channel count" );
		}
	}

	quint32 getDefaultFrequency() const
	{
		if( oalContext )
		{
			return oalContext->getFrequency();
		}
		else
		{
			OALLibrary library;
			return library.createDevice( playbackDeviceName )->createContext( false )->getFrequency();
		}
	}

	QStringList getHrtfFilePaths() const
	{
		QStringList paths = getHrtfFilePaths( QDir( ":/etc/hrtfs/" ) );
		paths.append( getHrtfFilePaths( getOALHRTFPath() ) );
		return paths;
	}

	QStringList getHrtfFilePaths( const QDir &dir ) const
	{
		QStringList paths;
		foreach( QString entry, dir.entryList( QStringList() << "*.mhr", QDir::Files ) )
		{
			if( !entry.contains( "default", Qt::CaseInsensitive ) )
			{
				paths.append( dir.filePath( entry ) );
			}
		}
		return paths;
	}

public:
	QPointer<OALLibrary> oalLibrary;
	QPointer<OALContext> oalContext;
	QMap<quint16, Entity::Vector> userPositions;
	QMap<quint16, QPointer<OALSource>> userSources;
	QPointer<OALSource> testSoundSource;
	bool isEnabled;
	Entity::Vector cameraPosition;
	Entity::Vector cameraForward;
	Entity::Vector cameraUp;
	QString playbackDeviceName;
	float playbackVolume;
	bool hrtfEnabled;
};

OpenALBackend::OpenALBackend( QObject *parent )
	: QObject( parent ), d_ptr( new OpenALBackendPrivate() )
{
}

OpenALBackend::~OpenALBackend()
{
	Q_D( OpenALBackend );
	d->disableAL();
	delete d;
}

void OpenALBackend::setEnabled( bool enabled )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setEnabled(" << enabled << "), state: " << d->isEnabled;
	try
	{
		if( enabled )
		{
			d->enableAL();
		}
		else
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
		d->updateUserToAL( id );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to remove user, reason: " << error.what();
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

	try
	{
		d->updateCameraToAL();
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

	if( d->playbackDeviceName == name )
	{
		return;
	}
	d->playbackDeviceName = name;

	try
	{
		d->restartAL();
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to change playback device, reason: " << error.what();
	}
}

void OpenALBackend::setPlaybackVolume( float volume )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	Log::debug() << "OpenALBackend::setPlaybackVolume(" << volume << ")";
	d->playbackVolume = volume;

	if( !d->oalContext )
	{
		return;
	}

	try
	{
		d->oalContext->setListenerGain( tsVolumeModifierToOALGain( volume ) );
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to change playback volume, reason: " << error.what();
	}
}

void OpenALBackend::setHrtfEnabled( bool enabled )
{
	Q_D( OpenALBackend );

	if( d->hrtfEnabled == enabled )
	{
		return;
	}
	d->hrtfEnabled = enabled;

	try
	{
		d->restartAL();
	}
	catch( const OpenAL::Failure &error )
	{
		Log::error() << "Failed to change HRTF state, reason: " << error.what();
	}
}

void OpenALBackend::setHrtfDataSet( const QString &name )
{
	// TODO
}

QStringList OpenALBackend::getHrtfDataPaths() const
{
	Q_D( const OpenALBackend );
	quint32 frequency = d->getDefaultFrequency();
	QString frequencyStr = QString::number( frequency );
	QSet<QString> pathsSet;
	foreach( QString path, d->getHrtfFilePaths() )
	{
		if( path.contains( frequencyStr ) )
		{
			pathsSet.insert( path.replace( frequencyStr, "%r" ) );
		}
	}
	return pathsSet.toList();
}

void OpenALBackend::playTestSound( const QString &filePath )
{
	Q_D( OpenALBackend );
	if( d->oalContext )
	{
		try
		{
			delete d->testSoundSource;
			d->testSoundSource = d->oalContext->createSource();
			d->testSoundSource->setRelative( true );
			d->testSoundSource->setRolloffFactor( 0 );
			d->testSoundSource->setLooping( true );

			WavFile file( filePath );
			if( !file.open( WavFile::ReadOnly ) )
			{
				Log::error() << "Failed to open test sound file, reason: " << file.errorString();
				return;
			}
			QByteArray audioData = file.readAll();

			d->testSoundSource->playbackAudioData( d->getALFormat( file.getChannels(), file.getBitsPerSample() ),
												   audioData.data(),
												   audioData.size(),
												   file.getSampleRate() );
			d->testSoundSource->play();
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to start test sound playback, reason: " << error.what();
		}
	}
}

void OpenALBackend::positionTestSound( const Entity::Vector &position )
{
	Q_D( OpenALBackend );
	if( d->testSoundSource )
	{
		try
		{
			d->testSoundSource->setPosition( position.x, position.y, -position.z );
		}
		catch( const OpenAL::Failure &error )
		{
			Log::error() << "Failed to position test sound, reason: " << error.what();
		}
	}
}

void OpenALBackend::stopTestSound()
{
	Q_D( OpenALBackend );
	delete d->testSoundSource;
}

void OpenALBackend::onEditPlaybackVoiceDataEvent( quint16 id, short *samples, int sampleCount, int channels )
{
	Q_D( OpenALBackend );
	QMutexLocker locker( &mutex );
	if( d->userPositions.contains( id ) )
	{
		try
		{
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
