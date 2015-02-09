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

#include "teamspeakplugin.h"
#include "../entities/enums.h"

#include <Windows.h>
#include <iostream>
#include <cassert>
#include <public_errors.h>
#include <ts3_functions.h>
#include <QApplication>
#include <QDir>
#include <QPointer>
#include <QSet>
#include <QTimer>
#include <QWidget>

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
PLUGINS_EXPORTDLL int ts3plugin_offersConfigure();
PLUGINS_EXPORTDLL void ts3plugin_configure( void* handle, void* qParentWidget );
PLUGINS_EXPORTDLL void ts3plugin_registerPluginID( const char* id );
PLUGINS_EXPORTDLL void ts3plugin_currentServerConnectionChanged( uint64 serverConnectionHandlerID );
PLUGINS_EXPORTDLL void ts3plugin_freeMemory( void* data );
PLUGINS_EXPORTDLL int ts3plugin_requestAutoload();
PLUGINS_EXPORTDLL void ts3plugin_initMenus( PluginMenuItem*** menuItems, char** menuIcon );

/* Clientlib */
PLUGINS_EXPORTDLL void ts3plugin_onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber );
PLUGINS_EXPORTDLL void ts3plugin_onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char* moveMessage );
PLUGINS_EXPORTDLL int  ts3plugin_onServerErrorEvent( uint64 serverConnectionHandlerID, const char* errorMessage, unsigned int error, const char* returnCode, const char* extraMessage );
PLUGINS_EXPORTDLL void ts3plugin_onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float* volume );
PLUGINS_EXPORTDLL void ts3plugin_onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume );
PLUGINS_EXPORTDLL void ts3plugin_onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels );

/* Client UI callbacks */
PLUGINS_EXPORTDLL void ts3plugin_onMenuItemEvent( uint64 serverConnectionHandlerID, enum PluginMenuType type, int menuItemID, uint64 selectedItemID );

#ifdef __cplusplus
}
#endif

extern void pluginInit( QObject *parent );
extern void pluginShutdown();

static char* gPluginID = NULL;
static TS3Functions gTs3Functions;
static QPointer<Driver::TeamSpeakPlugin> gTeamSpeakPlugin;
static QList<Driver::TeamSpeakAudioBackend*> gAudioBackends;

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

namespace {

TS3_VECTOR toTSVector( const Entity::Vector &vector )
{
	TS3_VECTOR tsVector;
	tsVector.x = vector.x;
	tsVector.y = vector.y;
	tsVector.z = vector.z;
	return tsVector;
}

QWidget* getMainWindowWidget()
{
	foreach( QWidget *widget, QApplication::topLevelWidgets() )
	{
		if( widget->isWindow() && widget->inherits( "QMainWindow" ) && !widget->windowTitle().isEmpty() )
		{
			return widget;
		}
	}
	return NULL;
}

LogLevel toTSLogLevel( Log::Severity severity )
{
	switch( severity )
	{
	case Log::Debug:
		return LogLevel_DEBUG;
	case Log::Info:
		return LogLevel_INFO;
	case Log::Warning:
		return LogLevel_WARNING;
	case Log::Error:
		return LogLevel_ERROR;
	}
	return LogLevel_INFO;
}

}

/*********************************** Required functions ************************************/
/*
 * If any of these required functions is not implemented, TS3 will refuse to load the plugin
 */

/* Unique name identifying this plugin */
const char* ts3plugin_name()
{
	return "TessuMod Plugin";
}

/* Plugin version */
const char* ts3plugin_version()
{
	return "0.1";
}

/* Plugin API version. Must be the same as the clients API major version, else the plugin fails to load. */
int ts3plugin_apiVersion()
{
	return PLUGIN_API_VERSION;
}

/* Plugin author */
const char* ts3plugin_author()
{
	return "jhakonen @ EU";
}

/* Plugin description */
const char* ts3plugin_description()
{
	return "This plugin provides positional audio support for World of Tanks.";
}

/* Set TeamSpeak 3 callback functions */
void ts3plugin_setFunctionPointers( const struct TS3Functions funcs )
{
	gTs3Functions = funcs;
}

/*
 * Custom code called right after loading the plugin. Returns 0 on success, 1 on failure.
 * If the function returns 1 on failure, the plugin will be unloaded again.
 */
int ts3plugin_init()
{
	pluginInit( Driver::TeamSpeakPlugin::singleton() );
	return 0;  /* 0 = success, 1 = failure, -2 = failure but client will not show a "failed to load" warning */
	/* -2 is a very special case and should only be used if a plugin displays a dialog (e.g. overlay) asking the user to disable
	 * the plugin again, avoiding the show another dialog by the client telling the user the plugin failed to load.
	 * For normal case, if a plugin really failed to load because of an error, the correct return value is 1. */
}

/* Custom code called right before the plugin is unloaded */
void ts3plugin_shutdown()
{
	pluginShutdown();
	delete [] gPluginID;
	gPluginID = NULL;
	delete Driver::TeamSpeakPlugin::singleton();
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
	Q_UNUSED( handle );
	Driver::TeamSpeakPlugin::singleton()->showSettingsUi( (QWidget*)qParentWidget );
}

/*
 * If the plugin wants to use error return codes, plugin commands, hotkeys or menu items, it needs to register a command ID. This function will be
 * automatically called after the plugin was initialized. This function is optional. If you don't use these features, this function can be omitted.
 * Note the passed pluginID parameter is no longer valid after calling this function, so you must copy it and store it in the plugin.
 */
void ts3plugin_registerPluginID( const char* id )
{
	size_t size = strlen( id ) + 1;
	gPluginID = new char[strlen( id ) + 1];
	strncpy_s( gPluginID, size, id, size );
	printf( "PLUGIN: registerPluginID: %s\n", gPluginID );
}

/* Client changed current server connection handler */
void ts3plugin_currentServerConnectionChanged( uint64 serverConnectionHandlerID )
{
	Driver::TeamSpeakPlugin::singleton()->onCurrentServerConnectionChanged( serverConnectionHandlerID );
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
int ts3plugin_requestAutoload()
{
	return 1;  /* 1 = request autoloaded, 0 = do not request autoload */
}

/* Helper function to create a menu item */
static struct PluginMenuItem* createMenuItem( PluginMenuType type, int id, const char* text )
{
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
	CREATE_MENU_ITEM( PLUGIN_MENU_TYPE_GLOBAL,  Entity::MENU_ID_GLOBAL_SETTINGS,  "Settings" );
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
	Driver::TeamSpeakPlugin::singleton()->onConnectStatusChangeEvent( serverConnectionHandlerID, newStatus, errorNumber );
}

void ts3plugin_onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage )
{
	Log::debug() << "onClientMoveEvent() :: "
				 << "clientID: " << clientID << ", "
				 << "oldChannelID: " << oldChannelID << ", "
				 << "newChannelID: " << newChannelID << ", "
				 << "visibility: " << visibility;
	Driver::TeamSpeakPlugin::singleton()->onClientMoveEvent( serverConnectionHandlerID, clientID, oldChannelID, newChannelID, visibility, moveMessage );
}

int ts3plugin_onServerErrorEvent(uint64 serverConnectionHandlerID, const char* errorMessage, unsigned int error, const char* returnCode, const char* extraMessage)
{
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

void ts3plugin_onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float* volume )
{
	foreach( auto backend, gAudioBackends )
	{
		backend->onCustom3dRolloffCalculationClientEvent( serverConnectionHandlerID, clientID, distance, volume );
	}
}

void ts3plugin_onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume )
{
	foreach( auto backend, gAudioBackends )
	{
		backend->onCustom3dRolloffCalculationWaveEvent( serverConnectionHandlerID, waveHandle, distance, volume );
	}
}

void ts3plugin_onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels )
{
	Driver::TeamSpeakPlugin::singleton()->onEditPlaybackVoiceDataEvent( serverConnectionHandlerID, clientID, samples, sampleCount, channels );
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
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( selectedItemID );

	switch( type )
	{
	case PLUGIN_MENU_TYPE_GLOBAL:
		switch( menuItemID )
		{
		case Entity::MENU_ID_GLOBAL_SETTINGS:
			Driver::TeamSpeakPlugin::singleton()->showSettingsUi( getMainWindowWidget() );
			break;
		default:
			break;
		}
		break;
	default:
		break;
	}
}

namespace Driver
{

class TeamSpeakPluginPrivate
{
public:
	TeamSpeakPluginPrivate( TeamSpeakPlugin *q )
		: audioSink( NULL ), previousPlaybackVolume( 0 ), checkTimer( new QTimer( q ) )
	{
	}

	QSet<anyID> clientsInChannel;
	Interfaces::AudioSink *audioSink;
	mutable QString previousPlaybackDeviceName;
	mutable float previousPlaybackVolume;
	QTimer *checkTimer;
};

TeamSpeakPlugin::TeamSpeakPlugin()
	: d_ptr( new TeamSpeakPluginPrivate( this ) )
{
}

TeamSpeakPlugin::~TeamSpeakPlugin()
{
	Q_D( TeamSpeakPlugin );
	delete d;
}

TeamSpeakPlugin *TeamSpeakPlugin::singleton()
{
	if( !gTeamSpeakPlugin )
	{
		gTeamSpeakPlugin = new TeamSpeakPlugin();
	}
	return gTeamSpeakPlugin;
}

void TeamSpeakPlugin::logMessage( const QString &message, Log::Severity severity )
{
	QByteArray utf8Message = message.toUtf8();
	gTs3Functions.logMessage( utf8Message.data(), toTSLogLevel( severity ), "TessuMod Plugin", 0 );
}

quint16 TeamSpeakPlugin::getMyUserId() const
{
	anyID myID;
	if( gTs3Functions.getClientID( gTs3Functions.getCurrentServerConnectionHandlerID(), &myID ) != ERROR_ok )
	{
		return 0;
	}
	return myID;
}

QObject *TeamSpeakPlugin::qtObj()
{
	return this;
}

QString TeamSpeakPlugin::getPlaybackDeviceName() const
{
	Q_D( const TeamSpeakPlugin );
	d->previousPlaybackDeviceName = getTSPlaybackDeviceName();
	return d->previousPlaybackDeviceName;
}

float TeamSpeakPlugin::getPlaybackVolume() const
{
	Q_D( const TeamSpeakPlugin );
	d->previousPlaybackVolume = getTSPlaybackVolume();
	return d->previousPlaybackVolume;
}

void TeamSpeakPlugin::initialize()
{
	Q_D( TeamSpeakPlugin );
	foreach( anyID clientID, getMyChannelClients() )
	{
		emit chatUserAdded( clientID );
		d->clientsInChannel.insert( clientID );
	}
	connect( d->checkTimer, SIGNAL(timeout()), this, SLOT(onCheckTimeout()) );
	d->checkTimer->setInterval( 3000 );
	d->checkTimer->setSingleShot( false );
	d->checkTimer->start();
}

void TeamSpeakPlugin::onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short *samples, int sampleCount, int channels )
{
	Q_D( TeamSpeakPlugin );
	if( gTs3Functions.getCurrentServerConnectionHandlerID() == serverConnectionHandlerID )
	{
		d->audioSink->onEditPlaybackVoiceDataEvent( clientID, samples, sampleCount, channels );
	}
}

void TeamSpeakPlugin::onCurrentServerConnectionChanged( uint64 serverConnectionHandlerID )
{
	Q_D( TeamSpeakPlugin );
	Q_UNUSED( serverConnectionHandlerID );
	foreach( anyID clientID, d->clientsInChannel )
	{
		emit chatUserRemoved( clientID );
	}
	d->clientsInChannel.clear();
	foreach( anyID clientID, getMyChannelClients() )
	{
		emit chatUserAdded( clientID );
		d->clientsInChannel.insert( clientID );
	}
}

void TeamSpeakPlugin::onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber )
{
	Q_D( TeamSpeakPlugin );
	Q_UNUSED( errorNumber );
	if( gTs3Functions.getCurrentServerConnectionHandlerID() != serverConnectionHandlerID )
	{
		return;
	}
	if( STATUS_DISCONNECTED == newStatus )
	{
		foreach( anyID clientID, d->clientsInChannel )
		{
			emit chatUserRemoved( clientID );
		}
		d->clientsInChannel.clear();
	}
	if( STATUS_CONNECTION_ESTABLISHED == newStatus )
	{
		foreach( anyID clientID, getMyChannelClients() )
		{
			emit chatUserAdded( clientID );
			d->clientsInChannel.insert( clientID );
		}
	}
}

void TeamSpeakPlugin::onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage )
{
	Q_D( TeamSpeakPlugin );
	Q_UNUSED( visibility );
	Q_UNUSED( moveMessage );
	if( gTs3Functions.getCurrentServerConnectionHandlerID() != serverConnectionHandlerID )
	{
		return;
	}
	// I moved to a new channel
	if( getMyUserId() == clientID )
	{
		Log::debug() << "I moved to new channel";
		foreach( anyID clientID, d->clientsInChannel )
		{
			emit chatUserRemoved( clientID );
		}
		d->clientsInChannel.clear();
		foreach( anyID clientID, getMyChannelClients() )
		{
			emit chatUserAdded( clientID );
			d->clientsInChannel.insert( clientID );
		}
		return;
	}
	// someone else moved to my channel
	else if( getMyChannelID() == newChannelID )
	{
		Log::debug() << "Client " << clientID << " entered my channel";
		emit chatUserAdded( clientID );
		d->clientsInChannel.insert( clientID );
	}
	// someone else moved away from my channel
	else if( getMyChannelID() == oldChannelID )
	{
		Log::debug() << "Client " << clientID << " left my channel";
		d->clientsInChannel.remove( clientID );
		emit chatUserRemoved( clientID );
	}
}

void TeamSpeakPlugin::setAudioSink( Interfaces::AudioSink *sink )
{
	Q_D( TeamSpeakPlugin );
	d->audioSink = sink;
}

QString TeamSpeakPlugin::getPluginDataPath() const
{
	char pluginPath[512];
	gTs3Functions.getPluginPath( pluginPath, 512 );
	return QDir::cleanPath( QString( pluginPath ) + "/tessumod_plugin" );
}

void TeamSpeakPlugin::showSettingsUi( QWidget *parent )
{
	emit settingsUiRequested( parent );
}

TeamSpeakAudioBackend *TeamSpeakPlugin::createAudioBackend()
{
	auto backend = new TeamSpeakAudioBackend( this );
	gAudioBackends.append( backend );
	return backend;
}

void TeamSpeakPlugin::onCheckTimeout()
{
	Q_D( TeamSpeakPlugin );
	QString deviceName = getTSPlaybackDeviceName();
	if( d->previousPlaybackDeviceName != deviceName )
	{
		d->previousPlaybackDeviceName = deviceName;
		emit playbackDeviceChanged();
	}

	float volume = getTSPlaybackVolume();
	if( d->previousPlaybackVolume != volume )
	{
		d->previousPlaybackVolume = volume;
		emit playbackVolumeChanged();
	}
}

QString TeamSpeakPlugin::getTSPlaybackDeviceName() const
{
	QString name = getTSCurrentPlaybackDeviceName();
	if( name.isEmpty() )
	{
		name = getTSDefaultPlaybackDeviceName();
	}
	return name;
}

QString TeamSpeakPlugin::getTSCurrentPlaybackDeviceName() const
{
	QString result;
	char *playbackMode;
	if( gTs3Functions.getCurrentPlayBackMode( gTs3Functions.getCurrentServerConnectionHandlerID(), &playbackMode ) == ERROR_ok )
	{
		char* playbackDeviceID;
		if( gTs3Functions.getCurrentPlaybackDeviceName( gTs3Functions.getCurrentServerConnectionHandlerID(), &playbackDeviceID, NULL ) == ERROR_ok )
		{
			char*** deviceList;
			if( gTs3Functions.getPlaybackDeviceList( playbackMode, &deviceList ) == ERROR_ok )
			{
				for( int i = 0; deviceList[i] != NULL; ++i)
				{
					if( strcmp( playbackDeviceID, deviceList[i][1] ) == 0 )
					{
						result = QString::fromUtf8( deviceList[i][0] );
					}
					gTs3Functions.freeMemory( deviceList[i][0] );
					gTs3Functions.freeMemory( deviceList[i][1] );
					gTs3Functions.freeMemory( deviceList[i] );
				}
				gTs3Functions.freeMemory( deviceList );
			}
			gTs3Functions.freeMemory( playbackDeviceID );
		}
	}
	return result;
}

QString TeamSpeakPlugin::getTSDefaultPlaybackDeviceName() const
{
	QString result;
	char* defaultMode;
	if( gTs3Functions.getDefaultPlayBackMode( &defaultMode ) == ERROR_ok )
	{
		char** defaultPlaybackDevice;
		if( gTs3Functions.getDefaultPlaybackDevice( defaultMode, &defaultPlaybackDevice) == ERROR_ok )
		{
			result = QString::fromUtf8( defaultPlaybackDevice[0] );
			gTs3Functions.freeMemory( defaultPlaybackDevice[0] );
			gTs3Functions.freeMemory( defaultPlaybackDevice[1] );
			gTs3Functions.freeMemory( defaultPlaybackDevice );
		}
		else
		{
			Log::error() << "Failed to get default playback device";
		}
		gTs3Functions.freeMemory( defaultMode );
	}
	else
	{
		Log::error() << "Failed to get default playback mode";
	}
	return result;
}

float TeamSpeakPlugin::getTSPlaybackVolume() const
{
	float volume = 0;
	gTs3Functions.getPlaybackConfigValueAsFloat( gTs3Functions.getCurrentServerConnectionHandlerID(), "volume_modifier", &volume );
	return volume;
}

QList<anyID> TeamSpeakPlugin::getMyChannelClients() const
{
	anyID* clients;
	QList<anyID> results;
	uint64 channelId = getMyChannelID();
	if( channelId == -1 )
	{
		return results;
	}
	gTs3Functions.getChannelClientList( gTs3Functions.getCurrentServerConnectionHandlerID(), getMyChannelID(), &clients );
	for( int i = 0; clients[i] != NULL; i++ )
	{
		if( clients[i] != getMyUserId() )
		{
			results.append( clients[i] );
		}
	}
	gTs3Functions.freeMemory( clients );
	return results;
}

uint64 TeamSpeakPlugin::getMyChannelID() const
{
	uint64 myID = -1;
	gTs3Functions.getChannelOfClient( gTs3Functions.getCurrentServerConnectionHandlerID(), getMyUserId(), &myID );
	return myID;
}

class TeamSpeakAudioBackendPrivate
{
public:
	TeamSpeakAudioBackendPrivate()
		: isEnabled( false )
	{
	}

public:
	Entity::Vector origo;
	QMap<quint16, Entity::Vector> clientPositions;
	bool isEnabled;
};

TeamSpeakAudioBackend::TeamSpeakAudioBackend( QObject *parent )
	: QObject( parent ), d_ptr( new TeamSpeakAudioBackendPrivate )
{

}

TeamSpeakAudioBackend::~TeamSpeakAudioBackend()
{
	Q_D( TeamSpeakAudioBackend );
	delete d;
}

void TeamSpeakAudioBackend::onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float *volume )
{
	Q_D( TeamSpeakAudioBackend );
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( distance );
	if( d->isEnabled && gTs3Functions.getCurrentServerConnectionHandlerID() == serverConnectionHandlerID && d->clientPositions.contains( clientID ) )
	{
		*volume = 1.0;
	}
}

void TeamSpeakAudioBackend::onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float *volume )
{
	Q_D( TeamSpeakAudioBackend );
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( waveHandle );
	Q_UNUSED( distance );
	if( d->isEnabled && gTs3Functions.getCurrentServerConnectionHandlerID() == serverConnectionHandlerID )
	{
		*volume = 1.0;
	}
}

void TeamSpeakAudioBackend::setEnabled( bool enabled )
{
	Q_D( TeamSpeakAudioBackend );
	d->isEnabled = enabled;
}

bool TeamSpeakAudioBackend::isEnabled() const
{
	Q_D( const TeamSpeakAudioBackend );
	return d->isEnabled;
}

void TeamSpeakAudioBackend::addUser( quint16 id )
{
	Q_D( TeamSpeakAudioBackend );
	Log::debug() << "TeamSpeakAudioBackend::addUser() :: id: " << id;
	d->clientPositions[id] = Entity::Vector();
}

void TeamSpeakAudioBackend::removeUser( quint16 id )
{
	Q_D( TeamSpeakAudioBackend );
	Log::debug() << "TeamSpeakAudioBackend::removeUser() :: id: " << id;
	d->clientPositions.remove( id );
	TS3_VECTOR zero = {0, 0, 0};
	gTs3Functions.channelset3DAttributes( gTs3Functions.getCurrentServerConnectionHandlerID(), id, &zero );
}


void TeamSpeakAudioBackend::positionUser( quint16 id, const Entity::Vector &position )
{
	Q_D( TeamSpeakAudioBackend );
	//Log::debug() << "TeamSpeakAudioBackend::positionUser() :: id: " << id << ", pos: " << position;
	d->clientPositions[id] = position;
	TS3_VECTOR tsPosition = toTSVector( position - d->origo );
	gTs3Functions.channelset3DAttributes( gTs3Functions.getCurrentServerConnectionHandlerID(), id, &tsPosition );
}

void TeamSpeakAudioBackend::positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up )
{
	Q_D( TeamSpeakAudioBackend );
	//Log::debug() << "TeamSpeakAudioBackend::positionCamera() :: pos: " << position << ", forward: " << forward << ", up: " << up;
	d->origo = position;
	foreach( quint16 id, d->clientPositions.keys() )
	{
		TS3_VECTOR tsPosition = toTSVector( d->clientPositions[id] - d->origo );
		gTs3Functions.channelset3DAttributes( gTs3Functions.getCurrentServerConnectionHandlerID(), id, &tsPosition );
	}
	TS3_VECTOR tsPosition = {0, 0, 0};
	TS3_VECTOR tsForward = toTSVector( forward );
	TS3_VECTOR tsUp = toTSVector( up );
	gTs3Functions.systemset3DListenerAttributes( gTs3Functions.getCurrentServerConnectionHandlerID(), &tsPosition, &tsForward, &tsUp );
}

}
