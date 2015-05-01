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

#pragma once
#include <AL/alext.h>
#include <QtGlobal>

namespace OpenAL {

class OutputInfo;
class SourceInfo;
class ListenerInfo;
class AudioData;

namespace PrivateImpl {

void reset();
ALenum oalGetFormat( quint16 channels, quint16 samples );
ALCdevice *queryDevice( const OutputInfo &info );
ALCcontext *queryContext( const OutputInfo &info );
ALuint querySource( const SourceInfo &info );
void updateSourceOptions( const SourceInfo &info, bool force = false );
void updateListenerOptions( const ListenerInfo &info );
void releaseAllContexts();
void releaseAllDevices();
void releaseAllSources();
void releaseSource( quint32 id );
void applyThreadContext( const OutputInfo &info );
ALuint bufferAudioData( const AudioData &audioData );
void cleanupProcessedBuffers( const SourceInfo &sourceInfo );
bool isSourcePlaying( const SourceInfo &sourceInfo );

}
}
