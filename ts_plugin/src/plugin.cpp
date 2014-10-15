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

#include "plugin.h"
#include "sharedmemorylistener.h"
#include "positionalaudio.h"

#include <Windows.h>

static struct TS3Functions ts3Functions;
static SharedMemoryListener* memoryListener;
static PositionalAudio* positionalAudio;

#define PLUGIN_API_VERSION 20

#ifdef _WIN32
/* Helper function to convert wchar_T to Utf-8 encoded strings on Windows */
static int wcharToUtf8(const wchar_t* str, char** result) {
	int outlen = WideCharToMultiByte(CP_UTF8, 0, str, -1, 0, 0, 0, 0);
	*result = (char*)malloc(outlen);
	if(WideCharToMultiByte(CP_UTF8, 0, str, -1, *result, outlen, 0, 0) == 0) {
		*result = NULL;
		return -1;
	}
	return 0;
}
#endif

/*********************************** Required functions ************************************/
/*
 * If any of these required functions is not implemented, TS3 will refuse to load the plugin
 */

/* Unique name identifying this plugin */
const char* ts3plugin_name() {
	return "TessuMod Plugin";
}

/* Plugin version */
const char* ts3plugin_version() {
    return "0.1";
}

/* Plugin API version. Must be the same as the clients API major version, else the plugin fails to load. */
int ts3plugin_apiVersion() {
	return PLUGIN_API_VERSION;
}

/* Plugin author */
const char* ts3plugin_author() {
	return "jhakonen @ EU";
}

/* Plugin description */
const char* ts3plugin_description() {
	return "This plugin provides positional audio support for World of Tanks.";
}

/* Set TeamSpeak 3 callback functions */
void ts3plugin_setFunctionPointers(const struct TS3Functions funcs) {
    ts3Functions = funcs;
}

/*
 * Custom code called right after loading the plugin. Returns 0 on success, 1 on failure.
 * If the function returns 1 on failure, the plugin will be unloaded again.
 */
int ts3plugin_init() {
	memoryListener = new SharedMemoryListener();
	positionalAudio = new PositionalAudio( ts3Functions );

	QObject::connect( memoryListener, SIGNAL( cameraPositionChanged( TS3_VECTOR ) ),
					  positionalAudio, SLOT( onCameraPositionChanged( TS3_VECTOR ) ) );
	QObject::connect( memoryListener, SIGNAL( cameraDirectionChanged( TS3_VECTOR ) ),
					  positionalAudio, SLOT( onCameraDirectionChanged( TS3_VECTOR ) ) );

	QObject::connect( memoryListener, SIGNAL( clientAdded( anyID, TS3_VECTOR ) ),
					  positionalAudio, SLOT( onClientAdded( anyID, TS3_VECTOR ) ) );
	QObject::connect( memoryListener, SIGNAL( clientPositionChanged( anyID, TS3_VECTOR ) ),
					  positionalAudio, SLOT( onClientPositionChanged( anyID, TS3_VECTOR ) ) );
	QObject::connect( memoryListener, SIGNAL( clientRemoved( anyID ) ),
					  positionalAudio, SLOT( onClientRemoved( anyID ) ) );

	memoryListener->start();

    return 0;  /* 0 = success, 1 = failure, -2 = failure but client will not show a "failed to load" warning */
	/* -2 is a very special case and should only be used if a plugin displays a dialog (e.g. overlay) asking the user to disable
	 * the plugin again, avoiding the show another dialog by the client telling the user the plugin failed to load.
	 * For normal case, if a plugin really failed to load because of an error, the correct return value is 1. */
}

/* Custom code called right before the plugin is unloaded */
void ts3plugin_shutdown() {
	memoryListener->stop();
	delete memoryListener;
	delete positionalAudio;
}

/****************************** Optional functions ********************************/
/*
 * Following functions are optional, if not needed you don't need to implement them.
 */

/* Client changed current server connection handler */
void ts3plugin_currentServerConnectionChanged( uint64 serverConnectionHandlerID ) {
	positionalAudio->setServerConnectionHandlerID( serverConnectionHandlerID );
}

/*
 * Plugin requests to be always automatically loaded by the TeamSpeak 3 client unless
 * the user manually disabled it in the plugin dialog.
 * This function is optional. If missing, no autoload is assumed.
 */
int ts3plugin_requestAutoload() {
	return 1;  /* 1 = request autoloaded, 0 = do not request autoload */
}

int ts3plugin_onServerErrorEvent(uint64 serverConnectionHandlerID, const char* errorMessage, unsigned int error, const char* returnCode, const char* extraMessage) {
	Q_UNUSED( extraMessage );
	printf("PLUGIN: onServerErrorEvent %llu %s %d %s\n", (long long unsigned int)serverConnectionHandlerID, errorMessage, error, (returnCode ? returnCode : ""));
	if(returnCode) {
		/* A plugin could now check the returnCode with previously (when calling a function) remembered returnCodes and react accordingly */
		/* In case of using a a plugin return code, the plugin can return:
		 * 0: Client will continue handling this error (print to chat tab)
		 * 1: Client will ignore this error, the plugin announces it has handled it */
		return 1;
	}
	return 0;  /* If no plugin return code was used, the return value of this function is ignored */
}

void ts3plugin_onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float* volume ) {
	positionalAudio->onCustom3dRolloffCalculationClientEvent( serverConnectionHandlerID, clientID, distance, volume );
}

void ts3plugin_onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume ) {
	positionalAudio->onCustom3dRolloffCalculationWaveEvent( serverConnectionHandlerID, waveHandle, distance, volume );
}
