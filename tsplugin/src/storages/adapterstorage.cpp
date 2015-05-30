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

#include "adapterstorage.h"

namespace Storage
{

AdapterStorage::AdapterStorage( QObject *parent )
	: QObject( parent ), voiceChatAdapter( NULL ), gameDataAdapter( NULL ),
	  uiAdapter( NULL )
{
}

Interfaces::AudioAdapter *AdapterStorage::getAudio( int backend ) const
{
	return audioAdapters.value( backend, NULL );
}

QList<Interfaces::AudioAdapter*> AdapterStorage::getAudios() const
{
	return audioAdapters.values();
}

Interfaces::AudioAdapter *AdapterStorage::getTestAudio( int backend ) const
{
	return testAudioAdapters.value( backend, NULL );
}

QList<Interfaces::AudioAdapter *> AdapterStorage::getTestAudios() const
{
	return testAudioAdapters.values();
}

Interfaces::VoiceChatAdapter *AdapterStorage::getVoiceChat() const
{
	return voiceChatAdapter;
}

Interfaces::GameDataAdapter *AdapterStorage::getGameData() const
{
	return gameDataAdapter;
}

Interfaces::UiAdapter *AdapterStorage::getUi() const
{
	return uiAdapter;
}

void AdapterStorage::setAudio( int backend, Interfaces::AudioAdapter *adapter )
{
	audioAdapters[backend] = adapter;
}

void AdapterStorage::setTestAudio( int backend, Interfaces::AudioAdapter *adapter )
{
	testAudioAdapters[backend] = adapter;
}

void AdapterStorage::setVoiceChat( Interfaces::VoiceChatAdapter *adapter )
{
	voiceChatAdapter = adapter;
}

void AdapterStorage::setGameData( Interfaces::GameDataAdapter *adapter )
{
	gameDataAdapter = adapter;
}

void AdapterStorage::setUi( Interfaces::UiAdapter *adapter )
{
	uiAdapter = adapter;
}

}
