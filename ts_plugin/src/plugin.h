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

#include <ts3_functions.h>

#ifdef WIN32
#define PLUGINS_EXPORTDLL __declspec(dllexport)
#else
#define PLUGINS_EXPORTDLL __attribute__ ((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Required functions */
PLUGINS_EXPORTDLL const char* ts3plugin_name();
PLUGINS_EXPORTDLL const char* ts3plugin_version();
PLUGINS_EXPORTDLL int ts3plugin_apiVersion();
PLUGINS_EXPORTDLL const char* ts3plugin_author();
PLUGINS_EXPORTDLL const char* ts3plugin_description();
PLUGINS_EXPORTDLL void ts3plugin_setFunctionPointers( const struct TS3Functions funcs );
PLUGINS_EXPORTDLL int ts3plugin_init();
PLUGINS_EXPORTDLL void ts3plugin_shutdown();

/* Optional functions */
PLUGINS_EXPORTDLL void ts3plugin_currentServerConnectionChanged( uint64 serverConnectionHandlerID );
PLUGINS_EXPORTDLL int ts3plugin_requestAutoload();

/* Clientlib */
PLUGINS_EXPORTDLL void ts3plugin_onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber );
PLUGINS_EXPORTDLL void ts3plugin_onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char* moveMessage );
PLUGINS_EXPORTDLL int  ts3plugin_onServerErrorEvent( uint64 serverConnectionHandlerID, const char* errorMessage, unsigned int error, const char* returnCode, const char* extraMessage );
PLUGINS_EXPORTDLL void ts3plugin_onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float* volume );
PLUGINS_EXPORTDLL void ts3plugin_onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume );
PLUGINS_EXPORTDLL void ts3plugin_onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels );
PLUGINS_EXPORTDLL void ts3plugin_onEditPostProcessVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels, const unsigned int* channelSpeakerArray, unsigned int* channelFillMask );
PLUGINS_EXPORTDLL void ts3plugin_onEditMixedPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, short* samples, int sampleCount, int channels, const unsigned int* channelSpeakerArray, unsigned int* channelFillMask );

void onAudioBackendChanged(int newBackend );

#ifdef __cplusplus
}
#endif
