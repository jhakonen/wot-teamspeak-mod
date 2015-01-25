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

#include "modulebase.h"
#include <ts3_functions.h>
#include <AL/al.h>
#include <AL/alc.h>
#include <AL/alext.h>
#include <QPointer>
#include <QMutex>
#include <QMap>
#include <QSet>
#include <functional>

class QTimer;

template< typename TKey, typename TValue >
class SyncronizedMap
{
public:
	SyncronizedMap( const std::function<void(TValue)> &deleter = [](TValue) {} ) : deleter( deleter )
	{
	}

	bool contains( const TKey &key )
	{
		QMutexLocker locker( &mutex );
		return map.contains( key );
	}

	TValue& operator[]( const TKey &key )
	{
		QMutexLocker locker( &mutex );
		return map[key];
	}

	const TValue operator[]( const TKey &key ) const
	{
		QMutexLocker locker( &mutex );
		return map[key];
	}

	void remove( const TKey &key )
	{
		QMutexLocker locker( &mutex );
		deleter( map.take( key ) );
	}

	void clear()
	{
		QMutexLocker locker( &mutex );
		foreach( TValue value, map.values() ) {
			deleter( value );
		}
		map.clear();
	}

	TValue take( const TKey &key )
	{
		QMutexLocker locker( &mutex );
		return map.take( key );
	}

	QList<TValue> takeAllValues()
	{
		QMutexLocker locker( &mutex );
		auto values = map.values();
		map.clear();
		return values;
	}

private:
	std::function<void(TValue)> deleter;
	QMap<TKey, TValue> map;
	QMutex mutex;
};

class PositionalAudioOpenAL : public ModuleBase
{
	Q_OBJECT

public:
	PositionalAudioOpenAL( const TS3Functions ts3Interface, QObject *parent = 0 );
	~PositionalAudioOpenAL();

	void init();
	int providesAudioBackend() const;

	void onConnectStatusChangeEvent( uint64 serverConnectionHandlerID, int newStatus, unsigned int errorNumber );
	void onClientMoveEvent( uint64 serverConnectionHandlerID, anyID clientID, uint64 oldChannelID, uint64 newChannelID, int visibility, const char *moveMessage );
	void onEditPlaybackVoiceDataEvent( uint64 serverConnectionHandlerID, anyID clientID, short* samples, int sampleCount, int channels );

	void enable();
	void disable();
	void onCameraPositionChanged( TS3_VECTOR position );
	void onCameraDirectionChanged( TS3_VECTOR direction );
	void onClientAdded( anyID clientID, TS3_VECTOR position );
	void onClientPositionChanged( anyID clientID, TS3_VECTOR position );
	void onClientRemoved( anyID clientID );

public slots:
	void onCheckTimeout();

private:
	void onClientEnterMyChannel( anyID clientID );
	void onClientLeftMyChannel( anyID clientID );

	bool isNotMyClientID( anyID clientID ) const;
	anyID getMyClientID() const;
	uint64 getMyChannelID() const;
	QList<anyID> getMyChannelClients() const;
	QString getOALConfigPath() const;
	QString getAppdataPath() const;
	QString getOALHRTFPath() const;
	QString getTSPlaybackDeviceName() const;
	QString getTSCurrentPlaybackDeviceName() const;
	QString getTSDefaultPlaybackDeviceName() const;

	static bool isOALOk();
	static bool isOALContextOk( ALCdevice *device );
	static ALuint createOALSource();
	static void deleteOALSource( ALuint source );
	static void setSourcePosition( ALuint source, TS3_VECTOR position );
	static void clearSourcePosition( ALuint source );
	static void deleteOALProcessedSourceBuffers( ALuint source );
	static ALfloat tsVolumeModifierToOALGain(float tsVolumeModifier );

private:
	const TS3Functions ts3Interface;
	SyncronizedMap<anyID, TS3_VECTOR> clientPositions;
	SyncronizedMap<anyID, ALuint> clientSources;
	QSet<anyID> clientsInChannel;
	ALCdevice *device;
	ALCcontext *context;
	QPointer<QTimer> checkTimer;
	QString previousDeviceName;
	bool isEnabled;
};
