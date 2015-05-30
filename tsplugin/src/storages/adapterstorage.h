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

#include "../interfaces/storages.h"
#include <QMap>
#include <QObject>

namespace Storage
{

class AdapterStorage : public QObject, public Interfaces::AdapterStorage
{
public:
	AdapterStorage( QObject *parent );

	// from Interfaces::AdapterStorage
	Interfaces::AudioAdapter *getAudio( int backend ) const;
	QList<Interfaces::AudioAdapter*> getAudios() const;
	Interfaces::AudioAdapter *getTestAudio( int backend ) const;
	QList<Interfaces::AudioAdapter*> getTestAudios() const;
	Interfaces::VoiceChatAdapter *getVoiceChat() const;
	Interfaces::GameDataAdapter *getGameData() const;
	Interfaces::UiAdapter *getUi() const;

	// called from plugin.cpp
	void setAudio( int backend, Interfaces::AudioAdapter *adapter );
	void setTestAudio( int backend, Interfaces::AudioAdapter *adapter );
	void setVoiceChat( Interfaces::VoiceChatAdapter *adapter );
	void setGameData( Interfaces::GameDataAdapter *adapter );
	void setUi( Interfaces::UiAdapter *adapter );

private:
	QMap<int, Interfaces::AudioAdapter*> audioAdapters;
	QMap<int, Interfaces::AudioAdapter*> testAudioAdapters;
	Interfaces::VoiceChatAdapter *voiceChatAdapter;
	Interfaces::GameDataAdapter *gameDataAdapter;
	Interfaces::UiAdapter *uiAdapter;
};

}
