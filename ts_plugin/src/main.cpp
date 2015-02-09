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

#include "usecases/usecasefactory.h"
#include "storages/userstorage.h"
#include "storages/camerastorage.h"
#include "storages/adapterstorage.h"
#include "storages/settingsstorage.h"
#include "adapters/audioadapter.h"
#include "adapters/voicechatadapter.h"
#include "adapters/gamedataadapter.h"
#include "adapters/uiadapter.h"
#include "drivers/teamspeakplugin.h"
#include "drivers/inisettingsfile.h"
#include "drivers/openalbackend.h"
#include "drivers/wotconnector.h"

#include <QObject>
#include <QDir>
#include <Windows.h>

static DLL_DIRECTORY_COOKIE dllSearchCookie;

void pluginInit( QObject *parent )
{
	auto teamSpeakPlugin = Driver::TeamSpeakPlugin::singleton();

	Log::setSink( teamSpeakPlugin );
	QString dataPath = QDir::toNativeSeparators( teamSpeakPlugin->getPluginDataPath() );
	dllSearchCookie = AddDllDirectory( (wchar_t*)dataPath.utf16() );

	auto iniSettingsFile = new Driver::IniSettingsFile( parent );
	auto openALBackend = new Driver::OpenALBackend( parent );
	auto openALBackendTest = new Driver::OpenALBackend( parent );
	auto wotConnector = new Driver::WotConnector( parent );

	auto userStorage = new Storage::UserStorage( parent );
	auto cameraStorage = new Storage::CameraStorage( parent );
	auto adapterStorage = new Storage::AdapterStorage( parent );
	auto settingsStorage = new Storage::SettingsStorage( iniSettingsFile, parent );

	auto useCaseFactory = new UseCase::UseCaseFactory( parent );
	useCaseFactory->userStorage = userStorage;
	useCaseFactory->cameraStorage = cameraStorage;
	useCaseFactory->settingsStorage = settingsStorage;
	useCaseFactory->adapterStorage = adapterStorage;

	adapterStorage->setAudio( Entity::BuiltInBackend, new Adapter::AudioAdapter( teamSpeakPlugin->createAudioBackend(), parent ) );
	adapterStorage->setAudio( Entity::OpenALBackend, new Adapter::AudioAdapter( openALBackend, parent ) );
	adapterStorage->setTestAudio( Entity::BuiltInBackend, new Adapter::AudioAdapter( teamSpeakPlugin->createAudioBackend(), parent ) );
	adapterStorage->setTestAudio( Entity::OpenALBackend, new Adapter::AudioAdapter( openALBackendTest, parent ) );
	adapterStorage->setVoiceChat( new Adapter::VoiceChatAdapter( teamSpeakPlugin, useCaseFactory, parent ) );
	adapterStorage->setGameData( new Adapter::GameDataAdapter( wotConnector, useCaseFactory, parent ) );
	adapterStorage->setUi( new Adapter::UiAdapter( useCaseFactory, parent ) );

	teamSpeakPlugin->setAudioSink( openALBackend );

	teamSpeakPlugin->initialize();
	wotConnector->initialize();
	useCaseFactory->applicationInitialize();
}

void pluginShutdown()
{
	RemoveDllDirectory( dllSearchCookie );
}
