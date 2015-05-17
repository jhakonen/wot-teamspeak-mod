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

#include "../interfaces/drivers.h"
#include "../entities/vector.h"
#include "../utils/logging.h"
#include <ts3_functions.h>

namespace Driver
{
class TeamSpeakPluginPrivate;
class TeamSpeakAudioBackendPrivate;
class TeamSpeakAudioBackend;

class TeamSpeakPlugin : public QObject, public Log::Sink, public Interfaces::VoiceChatDriver
{
	Q_OBJECT

public:
	~TeamSpeakPlugin();
	static TeamSpeakPlugin *singleton();

	// from Log::Sink
	void logMessage( const QString &message, const char *channel, Log::Severity severity );

	// from Interfaces::VoiceChatDriver
	quint16 getMyUserId() const;
	QObject *qtObj();
	QString getPlaybackDeviceName() const;
	float getPlaybackVolume() const;

	void initialize();
	void onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels );
	void onCurrentServerConnectionChanged( uint64 serverConnectionHandlerID );
	void onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber );
	void onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage );
	void setAudioSink( Interfaces::AudioSink *sink );
	QString getPluginDataPath() const;
	void showSettingsUi( QWidget *parent );
	TeamSpeakAudioBackend *createAudioBackend();

signals:
	void chatUserAdded( quint16 id );
	void chatUserRemoved( quint16 id );
	void playbackDeviceChanged();
	void playbackVolumeChanged();
	void settingsUiRequested( QWidget *parent );

private slots:
	void onCheckTimeout();

private:
	TeamSpeakPlugin();
	QString getTSPlaybackDeviceName() const;
	QString getTSCurrentPlaybackDeviceName() const;
	QString getTSDefaultPlaybackDeviceName() const;
	float getTSPlaybackVolume() const;
	QList<anyID> getMyChannelClients() const;
	uint64 getMyChannelID() const;

private:
	TeamSpeakPluginPrivate *const d_ptr;
	Q_DECLARE_PRIVATE( TeamSpeakPlugin )
};

class TeamSpeakAudioBackend : public QObject, public Interfaces::AudioDriver
{
	Q_OBJECT

public:
	TeamSpeakAudioBackend( QObject *parent );
	~TeamSpeakAudioBackend();

	void onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float *volume );
	void onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float *volume );

	// from Interfaces::AudioDriver
	void setEnabled( bool enabled );
	bool isEnabled() const;
	void addUser( quint16 id );
	void removeUser( quint16 id );
	void positionUser( quint16 id, const Entity::Vector &position );
	void positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up );
	void setPlaybackDeviceName( const QString &/*name*/ ) {}
	void setPlaybackVolume( float /*volume*/ ) {}
	void setHrtfEnabled( bool /*enabled*/ ) {}
	void setHrtfDataSet( const QString &/*name*/ ) {}
	void setLoggingLevel( int /*level*/ ) {}
	QStringList getHrtfDataPaths() const { return QStringList(); }
	void playTestSound( const QString &filePath );
	void positionTestSound( const Entity::Vector &position );
	void stopTestSound();

private:
	TeamSpeakAudioBackendPrivate *const d_ptr;
	Q_DECLARE_PRIVATE( TeamSpeakAudioBackend )
};

}

