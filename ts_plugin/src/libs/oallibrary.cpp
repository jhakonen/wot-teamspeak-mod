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

#include "oallibrary.h"
#include "../utils/logging.h"

#include <QVector>

OALLibrary::OALLibrary( QObject *parent )
	: QObject( parent )
{
	OpenAL::loadLib();
}

OALLibrary::~OALLibrary()
{
	// TODO: unload lib
	qDeleteAll( devices );
}

OALDevice *OALLibrary::createDevice( const QString &name )
{
	devices.append( new OALDevice( name, this ) );
	return devices.last();
}

OALDevice::OALDevice( const QString &name, OALLibrary *parent )
	: QObject( parent ), device( NULL )
{
	QByteArray nameBytes = name.toUtf8();
	device = OpenAL::alcOpenDevice( nameBytes.data() );
}

OALDevice::~OALDevice()
{
	qDeleteAll( contexts );
	if( device )
	{
		try
		{
			OpenAL::alcCloseDevice( device );
		}
		catch( ... )
		{
			Log::warning() << "Failed to close OpenAL device";
		}
	}
}

OALContext *OALDevice::createContext( bool hrtfEnabled )
{
	OALContext defaultContext( this );
	contexts.append( new OALContext( defaultContext.getFrequency(), hrtfEnabled, this ) );
	return contexts.last();
}

OALDevice::operator ALCdevice*() const
{
	return device;
}

OALContext::OALContext( OALDevice *parent )
	: QObject( parent ), context( NULL ), device( parent )
{
	context = OpenAL::alcCreateContext( *device, NULL );
}

OALContext::OALContext( ALCint frequency, bool hrtfEnabled, OALDevice *parent )
	: QObject( parent ), context( NULL ), device( parent )
{
	ALCint attrs[6] = { 0 };
	int i = 0;
	attrs[i++] = ALC_FREQUENCY;
	attrs[i++] = frequency;
	attrs[i++] = ALC_HRTF_SOFT;
	attrs[i++] = hrtfEnabled? ALC_TRUE: ALC_FALSE;
	context = OpenAL::alcCreateContext( *device, attrs );
}

OALContext::~OALContext()
{
	qDeleteAll( sources );
	try
	{
		OpenAL::alcSetThreadContext( NULL );
		OpenAL::alcDestroyContext( context );
	}
	catch( ... )
	{
		Log::warning() << "Failed to destroy OpenAL context";
	}
}

OALSource *OALContext::createSource()
{
	sources.append( new OALSource( this ) );
	return sources.last();
}

ALuint OALContext::getFrequency() const
{
	OpenAL::alcSetThreadContext( context );
	ALCint attributesSize;
	OpenAL::alcGetIntegerv( *device, ALC_ATTRIBUTES_SIZE, 1, &attributesSize );
	QVector<ALCint> attributes( attributesSize );
	OpenAL::alcGetIntegerv( *device, ALC_ALL_ATTRIBUTES, attributesSize, attributes.data() );
	for( auto it = attributes.cbegin(); it != attributes.cend(); it += 2 )
	{
		if( *it == ALC_FREQUENCY )
		{
			return *(it + 1);
		}
	}
	throw OpenAL::Failure( "Sample rate frequency not found from device" );
}

void OALContext::setListenerOrientation( ALfloat forwardX, ALfloat forwardY, ALfloat forwardZ, ALfloat upX, ALfloat upY, ALfloat upZ )
{
	OpenAL::alcSetThreadContext( context );
	ALfloat orientation[] = { forwardX, forwardY, forwardZ, upX, upY, upZ };
	OpenAL::alListenerfv( AL_ORIENTATION, orientation );
}

void OALContext::setListenerGain( ALfloat gain )
{
	OpenAL::alcSetThreadContext( context );
	OpenAL::alListenerf( AL_GAIN, gain );
}

void OALContext::setListenerVelocity( ALfloat x, ALfloat y, ALfloat z )
{
	OpenAL::alcSetThreadContext( context );
	OpenAL::alListener3f( AL_VELOCITY, x, y, z );
}

void OALContext::setListenerPosition( ALfloat x, ALfloat y, ALfloat z )
{
	OpenAL::alcSetThreadContext( context );
	OpenAL::alListener3f( AL_POSITION, x, y, z );
}

OALContext::operator ALCcontext*() const
{
	return context;
}

OALSource::OALSource( OALContext *parent )
	: QObject( parent ), source( 0 ), context( parent ), playbackBuffer( 0 )
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alGenSources( 1, &source );
	startTimer( 1000 );
}

void OALSource::cleanupProcessedBuffers()
{
	try
	{
		OpenAL::alcSetThreadContext( *context );
		ALint processedCount = 0;
		OpenAL::alGetSourcei( source, AL_BUFFERS_PROCESSED, &processedCount );
		if( processedCount > 0 )
		{
			QVector<ALuint> buffers( processedCount );
			OpenAL::alSourceUnqueueBuffers( source, buffers.size(), buffers.data() );
			OpenAL::alDeleteBuffers( buffers.size(), buffers.data() );
		}
	}
	catch( const OpenAL::Failure &error )
	{
		Log::warning() << "Failed to clean up processed buffers, reason: " << error.what();
	}
}

OALSource::~OALSource()
{
	OpenAL::alcSetThreadContext( *context );

	try
	{
		if( isPlaying() )
		{
			stop();
		}
	}
	catch( const OpenAL::Failure &error )
	{
		Log::warning() << "Failed to stop OpenAL playback, reason: " << error.what();
	}

	if( playbackBuffer )
	{
		try
		{
			OpenAL::alSourcei( source, AL_BUFFER, 0 );
			OpenAL::alDeleteBuffers( 1, &playbackBuffer );
		}
		catch( const OpenAL::Failure &error )
		{
			Log::warning() << "Failed to destroy OpenAL playback buffer, reason: " << error.what();
		}
	}

	cleanupProcessedBuffers();

	try
	{
		OpenAL::alDeleteSources( 1, &source );
	}
	catch( ... )
	{
		Log::warning() << "Failed to destroy OpenAL source";
	}
}

void OALSource::setRolloffFactor( ALfloat factor )
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSourcef( source, AL_ROLLOFF_FACTOR, factor );
}

void OALSource::setPosition( ALfloat x, ALfloat y, ALfloat z )
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSource3f( source, AL_POSITION, x, y, z );
}

void OALSource::setRelative( bool relative )
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSourcei( source, AL_SOURCE_RELATIVE, relative? AL_TRUE: AL_FALSE );
}

void OALSource::setLooping( bool looping )
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSourcei( source, AL_LOOPING, looping? AL_TRUE: AL_FALSE );
}

bool OALSource::isPlaying() const
{
	ALint state;
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alGetSourcei( source, AL_SOURCE_STATE, &state );
	return state == AL_PLAYING;
}

void OALSource::playbackAudioData( ALenum format, const ALvoid *data, ALsizei size, ALsizei frequency )
{
	if( playbackBuffer )
	{
		throw OpenAL::Failure( "Playback buffer is already assigned" );
	}

	OpenAL::alcSetThreadContext( *context );
	OpenAL::alGenBuffers( 1, &playbackBuffer );

	try
	{
		OpenAL::alBufferData( playbackBuffer, format, data, size, frequency );
		OpenAL::alSourcei( source, AL_BUFFER, playbackBuffer );
	}
	catch( ... )
	{
		// something went wrong, release buffer if possible
		ALuint buffer = playbackBuffer;
		playbackBuffer = 0;
		OpenAL::alDeleteBuffers( 1, &buffer );
		throw;
	}
}

void OALSource::queueAudioData( ALenum format, const ALvoid *data, ALsizei size, ALsizei frequency )
{
	ALuint buffer;

	cleanupProcessedBuffers();

	OpenAL::alcSetThreadContext( *context );
	OpenAL::alGenBuffers( 1, &buffer );

	try
	{
		OpenAL::alBufferData( buffer, format, data, size, frequency );
		OpenAL::alSourceQueueBuffers( source, 1, &buffer );
	}
	catch( ... )
	{
		// something went wrong, release buffer if possible
		ALuint buffer = playbackBuffer;
		playbackBuffer = 0;
		OpenAL::alDeleteBuffers( 1, &buffer );
		throw;
	}
}

void OALSource::play()
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSourcePlay( source );
}

void OALSource::stop()
{
	OpenAL::alcSetThreadContext( *context );
	OpenAL::alSourceStop( source );
}

void OALSource::timerEvent( QTimerEvent *event )
{
	Q_UNUSED( event );
	cleanupProcessedBuffers();
}
