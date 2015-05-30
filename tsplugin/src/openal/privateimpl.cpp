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

#include "privateimpl.h"
#include "proxies.h"
#include "structures.h"
#include "../utils/logging.h"

#include <QVector>
#include <QMap>

namespace OpenAL {
namespace PrivateImpl {

static QMap<QString, ALCdevice*> gOALDevices;
static QMap<OutputInfo, ALCcontext*> gOALContexts;
static QMap<OutputInfo, ListenerInfo> gListenerInfos;
static QMap<quint32, QPair<SourceInfo, ALuint>> gOALSources;
static bool gLibraryLoaded = false;

void reset()
{
	if( gLibraryLoaded )
	{
		releaseAllSources();
		releaseAllContexts();
		releaseAllDevices();
		Proxies::unloadLib();
		gLibraryLoaded = false;
	}
}

ALCdevice *queryDevice( const OutputInfo &info )
{
	if( !info.isValid() )
	{
		return NULL;
	}
	if( !gLibraryLoaded )
	{
		OpenAL::Proxies::loadLib();
		gLibraryLoaded = true;
	}
	// create OpenAL device if it doesn't exist yet
	if( !gOALDevices.contains( info.getDeviceName() ) )
	{
		QByteArray nameBytes = info.getDeviceName().toUtf8();
		gOALDevices[info.getDeviceName()] = OpenAL::Proxies::alcOpenDevice( nameBytes.data() );
	}
	return gOALDevices[info.getDeviceName()];
}

ALCcontext *queryContext( const OutputInfo &info )
{
	if( !info.isValid() )
	{
		return NULL;
	}
	// create OpenAL context if it doesn't exist yet
	if( !gOALContexts.contains( info ) )
	{
		ALCint attrs[7] = { 0 };
		int i = 0;
		attrs[i++] = ALC_FREQUENCY;
		attrs[i++] = info.getSampleRate();
		if( info.isHrtfEnabled() )
		{
			attrs[i++] = ALC_FORMAT_CHANNELS_SOFT;
			attrs[i++] = ALC_STEREO_SOFT;
			attrs[i++] = ALC_HRTF_SOFT;
			attrs[i++] = ALC_TRUE;
		}
		gOALContexts[info] = OpenAL::Proxies::alcCreateContext( queryDevice( info ), attrs );
	}
	return gOALContexts[info];
}

ALuint querySource( const SourceInfo &info )
{
	if( !info.isValid() )
	{
		return 0;
	}
	bool createNew = false;
	if( gOALSources.contains( info.getId() ) )
	{
		// source already exists
		SourceInfo prevInfo = gOALSources[info.getId()].first;
		if( info.getOutputInfo() != prevInfo.getOutputInfo() )
		{
			// changed output info requires new context or device and such a
			// new source as well
			releaseSource( info.getId() );
			createNew = true;
		}
	}
	else
	{
		// source doesn't exist --> create a new one
		createNew = true;
	}
	if( createNew )
	{
		ALuint source;
		OpenAL::Proxies::alGenSources( 1, &source );
		gOALSources[info.getId()] = qMakePair( info, source );
	}
	updateSourceOptions( info, createNew );
	return gOALSources[info.getId()].second;
}

void updateSourceOptions( const SourceInfo &info, bool force )
{
	if( !info.isValid() )
	{
		return;
	}
	if( gOALSources.contains( info.getId() ) )
	{
		SourceInfo prevInfo = gOALSources[info.getId()].first;
		ALuint source = gOALSources[info.getId()].second;
		if( force || info.getPosition() != prevInfo.getPosition() )
		{
			OpenAL::Proxies::alSource3f( source, AL_POSITION, info.getPosition().x, info.getPosition().y, info.getPosition().z );
		}
		if( force || info.getRolloffFactor() != prevInfo.getRolloffFactor() )
		{
			OpenAL::Proxies::alSourcef( source, AL_ROLLOFF_FACTOR, info.getRolloffFactor() );
		}
		if( force || info.isRelative() != prevInfo.isRelative() )
		{
			OpenAL::Proxies::alSourcei( source, AL_SOURCE_RELATIVE, info.isRelative()? AL_TRUE: AL_FALSE );
		}
		if( force || info.isStreaming() != prevInfo.isStreaming() )
		{
			OpenAL::Proxies::alSourcei( source, AL_LOOPING, info.isStreaming()? AL_FALSE: AL_TRUE );
		}
		gOALSources[info.getId()].first = info;
	}
}

void updateListenerOptions( const ListenerInfo &info )
{
	if( !info.isValid() )
	{
		return;
	}
	bool force = false;
	if( !gListenerInfos.contains( info.getOutputInfo() ) )
	{
		gListenerInfos[info.getOutputInfo()] = info;
		force = true;
	}
	ListenerInfo prevInfo = gListenerInfos[info.getOutputInfo()];
	if( force || info.getForward() != prevInfo.getForward() || info.getUp() != prevInfo.getForward() )
	{
		ALfloat orientation[] = { info.getForward().x, info.getForward().y, info.getForward().z,
								  info.getUp().x, info.getUp().y, info.getUp().z };
		OpenAL::Proxies::alListenerfv( AL_ORIENTATION, orientation );
	}
	if( force || info.getPosition() != prevInfo.getPosition() )
	{
		OpenAL::Proxies::alListener3f( AL_POSITION, info.getPosition().x, info.getPosition().y, info.getPosition().z );
	}
	if( force || info.getGain() != prevInfo.getGain() )
	{
		OpenAL::Proxies::alListenerf( AL_GAIN, info.getGain() );
	}
	if( force || info.getVelocity() != prevInfo.getVelocity() )
	{
		OpenAL::Proxies::alListener3f( AL_VELOCITY, info.getVelocity().x, info.getVelocity().y, info.getVelocity().z );
	}
}

void releaseAllContexts()
{
	OpenAL::Proxies::alcSetThreadContext( NULL );
	foreach( ALCcontext *context, gOALContexts )
	{
		try
		{
			OpenAL::Proxies::alcDestroyContext( context );
		}
		catch( ... )
		{
			Log::warning() << "Failed to release OpenAL context ";
		}
	}
	gListenerInfos.clear();
	gOALContexts.clear();
}

void releaseAllDevices()
{
	foreach( QString name, gOALDevices.keys() )
	{
		try
		{
			OpenAL::Proxies::alcCloseDevice( gOALDevices[name] );
		}
		catch( ... )
		{
			Log::warning() << "Failed to close OpenAL device " << name;
		}
	}
	gOALDevices.clear();
}

void releaseAllSources()
{
	foreach( quint32 id, gOALSources.keys() )
	{
		releaseSource( id );
	}
	gOALSources.clear();
}

void releaseSource( quint32 id )
{
	try
	{
		if( gOALSources.contains( id ) )
		{
			auto sourceData = gOALSources.take( id );
			applyThreadContext( sourceData.first.getOutputInfo() );
			OpenAL::Proxies::alDeleteSources( 1, &sourceData.second );
		}
	}
	catch( ... )
	{
		Log::warning() << "Failed to destroy OpenAL source";
	}
}

ALenum oalGetFormat( quint16 channels, quint16 samples )
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

bool isSourcePlaying( const SourceInfo &sourceInfo )
{
	ALint state;
	OpenAL::Proxies::alGetSourcei( querySource( sourceInfo ), AL_SOURCE_STATE, &state );
	return state == AL_PLAYING;
}

void applyThreadContext( const OutputInfo &info )
{
	OpenAL::Proxies::alcSetThreadContext( queryContext( info ) );
}

ALuint bufferAudioData( const AudioData &audioData )
{
	ALuint buffer = 0;
	OpenAL::Proxies::alGenBuffers( 1, &buffer );
	try
	{
		ALenum format = oalGetFormat( audioData.getChannelCount(), audioData.getSampleSize() );
		Proxies::alBufferData( buffer,
							   format,
							   audioData.getData(),
							   audioData.getDataSize(),
							   audioData.getSampleRate() );
	}
	catch( ... )
	{
		// something went wrong, release buffer if possible
		if( buffer )
		{
			OpenAL::Proxies::alDeleteBuffers( 1, &buffer );
		}
		throw;
	}
	return buffer;
}

void cleanupProcessedBuffers( const SourceInfo &sourceInfo )
{
	try
	{
		ALuint source = querySource( sourceInfo );
		ALint processedCount = 0;
		OpenAL::Proxies::alGetSourcei( source, AL_BUFFERS_PROCESSED, &processedCount );
		if( processedCount > 0 )
		{
			QVector<ALuint> buffers( processedCount );
			Proxies::alSourceUnqueueBuffers( source, buffers.size(), buffers.data() );
			Proxies::alDeleteBuffers( buffers.size(), buffers.data() );
		}
	}
	catch( const OpenAL::Failure &error )
	{
		Log::warning() << "Failed to clean up processed buffers, reason: " << error.what();
	}
}

}
}
