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

/**
 * @file
 *
 * This header defines compile time linking to runtime loaded OpenAL library.
 *
 * Use loadLib() and unloadLib() to (un)load OpenAL library on runtime.
 *
 * Other functions wrap OpenAL's functions. They throw a failure exception if
 * the library hasn't been loaded yet.
 * In case the actual function call fails (alGetError() or alcGetError() return
 * an error after call) the proxy functions convert the fail into an exception
 * which is thrown back to caller.
 *
 * For rest of the documentation of al- and alc- prefixed function, see
 * OpenAL's reference documentation.
 */

#pragma once

#include <AL/al.h>
#include <AL/alc.h>
#include <QString>

#ifndef ALC_HRTF_SOFT
#define ALC_HRTF_SOFT 0x1992
#endif

namespace OpenAL
{

namespace Proxies
{

void loadLib();
void unloadLib();

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
void alSourceStop( ALuint source );

ALCdevice* alcOpenDevice( const ALCchar *devicename );
ALCboolean alcCloseDevice( ALCdevice *device );
ALCcontext* alcCreateContext( ALCdevice *device, const ALCint* attrlist );
void alcDestroyContext( ALCcontext *context );
ALCcontext *alcGetCurrentContext();
ALCboolean alcSetThreadContext( ALCcontext *context );
void alcGetIntegerv( ALCdevice *device, ALCenum param, ALCsizei size, ALCint *values );
ALCenum alcGetError( ALCdevice *device );
const ALCchar* alcGetString( ALCdevice *device, ALCenum param );

}

}
