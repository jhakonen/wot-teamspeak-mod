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
#include "positionalaudioopenal.h"
#include "settings.h"

#include <Windows.h>
#include <iostream>
#include <cassert>
#include <QCoreApplication>
#include <QDir>

static struct TS3Functions ts3Functions;
static QPointer<SharedMemoryListener> memoryListener;
static QPointer<Settings> settings;
static std::list<ModuleBase*> modules;
static DLL_DIRECTORY_COOKIE dllSearchCookie;
static char* pluginID = NULL;

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

#define CALL_MODULES( call ) \
	for( auto it = modules.begin(); it != modules.end(); ++it ) \
	{ \
		(*it)->call; \
	}

QString getPluginDataPath()
{
	char pluginPath[512];
	ts3Functions.getPluginPath( pluginPath, 512 );
	return QDir::cleanPath( QString( pluginPath ) + "/tessumod_plugin" );
}

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
	QString dataPath = QDir::toNativeSeparators( getPluginDataPath() );
	dllSearchCookie = AddDllDirectory( (wchar_t*)dataPath.utf16() );

	memoryListener = new SharedMemoryListener();
	settings = new Settings();
	modules.push_back( new PositionalAudio( ts3Functions ) );
	modules.push_back( new PositionalAudioOpenAL( ts3Functions ) );
	modules.push_back( settings );

	for( auto it = modules.begin(); it != modules.end(); ++it )
	{
		(*it)->init();
		QObject::connect( memoryListener, SIGNAL( cameraPositionChanged( TS3_VECTOR ) ),
						  *it, SLOT( onCameraPositionChanged( TS3_VECTOR ) ) );
		QObject::connect( memoryListener, SIGNAL( cameraDirectionChanged( TS3_VECTOR ) ),
						  *it, SLOT( onCameraDirectionChanged( TS3_VECTOR ) ) );
		QObject::connect( memoryListener, SIGNAL( clientAdded( anyID, TS3_VECTOR ) ),
						  *it, SLOT( onClientAdded( anyID, TS3_VECTOR ) ) );
		QObject::connect( memoryListener, SIGNAL( clientPositionChanged( anyID, TS3_VECTOR ) ),
						  *it, SLOT( onClientPositionChanged( anyID, TS3_VECTOR ) ) );
		QObject::connect( memoryListener, SIGNAL( clientRemoved( anyID ) ),
						  *it, SLOT( onClientRemoved( anyID ) ) );
	}

	QObject::connect( settings, &Settings::audioBackendChanged, onAudioBackendChanged );

	memoryListener->start();

	enableAndDisableModules();

    return 0;  /* 0 = success, 1 = failure, -2 = failure but client will not show a "failed to load" warning */
	/* -2 is a very special case and should only be used if a plugin displays a dialog (e.g. overlay) asking the user to disable
	 * the plugin again, avoiding the show another dialog by the client telling the user the plugin failed to load.
	 * For normal case, if a plugin really failed to load because of an error, the correct return value is 1. */
}

/* Custom code called right before the plugin is unloaded */
void ts3plugin_shutdown() {
	RemoveDllDirectory( dllSearchCookie );

	memoryListener->stop();
	delete memoryListener;
	for( auto it = modules.begin(); it != modules.end(); ++it )
	{
		delete *it;
	}
	modules.clear();

	delete [] pluginID;
	pluginID = NULL;
}

/****************************** Optional functions ********************************/
/*
 * Following functions are optional, if not needed you don't need to implement them.
 */

/* Tell client if plugin offers a configuration window. If this function is not implemented, it's an assumed "does not offer" (PLUGIN_OFFERS_NO_CONFIGURE). */
int ts3plugin_offersConfigure()
{
	/*
	 * Return values:
	 * PLUGIN_OFFERS_NO_CONFIGURE         - Plugin does not implement ts3plugin_configure
	 * PLUGIN_OFFERS_CONFIGURE_NEW_THREAD - Plugin does implement ts3plugin_configure and requests to run this function in an own thread
	 * PLUGIN_OFFERS_CONFIGURE_QT_THREAD  - Plugin does implement ts3plugin_configure and requests to run this function in the Qt GUI thread
	 */
	return PLUGIN_OFFERS_CONFIGURE_QT_THREAD;  /* In this case ts3plugin_configure does not need to be implemented */
}

/* Plugin might offer a configuration window. If ts3plugin_offersConfigure returns 0, this function does not need to be implemented. */
void ts3plugin_configure( void* handle, void* qParentWidget )
{
	CALL_MODULES( configure( handle, qParentWidget ) );
}

/*
 * If the plugin wants to use error return codes, plugin commands, hotkeys or menu items, it needs to register a command ID. This function will be
 * automatically called after the plugin was initialized. This function is optional. If you don't use these features, this function can be omitted.
 * Note the passed pluginID parameter is no longer valid after calling this function, so you must copy it and store it in the plugin.
 */
void ts3plugin_registerPluginID( const char* id )
{
	size_t size = strlen( id ) + 1;
	pluginID = new char[strlen( id ) + 1];
	strncpy_s( pluginID, size, id, size );
	printf("PLUGIN: registerPluginID: %s\n", pluginID);
}

/* Client changed current server connection handler */
void ts3plugin_currentServerConnectionChanged( uint64 serverConnectionHandlerID ) {
	CALL_MODULES( setServerConnectionHandlerID( serverConnectionHandlerID ) );
}

/* Required to release the memory for parameter "data" allocated in ts3plugin_infoData and ts3plugin_initMenus */
void ts3plugin_freeMemory( void* data )
{
	free( data );
}

/*
 * Plugin requests to be always automatically loaded by the TeamSpeak 3 client unless
 * the user manually disabled it in the plugin dialog.
 * This function is optional. If missing, no autoload is assumed.
 */
int ts3plugin_requestAutoload() {
	return 1;  /* 1 = request autoloaded, 0 = do not request autoload */
}

/* Helper function to create a menu item */
static struct PluginMenuItem* createMenuItem( PluginMenuType type, int id, const char* text ) {
	PluginMenuItem* menuItem = (PluginMenuItem*) malloc( sizeof( PluginMenuItem ) );
	menuItem->type = type;
	menuItem->id = id;
	strncpy_s( menuItem->text, text, PLUGIN_MENU_BUFSZ );
	menuItem->icon[0] = NULL;
	return menuItem;
}

/* Some makros to make the code to create menu items a bit more readable */
#define BEGIN_CREATE_MENUS( x ) const size_t sz = x + 1; size_t n = 0; *menuItems = (PluginMenuItem**) malloc( sizeof( PluginMenuItem* ) * sz );
#define CREATE_MENU_ITEM( a, b, c ) (*menuItems)[n++] = createMenuItem( a, b, c );
#define END_CREATE_MENUS (*menuItems)[n++] = NULL; assert( n == sz );

/*
 * Initialize plugin menus.
 * This function is called after ts3plugin_init and ts3plugin_registerPluginID. A pluginID is required for plugin menus to work.
 * Both ts3plugin_registerPluginID and ts3plugin_freeMemory must be implemented to use menus.
 * If plugin menus are not used by a plugin, do not implement this function or return NULL.
 */
void ts3plugin_initMenus( PluginMenuItem*** menuItems, char** menuIcon )
{
	/*
	 * Create the menus
	 * There are three types of menu items:
	 * - PLUGIN_MENU_TYPE_CLIENT:  Client context menu
	 * - PLUGIN_MENU_TYPE_CHANNEL: Channel context menu
	 * - PLUGIN_MENU_TYPE_GLOBAL:  "Plugins" menu in menu bar of main window
	 *
	 * Menu IDs are used to identify the menu item when ts3plugin_onMenuItemEvent is called
	 *
	 * The menu text is required, max length is 128 characters
	 *
	 * The icon is optional, max length is 128 characters. When not using icons, just pass an empty string.
	 * Icons are loaded from a subdirectory in the TeamSpeak client plugins folder. The subdirectory must be named like the
	 * plugin filename, without dll/so/dylib suffix
	 * e.g. for "test_plugin.dll", icon "1.png" is loaded from <TeamSpeak 3 Client install dir>\plugins\test_plugin\1.png
	 */

	BEGIN_CREATE_MENUS( 1 );  /* IMPORTANT: Number of menu items must be correct! */
	CREATE_MENU_ITEM( PLUGIN_MENU_TYPE_GLOBAL,  MENU_ID_GLOBAL_SETTINGS,  "Settings" );
	END_CREATE_MENUS;  /* Includes an assert checking if the number of menu items matched */

	/*
	 * Specify an optional icon for the plugin. This icon is used for the plugins submenu within context and main menus
	 * If unused, set menuIcon to NULL
	 */
	*menuIcon = NULL;

	/* All memory allocated in this function will be automatically released by the TeamSpeak client later by calling ts3plugin_freeMemory */
}

void ts3plugin_onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber )
{
	CALL_MODULES( onConnectStatusChangeEvent( serverConnectionHandlerID, newStatus, errorNumber ) );
}

void ts3plugin_onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage )
{
	std::cout << "onClientMoveEvent() :: "
			  << "clientID: " << clientID << ", "
			  << "oldChannelID: " << oldChannelID << ", "
			  << "newChannelID: " << newChannelID << ", "
			  << "visibility: " << visibility
			  << std::endl;
	CALL_MODULES( onClientMoveEvent( serverConnectionHandlerID, clientID, oldChannelID, newChannelID, visibility, moveMessage ) );
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
	CALL_MODULES( onCustom3dRolloffCalculationClientEvent( serverConnectionHandlerID, clientID, distance, volume ) );
}

void ts3plugin_onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume ) {
	CALL_MODULES( onCustom3dRolloffCalculationWaveEvent( serverConnectionHandlerID, waveHandle, distance, volume ) );
}

void ts3plugin_onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels ) {
	CALL_MODULES( onEditPlaybackVoiceDataEvent( serverConnectionHandlerID, clientID, samples, sampleCount, channels ) );
}

void ts3plugin_onEditPostProcessVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels, const unsigned int* channelSpeakerArray, unsigned int* channelFillMask )
{
	CALL_MODULES( onEditPostProcessVoiceDataEvent( serverConnectionHandlerID, clientID, samples, sampleCount, channels, channelSpeakerArray, channelFillMask ) );
}

void ts3plugin_onEditMixedPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, short* samples, int sampleCount, int channels, const unsigned int* channelSpeakerArray, unsigned int* channelFillMask )
{
	CALL_MODULES( onEditMixedPlaybackVoiceDataEvent( serverConnectionHandlerID, samples, sampleCount, channels, channelSpeakerArray, channelFillMask ) );
}

/*
 * Called when a plugin menu item (see ts3plugin_initMenus) is triggered. Optional function, when not using plugin menus, do not implement this.
 *
 * Parameters:
 * - serverConnectionHandlerID: ID of the current server tab
 * - type: Type of the menu (PLUGIN_MENU_TYPE_CHANNEL, PLUGIN_MENU_TYPE_CLIENT or PLUGIN_MENU_TYPE_GLOBAL)
 * - menuItemID: Id used when creating the menu item
 * - selectedItemID: Channel or Client ID in the case of PLUGIN_MENU_TYPE_CHANNEL and PLUGIN_MENU_TYPE_CLIENT. 0 for PLUGIN_MENU_TYPE_GLOBAL.
 */
void ts3plugin_onMenuItemEvent( uint64 serverConnectionHandlerID, PluginMenuType type, int menuItemID, uint64 selectedItemID )
{
	CALL_MODULES( onMenuItemEvent( serverConnectionHandlerID, type, menuItemID, selectedItemID ) );
}

void onAudioBackendChanged( int newBackend )
{
	Q_UNUSED( newBackend );
	enableAndDisableModules();
}

void onPositionalAudioToggled( bool enabled )
{
	Q_UNUSED( enabled );
	enableAndDisableModules();
}

void enableAndDisableModules()
{
	for( auto it = modules.begin(); it != modules.end(); ++it )
	{
		(*it)->setEnabled( settings->isPositionalAudioEnabled() &&
						   settings->getAudioBackend() == (*it)->providesAudioBackend() );
	}
}
