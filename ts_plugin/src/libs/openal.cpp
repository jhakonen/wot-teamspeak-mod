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

#include "openal.h"
#include <Windows.h>
#include <iostream>
#include <QMutex>
#include <QMutexLocker>

namespace
{

LPALBUFFERDATA           g_alBufferData;
LPALDELETEBUFFERS        g_alDeleteBuffers;
LPALDELETESOURCES        g_alDeleteSources;
LPALGENBUFFERS           g_alGenBuffers;
LPALGENSOURCES           g_alGenSources;
LPALGETERROR             g_alGetError;
LPALGETSOURCEI           g_alGetSourcei;
LPALGETSTRING            g_alGetString;
LPALSOURCEPLAY           g_alSourcePlay;
LPALSOURCEQUEUEBUFFERS   g_alSourceQueueBuffers;
LPALLISTENER3F           g_alListener3f;
LPALLISTENERF            g_alListenerf;
LPALLISTENERFV           g_alListenerfv;
LPALSOURCE3F             g_alSource3f;
LPALSOURCEF              g_alSourcef;
LPALSOURCEI              g_alSourcei;
LPALSOURCEUNQUEUEBUFFERS g_alSourceUnqueueBuffers;

LPALCOPENDEVICE          g_alcOpenDevice;
LPALCCREATECONTEXT       g_alcCreateContext;
LPALCMAKECONTEXTCURRENT  g_alcMakeContextCurrent;
LPALCDESTROYCONTEXT      g_alcDestroyContext;
LPALCCLOSEDEVICE         g_alcCloseDevice;
LPALCGETERROR            g_alcGetError;
LPALCGETSTRING           g_alcGetString;

HMODULE g_openALLib = NULL;

template <typename TFunction>
TFunction resolveSymbol( const char *symbol )
{
	TFunction result = (TFunction) GetProcAddress( g_openALLib, symbol );
	if( !result )
	{
		throw OpenAL::LibLoadFailure( "Failed to load OpenAL library, reason: " + getWin32ErrorMessage() );
	}
	return result;
}

inline void throwIfNotLoaded()
{
	if( !g_openALLib )
	{
		throw OpenAL::LibNotLoadedFailure();
	}
}

QString getWin32ErrorMessage()
{
	wchar_t *string = NULL;
	FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_FROM_SYSTEM,
				  NULL,
				  GetLastError(),
				  MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
				  (LPWSTR)&string,
				  0,
				  NULL);
	QString message = QString::fromWCharArray( string );
	LocalFree( (HLOCAL)string );
	return message;
}

void testForALError()
{
	ALenum err = OpenAL::alGetError();
	if( err != AL_NO_ERROR )
	{
		throw OpenAL::Failure( QString( "OpenAL error: %1, %2" ).arg( err ).arg( OpenAL::alGetString( err ) ) );
	}
}

void testForALCError( ALCdevice *device )
{
	ALCenum err = OpenAL::alcGetError( device );
	if( err != ALC_NO_ERROR )
	{
		throw OpenAL::Failure( QString( "OpenAL context error: %1, %2" ).arg( err ).arg( OpenAL::alcGetString( device, err ) ) );
	}
}

}

namespace OpenAL
{

void loadLib()
{
	if( !g_openALLib )
	{
		#if defined( _WIN64 )
		QString libName = "OpenAL64";
		#else
		QString libName = "OpenAL32";
		#endif
		g_openALLib = LoadLibraryEx( (wchar_t*)libName.utf16(), NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS );
		if( !g_openALLib )
		{
			throw OpenAL::LibLoadFailure( "Failed to load OpenAL library, reason: " + getWin32ErrorMessage() );
		}

		g_alBufferData           = resolveSymbol<LPALBUFFERDATA>( "alBufferData" );
		g_alDeleteBuffers        = resolveSymbol<LPALDELETEBUFFERS>( "alDeleteBuffers" );
		g_alDeleteSources        = resolveSymbol<LPALDELETESOURCES>( "alDeleteSources" );
		g_alGenBuffers           = resolveSymbol<LPALGENBUFFERS>( "alGenBuffers" );
		g_alGenSources           = resolveSymbol<LPALGENSOURCES>( "alGenSources" );
		g_alGetError             = resolveSymbol<LPALGETERROR>( "alGetError" );
		g_alGetSourcei           = resolveSymbol<LPALGETSOURCEI>( "alGetSourcei" );
		g_alGetString            = resolveSymbol<LPALGETSTRING>( "alGetString" );
		g_alSourcePlay           = resolveSymbol<LPALSOURCEPLAY>( "alSourcePlay" );
		g_alSourceQueueBuffers   = resolveSymbol<LPALSOURCEQUEUEBUFFERS>( "alSourceQueueBuffers" );
		g_alListener3f           = resolveSymbol<LPALLISTENER3F>( "alListener3f" );
		g_alListenerf            = resolveSymbol<LPALLISTENERF>( "alListenerf" );
		g_alListenerfv           = resolveSymbol<LPALLISTENERFV>( "alListenerfv" );
		g_alSource3f             = resolveSymbol<LPALSOURCE3F>( "alSource3f" );
		g_alSourcef              = resolveSymbol<LPALSOURCEF>( "alSourcef" );
		g_alSourcei              = resolveSymbol<LPALSOURCEI>( "alSourcei" );
		g_alSourceUnqueueBuffers = resolveSymbol<LPALSOURCEUNQUEUEBUFFERS>( "alSourceUnqueueBuffers" );
		g_alcOpenDevice          = resolveSymbol<LPALCOPENDEVICE>( "alcOpenDevice" );
		g_alcCreateContext       = resolveSymbol<LPALCCREATECONTEXT>( "alcCreateContext" );
		g_alcMakeContextCurrent  = resolveSymbol<LPALCMAKECONTEXTCURRENT>( "alcMakeContextCurrent" );
		g_alcDestroyContext      = resolveSymbol<LPALCDESTROYCONTEXT>( "alcDestroyContext" );
		g_alcCloseDevice         = resolveSymbol<LPALCCLOSEDEVICE>( "alcCloseDevice" );
		g_alcGetError            = resolveSymbol<LPALCGETERROR>( "alcGetError" );
		g_alcGetString           = resolveSymbol<LPALCGETSTRING>( "alcGetString" );
	}
}

void reloadLib()
{
	if( g_openALLib )
	{
		if( FreeLibrary( g_openALLib ) == FALSE )
		{
			throw OpenAL::LibLoadFailure( "Failed to unload OpenAL library, reason: " + getWin32ErrorMessage() );
		}
		g_openALLib = NULL;
	}
	loadLib();
}

const ALchar *alGetString( ALenum param )
{
	throwIfNotLoaded();
	return g_alGetString( param );
}

ALenum alGetError()
{
	throwIfNotLoaded();
	return g_alGetError();
}

void alListenerf( ALenum param, ALfloat value )
{
	throwIfNotLoaded();
	g_alListenerf( param, value );
	testForALError();
}

void alListener3f( ALenum param, ALfloat value1, ALfloat value2, ALfloat value3 )
{
	throwIfNotLoaded();
	g_alListener3f( param, value1, value2, value3 );
	testForALError();
}

void alListenerfv( ALenum param, const ALfloat *values )
{
	throwIfNotLoaded();
	g_alListenerfv( param, values );
	testForALError();
}

void alGenSources( ALsizei n, ALuint *sources )
{
	throwIfNotLoaded();
	g_alGenSources( n, sources );
	testForALError();
}

void alDeleteSources( ALsizei n, const ALuint *sources )
{
	throwIfNotLoaded();
	g_alDeleteSources( n, sources );
	testForALError();
}

void alSourcef( ALuint source, ALenum param, ALfloat value )
{
	throwIfNotLoaded();
	g_alSourcef( source, param, value );
	testForALError();
}

void alSource3f( ALuint source, ALenum param, ALfloat value1, ALfloat value2, ALfloat value3 )
{
	throwIfNotLoaded();
	g_alSource3f( source, param, value1, value2, value3 );
	testForALError();
}

void alSourcei( ALuint source, ALenum param, ALint value )
{
	throwIfNotLoaded();
	g_alSourcei( source, param, value );
	testForALError();
}

void alGetSourcei( ALuint source, ALenum param, ALint *value )
{
	throwIfNotLoaded();
	g_alGetSourcei( source, param, value );
}

void alBufferData( ALuint buffer, ALenum format, const ALvoid *data, ALsizei size, ALsizei freq )
{
	throwIfNotLoaded();
	g_alBufferData( buffer, format, data, size, freq );
	testForALError();
}

void alDeleteBuffers( ALsizei n, const ALuint *buffers )
{
	throwIfNotLoaded();
	g_alDeleteBuffers( n, buffers );
	testForALError();
}

void alGenBuffers( ALsizei n, ALuint *buffers )
{
	throwIfNotLoaded();
	g_alGenBuffers( n, buffers );
	testForALError();
}

void alSourceUnqueueBuffers( ALuint source, ALsizei nb, ALuint *buffers )
{
	throwIfNotLoaded();
	g_alSourceUnqueueBuffers( source, nb, buffers );
	testForALError();
}

void alSourceQueueBuffers( ALuint source, ALsizei nb, const ALuint *buffers )
{
	throwIfNotLoaded();
	g_alSourceQueueBuffers( source, nb, buffers );
	testForALError();
}

void alSourcePlay( ALuint source )
{
	throwIfNotLoaded();
	g_alSourcePlay( source );
	testForALError();
}

ALCdevice *alcOpenDevice( const ALCchar *devicename )
{
	throwIfNotLoaded();
	ALCdevice* device = g_alcOpenDevice( devicename );
	testForALCError( device );
	return device;
}

ALCboolean alcCloseDevice( ALCdevice *device )
{
	throwIfNotLoaded();
	return g_alcCloseDevice( device );
}

ALCcontext *alcCreateContext( ALCdevice *device, const ALCint *attrlist )
{
	throwIfNotLoaded();
	ALCcontext *context = g_alcCreateContext( device, attrlist );
	testForALCError( device );
	return context;
}

void alcDestroyContext( ALCcontext *context )
{
	throwIfNotLoaded();
	g_alcDestroyContext( context );
}

ALCboolean alcMakeContextCurrent( ALCcontext *context )
{
	throwIfNotLoaded();
	return g_alcMakeContextCurrent( context );
}

ALCenum alcGetError( ALCdevice *device )
{
	throwIfNotLoaded();
	return g_alcGetError( device );
}

const ALCchar *alcGetString( ALCdevice *device, ALCenum param )
{
	throwIfNotLoaded();
	return g_alcGetString( device, param );
}

}
