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

#pragma once

#include <AL/al.h>
#include <AL/alc.h>
#include <public_definitions.h>
#include <QString>

class QMutex;

namespace OpenAL
{

void loadLib();
void reloadLib();

const ALchar* alGetString( ALenum param );
ALenum alGetError();
void alListenerf( ALenum param, ALfloat value );
void alListener3f( ALenum param, ALfloat value1, ALfloat value2, ALfloat value3 );
void alListenerfv( ALenum param, const ALfloat *values );
void alGenSources( ALsizei n, ALuint *sources );
void alDeleteSources( ALsizei n, const ALuint *sources );
void alSourcef( ALuint source, ALenum param, ALfloat value );
void alSource3f( ALuint source, ALenum param, ALfloat value1, ALfloat value2, ALfloat value3 );
void alSourcei( ALuint source, ALenum param, ALint value );
void alGetSourcei( ALuint source,  ALenum param, ALint *value );
void alBufferData( ALuint buffer, ALenum format, const ALvoid *data, ALsizei size, ALsizei freq );
void alDeleteBuffers( ALsizei n, const ALuint *buffers );
void alGenBuffers( ALsizei n, ALuint *buffers );
void alSourceUnqueueBuffers( ALuint source, ALsizei nb, ALuint *buffers );
void alSourceQueueBuffers( ALuint source, ALsizei nb, const ALuint *buffers );
void alSourcePlay( ALuint source );

ALCdevice* alcOpenDevice( const ALCchar *devicename );
ALCboolean alcCloseDevice( ALCdevice *device );
ALCcontext* alcCreateContext( ALCdevice *device, const ALCint* attrlist );
void alcDestroyContext( ALCcontext *context );
ALCcontext *alcGetCurrentContext();
ALCboolean alcSetThreadContext( ALCcontext *context );
void alcGetIntegerv( ALCdevice *device, ALCenum param, ALCsizei size, ALCint *values );
ALCenum alcGetError( ALCdevice *device );
const ALCchar* alcGetString( ALCdevice *device, ALCenum param );

class Failure
{
public:
	Failure( const QString &error )
		: error( error )
	{
	}

	QString what() const
	{
		return error;
	}
private:
	QString error;
};

class LibLoadFailure : public Failure
{
public:
	LibLoadFailure( const QString &error )
		: Failure( error )
	{
	}
};

class LibNotLoadedFailure : public Failure
{
public:
	LibNotLoadedFailure()
		: Failure( "OpenAL library not loaded" )
	{
	}
};

}
