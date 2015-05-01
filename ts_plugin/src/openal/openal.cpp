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

#include "openal.h"
#include "privateimpl.h"
#include "structures.h"
#include "../utils/logging.h"
#include <QMap>
#include <QPair>
#include <QVector>
#include <QMutex>
#include <QMutexLocker>

static QMutex gMutex;

namespace OpenAL {

void reset()
{
	QMutexLocker locker( &gMutex );
	PrivateImpl::reset();
}

void playAudio( const SourceInfo &sourceInfo, const AudioData &audioData )
{
	if( !sourceInfo.isValid() )
	{
		return;
	}

	QMutexLocker locker( &gMutex );
	PrivateImpl::applyThreadContext( sourceInfo.getOutputInfo() );
	PrivateImpl::updateSourceOptions( sourceInfo );
	ALuint buffer = 0, silentBuffer = 0;

	try
	{
		buffer = PrivateImpl::bufferAudioData( audioData );
		ALuint source = PrivateImpl::querySource( sourceInfo );

		bool isPlaying = PrivateImpl::isSourcePlaying( sourceInfo );

		if( sourceInfo.isStreaming() )
		{
			PrivateImpl::cleanupProcessedBuffers( sourceInfo );
			if( !isPlaying )
			{
				// delay start of playback a bit so that we don't starve the playback device
				short silence[48000 / 10] = {};
				silentBuffer = PrivateImpl::bufferAudioData( AudioData( 1, sizeof(short) * 8, sizeof(silence), 48000, silence ) );
				Proxies::alSourceQueueBuffers( source, 1, &silentBuffer );
				silentBuffer = 0;
			}
			Proxies::alSourceQueueBuffers( source, 1, &buffer );
			buffer = 0;
		}
		else
		{
			Proxies::alSourcei( source, AL_BUFFER, buffer );
			buffer = 0;
		}

		if( !isPlaying )
		{
			Proxies::alSourcePlay( source );
		}
	}
	catch( ... )
	{
		// something went wrong, release buffers if possible
		if( buffer )
		{
			try
			{
				Proxies::alDeleteBuffers( 1, &buffer );
			}
			catch( ... ) {}
		}
		if( silentBuffer )
		{
			try
			{
				Proxies::alDeleteBuffers( 1, &silentBuffer );
			}
			catch( ... ) {}
		}
		throw;
	}
}

void stopAudio( const SourceInfo &sourceInfo )
{
	if( sourceInfo.isValid() )
	{
		QMutexLocker locker( &gMutex );
		PrivateImpl::applyThreadContext( sourceInfo.getOutputInfo() );
		PrivateImpl::updateSourceOptions( sourceInfo );
		Proxies::alSourceStop( PrivateImpl::querySource( sourceInfo ) );
	}
}

void updateSource( const SourceInfo &sourceInfo )
{
	if( sourceInfo.isValid() )
	{
		QMutexLocker locker( &gMutex );
		PrivateImpl::applyThreadContext( sourceInfo.getOutputInfo() );
		PrivateImpl::updateSourceOptions( sourceInfo );
	}
}

void updateListener( const ListenerInfo &listenerInfo )
{
	if( listenerInfo.isValid() )
	{
		QMutexLocker locker( &gMutex );
		PrivateImpl::applyThreadContext( listenerInfo.getOutputInfo() );
		PrivateImpl::updateListenerOptions( listenerInfo );
	}
}

}
