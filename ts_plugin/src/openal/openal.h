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
#include <QString>
#include "../entities/vector.h"
#include "proxies.h"

namespace OpenAL {

class OutputInfo;
class SourceInfo;
class ListenerInfo;
class AudioData;

/**
 * Resets OpenAL and releases any resources.
 *
 * Call this before process exit.
 */
void free();

/**
 * Resets OpenAL.
 *
 * Deletes all sources, contexts and devices and finally unloads OpenAL library
 * from process memory.
 *
 * Any of the other functions will automatically reload OpenAL on call if
 * necessary.
 *
 * This function is useful when you wish to force OpenAL to load alsoft.ini
 * and HRTF files.
 */
void reset();

/**
 * Sets OpenAL logging level to use.
 *
 * Log entries go to TeamSpeak's client log. The function returns true when
 * given logging level is different than current level. You should call
 * reset() if the logging level changed for the change to apply.
 *
 * Logging is disabled by default.
 *
 * Accepted logging levels:
 *   0 - Disabled
 *   1 - Errors only
 *   2 - Warnings and errors
 *   3 - Additional info, warnings and errors
 *   4 - Same as 3 + debug info
 *
 * @param logLevel log level to use
 * @return true if logging level changed
 */
bool setupLogging( int logLevel );

/**
 * Plays given audio data in provided source.
 *
 * This function lets you to play provided audio data within OpenAL.
 * Audio playback is started automatically if the source isn't yet playing
 * any data.
 *
 * Modifies also source's options if the source already exists.
 *
 * Use stopAudio() to stop the audio playback.
 *
 * @param sourceInfo information of the source
 * @param audioData audio data to play or stream
 */
void playAudio( const SourceInfo &sourceInfo, const AudioData &audioData );

/**
 * Stops audio playback.
 *
 * You can use this function to abruptly stop audio playback of given audio
 * source (e.g. if source is playing a looping audio data).
 *
 * Modifies also source's options if the source already exists.
 *
 * @param sourceInfo information of the source
 */
void stopAudio( const SourceInfo &sourceInfo );

/**
 * Modifies audio source's options.
 *
 * @param sourceInfo information of the source
 */
void updateSource( const SourceInfo &sourceInfo );

/**
 * Modifies audio listener's options.
 *
 * @param listenerInfo information of the listener
 */
void updateListener( const ListenerInfo &listenerInfo );

}
