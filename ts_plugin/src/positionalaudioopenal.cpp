/*
 * TessuMod: Mod for integrating TeamSpeak into World of Tanks
 * Copyright (C) 2014  Janne Hakonen
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

#include "positionalaudioopenal.h"
#include "ts_helpers.h"
#include "openal_helpers.h"

#include <iostream>
#include <cmath>
#include <public_errors.h>
#include <QStandardPaths>
#include <QRegularExpression>
#include <QDir>
#include <QTimer>
#include <QThread>
#include <QMutexLocker>
#include <QLibrary>

namespace {

const int AUDIO_FREQUENCY = 48000;

}

PositionalAudioOpenAL::PositionalAudioOpenAL( const TS3Functions ts3Interface, QObject *parent )
	: ModuleBase( parent ), ts3Interface( ts3Interface ),
	  clientSources( deleteOALSource ), device( NULL ), context( NULL ),
	  checkTimer( new QTimer( this ) ), isEnabled( false )
{
	checkTimer->setInterval( 3000 );
	checkTimer->setSingleShot( false );
	connect( checkTimer, SIGNAL(timeout()), this, SLOT(onCheckTimeout()) );
}

PositionalAudioOpenAL::~PositionalAudioOpenAL()
{
	clientPositions.clear();
	clientSources.clear();
	disable();
}

void PositionalAudioOpenAL::init()
{
	QString configInstallPath = getOALConfigPath();
	if( !QFile::exists( configInstallPath ) )
	{
		if( !QFile::copy( ":/etc/alsoft.ini", configInstallPath ) )
		{
			std::cout << "Failed to install config file to " << configInstallPath.toStdString() << std::endl;
		}
	}

	QString hrtfInstallPath = getOALHRTFPath();
	if( !QFile::exists( hrtfInstallPath ) )
	{
		if( !QFile::copy( QString(":/etc/default-%1.mhr").arg( AUDIO_FREQUENCY ), hrtfInstallPath ) )
		{
			std::cout << "Failed to install default HRTF file to " << hrtfInstallPath.toStdString() << std::endl;
		}
	}

	previousDeviceName = getTSPlaybackDeviceName();
	try
	{
		OpenAL::loadLib();
	}
	catch( const OpenAL::LibLoadFailure &e )
	{
		std::cout << e.what().toStdString() << std::endl;
	}
}

int PositionalAudioOpenAL::getAudioBackend() const
{
	return OpenALBackend;
}

void PositionalAudioOpenAL::onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber )
{
	Q_UNUSED( errorNumber );
	if( getServerConnectionHandlerID() != serverConnectionHandlerID )
	{
		return;
	}
	if( STATUS_DISCONNECTED == newStatus )
	{
		foreach( anyID clientID, clientsInChannel )
		{
			onClientLeftMyChannel( clientID );
		}
		clientsInChannel.clear();
	}
	if( STATUS_CONNECTION_ESTABLISHED == newStatus )
	{
		foreach( anyID clientID, getMyChannelClients() )
		{
			onClientEnterMyChannel( clientID );
			clientsInChannel.insert( clientID );
		}
	}
}

void PositionalAudioOpenAL::onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage )
{
	Q_UNUSED( visibility );
	Q_UNUSED( moveMessage );

	if( getServerConnectionHandlerID() != serverConnectionHandlerID )
	{
		return;
	}
	// I moved to a new channel
	if( getMyClientID() == clientID )
	{
		std::cout << "I moved to new channel" << std::endl;
		foreach( anyID clientID, clientsInChannel )
		{
			onClientLeftMyChannel( clientID );
		}
		clientsInChannel.clear();
		foreach( anyID clientID, getMyChannelClients() )
		{
			onClientEnterMyChannel( clientID );
			clientsInChannel.insert( clientID );
		}
		return;
	}
	// someone else moved to my channel
	else if( getMyChannelID() == newChannelID )
	{
		std::cout << "Client " << clientID << " entered my channel" << std::endl;
		onClientEnterMyChannel( clientID );
		clientsInChannel.insert( clientID );
	}
	// someone else moved away from my channel
	else if( getMyChannelID() == oldChannelID )
	{
		std::cout << "Client " << clientID << " left my channel" << std::endl;
		clientsInChannel.remove( clientID );
		onClientLeftMyChannel( clientID );
	}
}

void PositionalAudioOpenAL::onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short *samples, int sampleCount, int channels )
{
	if( !isEnabled )
	{
		return;
	}
	if( getServerConnectionHandlerID() != serverConnectionHandlerID )
	{
		return;
	}
	if( !clientSources.contains( clientID ) )
	{
		return;
	}

	ALuint source = clientSources[clientID];
	ALint state;
	ALuint buffer;
	int sampleDataLength = sampleCount * channels * 2;

	deleteOALProcessedSourceBuffers( source );

	OpenAL::alGetSourcei( source, AL_SOURCE_STATE, &state );
	if( !isOALOk() )
	{
		std::cout << "Failed to get source state" << std::endl;
	}
	// delay start of playback a bit so that we don't starve the playback device
	if( state != AL_PLAYING )
	{
		OpenAL::alGenBuffers( 1, &buffer );
		if( isOALOk() )
		{
			short silence[AUDIO_FREQUENCY / 10] = {}; // 0.1 seconds worth of silence
			OpenAL::alBufferData( buffer, AL_FORMAT_MONO16, silence, sizeof(silence), AUDIO_FREQUENCY );
			if( isOALOk() )
			{
				OpenAL::alSourceQueueBuffers( source, 1, &buffer );
				if( !isOALOk() )
				{
					std::cout << "Failed to queue silence buffer" << std::endl;
				}
			}
			else
			{
				std::cout << "Failed to buffer silence" << std::endl;
			}
		}
		else
		{
			std::cout << "Failed to generate silence buffer" << std::endl;
		}
	}

	OpenAL::alGenBuffers( 1, &buffer );
	if( isOALOk() )
	{
		OpenAL::alBufferData( buffer, AL_FORMAT_MONO16, samples, sampleDataLength, AUDIO_FREQUENCY );
		if( isOALOk() )
		{
			OpenAL::alSourceQueueBuffers( source, 1, &buffer );
			if( isOALOk() )
			{
				if( state != AL_PLAYING )
				{
					OpenAL::alSourcePlay( source );
					if( !isOALOk() )
					{
						std::cout << "Failed to start playback" << std::endl;
					}
				}
				// write silence back to teamspeak
				memset( samples, 0, sampleDataLength );
			}
			else
			{
				std::cout << "Failed to queue buffer" << std::endl;
			}
		}
		else
		{
			std::cout << "Failed to buffer data" << std::endl;
		}
	}
	else
	{
		std::cout << "Failed to generate buffer" << std::endl;
	}
}

void PositionalAudioOpenAL::enable()
{
	if( isEnabled )
	{
		return;
	}

	ALCint attrs[6] = { 0 };
	attrs[0] = ALC_FORMAT_TYPE_SOFT;
	attrs[1] = ALC_SHORT_SOFT;
	attrs[2] = ALC_FREQUENCY;
	attrs[3] = AUDIO_FREQUENCY;

	QString deviceName = getTSPlaybackDeviceName();
	QByteArray deviceNameBytes = deviceName.toUtf8();
	device = OpenAL::alcOpenDevice( deviceNameBytes.data() );
	if( !isOALContextOk( device ) )
	{
		std::cout << "OpenAL failed to open device '" << deviceName.toStdString() << "' for playback!" << std::endl;
		return;
	}

	context = OpenAL::alcCreateContext( device, attrs );
	if( !isOALContextOk( device ) )
	{
		std::cout << "Failed to create OpenAL audio context" << std::endl;
		disable();
		return;
	}

	OpenAL::alcMakeContextCurrent( context );
	if( !isOALContextOk( device ) )
	{
		std::cout << "Failed to change OpenAL audio context" << std::endl;
		disable();
		return;
	}

	OpenAL::alListener3f( AL_POSITION, 0.0f, 0.0f, 0.0f );
	if( !isOALOk() )
	{
		std::cout << "Failed to set listener position" << std::endl;
	}

	OpenAL::alListener3f( AL_VELOCITY, 0.0f, 0.0f, 0.0f );
	if( !isOALOk() )
	{
		std::cout << "Failed to set listener velocity" << std::endl;
	}

	foreach( anyID clientID, clientsInChannel )
	{
		clientSources[clientID] = createOALSource();
	}

	checkTimer->start();
	isEnabled = true;
}

void PositionalAudioOpenAL::disable()
{
	if( !isEnabled )
	{
		return;
	}

	clientSources.clear();

	if( context )
	{
		OpenAL::alcMakeContextCurrent( NULL );
		OpenAL::alcDestroyContext( context );
		context = 0;
	}
	if( device )
	{
		OpenAL::alcCloseDevice( device );
		device = 0;
	}

	checkTimer->stop();
	isEnabled = false;
}

void PositionalAudioOpenAL::onCameraPositionChanged( TS3_VECTOR position )
{
	if( isEnabled )
	{
		OpenAL::alListener3f( AL_POSITION, position.x, position.y, -position.z );
		if( !isOALOk() )
		{
			std::cout << "Failed to set listener position" << std::endl;
		}
	}
}

void PositionalAudioOpenAL::onCameraDirectionChanged( TS3_VECTOR direction )
{
	if( isEnabled )
	{
		// cannot calculate up-vector if both x and z are zero
		if( direction.x == 0 && direction.z == 0 )
		{
			return;
		}

		TS3_VECTOR up = toUnitVector( crossProduct( direction, createVector( direction.z, 0, -direction.x ) ) );
		std::cout << "onCameraDirectionChanged() :: direction: " << direction << ", up: " << up << std::endl;
		ALfloat orientation[] = { direction.x, direction.y, -direction.z, up.x, up.y, -up.z };
		OpenAL::alListenerfv( AL_ORIENTATION, orientation );
		if( !isOALOk() )
		{
			std::cout << "Failed to set listener orientation" << std::endl;
		}
	}
}

void PositionalAudioOpenAL::onClientAdded( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		std::cout << "client added" << std::endl;
		clientPositions[clientID] = position;
		if( isEnabled && clientSources.contains( clientID ) )
		{
			setSourcePosition( clientSources[clientID], position );
		}
	}
}

void PositionalAudioOpenAL::onClientPositionChanged( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		//std::cout << "position changed: " << position << std::endl;
		clientPositions[clientID] = position;
		if( isEnabled && clientSources.contains( clientID ) )
		{
			setSourcePosition( clientSources[clientID], position );
		}
	}
}

void PositionalAudioOpenAL::onClientRemoved( anyID clientID )
{
	clientPositions.remove( clientID );
	if( isEnabled && clientSources.contains( clientID ) )
	{
		clearSourcePosition( clientSources[clientID] );
	}
}

void PositionalAudioOpenAL::onCheckTimeout()
{
	if( isEnabled )
	{
		QString deviceName = getTSPlaybackDeviceName();
		if( previousDeviceName != deviceName )
		{
			previousDeviceName = deviceName;
			disable();
			enable();
		}

		float volume = 0;
		ts3Interface.getPlaybackConfigValueAsFloat( getServerConnectionHandlerID(), "volume_modifier", &volume );
		//std::cout << "TS volume: " << volume << ", OAL volume: " << tsVolumeModifierToOALGain( volume ) << std::endl;
		OpenAL::alListenerf( AL_GAIN, tsVolumeModifierToOALGain( volume ) );
	}
}

void PositionalAudioOpenAL::onClientEnterMyChannel( anyID clientID )
{
	if( isEnabled )
	{
		clientSources[clientID] = createOALSource();
	}
}

void PositionalAudioOpenAL::onClientLeftMyChannel( anyID clientID )
{
	if( isEnabled )
	{
		clientSources.remove( clientID );
	}
}

bool PositionalAudioOpenAL::isNotMyClientID( anyID clientID ) const
{
	return getMyClientID() != clientID;
}

anyID PositionalAudioOpenAL::getMyClientID() const
{
	anyID myID = -1;
	ts3Interface.getClientID( getServerConnectionHandlerID(), &myID );
	return myID;
}

uint64 PositionalAudioOpenAL::getMyChannelID() const
{
	uint64 myID = -1;
	ts3Interface.getChannelOfClient( getServerConnectionHandlerID(), getMyClientID(), &myID );
	return myID;
}

QList<anyID> PositionalAudioOpenAL::getMyChannelClients() const
{
	anyID* clients;
	QList<anyID> results;
	ts3Interface.getChannelClientList( getServerConnectionHandlerID(), getMyChannelID(), &clients );
	for( int i = 0; clients[i] != NULL; i++ )
	{
		if( clients[i] != getMyClientID() )
		{
			results.append( clients[i] );
		}
	}
	ts3Interface.freeMemory( clients );
	return results;
}

QString PositionalAudioOpenAL::getOALConfigPath() const
{
	return QDir::cleanPath( getAppdataPath() + "/alsoft.ini" );
}

QString PositionalAudioOpenAL::getAppdataPath() const
{
	QString targetPath = QStandardPaths::standardLocations( QStandardPaths::GenericDataLocation )[0];
	return targetPath.replace( QRegularExpression( "Local$" ), "Roaming" );
}

QString PositionalAudioOpenAL::getOALHRTFPath() const
{
	QString targetPath = getAppdataPath() + "/openal/hrtf";
	QDir().mkpath( targetPath );
	return QDir::cleanPath( ( targetPath + "/default-%1.mhr" ).arg( AUDIO_FREQUENCY ) );
}

QString PositionalAudioOpenAL::getTSPlaybackDeviceName() const
{
	QString name = getTSCurrentPlaybackDeviceName();
	if( name.isEmpty() )
	{
		name = getTSDefaultPlaybackDeviceName();
	}
	return name;
}

QString PositionalAudioOpenAL::getTSCurrentPlaybackDeviceName() const
{
	QString result;
	char *playbackMode;
	if( ts3Interface.getCurrentPlayBackMode( getServerConnectionHandlerID(), &playbackMode ) == ERROR_ok )
	{
		char* playbackDeviceID;
		if( ts3Interface.getCurrentPlaybackDeviceName( getServerConnectionHandlerID(), &playbackDeviceID, NULL ) == ERROR_ok )
		{
			char*** deviceList;
			if( ts3Interface.getPlaybackDeviceList( playbackMode, &deviceList ) == ERROR_ok )
			{
				for( int i = 0; deviceList[i] != NULL; ++i)
				{
					if( strcmp( playbackDeviceID, deviceList[i][1] ) == 0 )
					{
						result = QString::fromUtf8( deviceList[i][0] );
					}
					ts3Interface.freeMemory( deviceList[i][0] );
					ts3Interface.freeMemory( deviceList[i][1] );
					ts3Interface.freeMemory( deviceList[i] );
				}
				ts3Interface.freeMemory( deviceList );
			}
			ts3Interface.freeMemory( playbackDeviceID );
		}
	}
	return result;
}

QString PositionalAudioOpenAL::getTSDefaultPlaybackDeviceName() const
{
	QString result;
	char* defaultMode;
	if( ts3Interface.getDefaultPlayBackMode( &defaultMode ) == ERROR_ok )
	{
		char** defaultPlaybackDevice;
		if( ts3Interface.getDefaultPlaybackDevice( defaultMode, &defaultPlaybackDevice) == ERROR_ok )
		{
			result = QString::fromUtf8( defaultPlaybackDevice[0] );
			ts3Interface.freeMemory( defaultPlaybackDevice[0] );
			ts3Interface.freeMemory( defaultPlaybackDevice[1] );
			ts3Interface.freeMemory( defaultPlaybackDevice );
		}
		else
		{
			std::cout << "Failed to get default playback device" << std::endl;
		}
		ts3Interface.freeMemory( defaultMode );
	}
	else
	{
		std::cout << "Failed to get default playback mode" << std::endl;
	}
	return result;
}

bool PositionalAudioOpenAL::isOALOk()
{
	ALenum err = OpenAL::alGetError();
	if( err != AL_NO_ERROR )
	{
		fprintf( stdout, "OpenAL Error: %d, %s\n", err, OpenAL::alGetString( err ) );
		return false;
	}
	return true;
}

bool PositionalAudioOpenAL::isOALContextOk( ALCdevice *device )
{
	ALCenum err = OpenAL::alcGetError( device );
	if( err != ALC_NO_ERROR )
	{
		fprintf( stdout, "OpenAL Context Error: %d, %s\n", err, OpenAL::alcGetString( device, err ) );
		return false;
	}
	return true;
}

ALuint PositionalAudioOpenAL::createOALSource()
{
	ALuint source = 0;
	OpenAL::alGenSources( 1, &source );
	if( isOALOk() )
	{
		setSourcePosition( source, createVector( 0.0f, 0.0f, 0.0f ) );
		OpenAL::alSourcef( source, AL_ROLLOFF_FACTOR, 0.0f );
		if( !isOALOk() )
		{
			std::cout << "Failed to set source position" << std::endl;
		}
	}
	else
	{
		std::cout << "Failed to generate source" << std::endl;
	}
	return source;
}

void PositionalAudioOpenAL::deleteOALSource( ALuint source )
{
	OpenAL::alDeleteSources( 1, &source );
	if( !isOALOk() )
	{
		std::cout << "Failed to delete source" << std::endl;
	}
}

void PositionalAudioOpenAL::setSourcePosition( ALuint source, TS3_VECTOR position )
{
	OpenAL::alSourcei( source, AL_SOURCE_RELATIVE, AL_FALSE );
	OpenAL::alSource3f( source, AL_POSITION, position.x, position.y, -position.z );
	if ( !isOALOk() )
	{
		std::cout << "Failed to set source position" << std::endl;
	}
}

void PositionalAudioOpenAL::clearSourcePosition( ALuint source )
{
	OpenAL::alSourcei( source, AL_SOURCE_RELATIVE, AL_TRUE );
	OpenAL::alSource3f( source, AL_POSITION, 0, 0, 0 );
	if ( !isOALOk() )
	{
		std::cout << "Failed to clear source position" << std::endl;
	}
}

void PositionalAudioOpenAL::deleteOALProcessedSourceBuffers( ALuint source )
{
	ALint processedCount = 0;
	OpenAL::alGetSourcei( source, AL_BUFFERS_PROCESSED, &processedCount );
	if( !isOALOk() )
	{
		std::cout << "Failed to get source's processed buffer count" << std::endl;
	}
	if( processedCount > 0 )
	{
		ALuint* buffers = new ALuint[processedCount];
		OpenAL::alSourceUnqueueBuffers( source, processedCount, buffers );
		if( isOALOk() )
		{
			OpenAL::alDeleteBuffers( processedCount, buffers );
			delete [] buffers;
			if( !isOALOk() )
			{
				std::cout << "Failed to remove processed buffers" << std::endl;
			}
		}
		else
		{
			std::cout << "Failed to unqueue processed buffers" << std::endl;
		}
	}
}

ALfloat PositionalAudioOpenAL::tsVolumeModifierToOALGain( float tsVolumeModifier )
{
	return 1.0 / ( pow( 2.0, tsVolumeModifier / -6.0 ) );
}
