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

class QFileSystemWatcher;

namespace Driver
{

class OpenALBackendPrivate;

class OpenALBackend : public QObject, public Interfaces::AudioDriver, public Interfaces::AudioSink
{
	Q_OBJECT

public:
	OpenALBackend( QObject *parent );
	~OpenALBackend();

	// from Interfaces::AudioDriver
	void setEnabled( bool enabled );
	bool isEnabled() const;
	void removeUser( quint16 id );
	void positionUser( quint16 id, const Entity::Vector &position );
	void positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up );
	void setPlaybackDeviceName( const QString &name );
	void setPlaybackVolume( float volume );
	void setHrtfEnabled( bool enabled );
	void setHrtfDataSet( const QString &name );
	void setLoggingLevel( int level );
	QStringList getHrtfDataFileNames() const;
	void playTestSound( const QString &filePath );
	void positionTestSound( const Entity::Vector &position );
	void stopTestSound();

	// from Interfaces::AudioSink
	void onEditPlaybackVoiceDataEvent( quint16 id, short *samples, int sampleCount, int channels );

private:
	OpenALBackendPrivate *const d_ptr;
	Q_DECLARE_PRIVATE( OpenALBackend )
};

class OpenALConfFile : public QObject, public Interfaces::ConfigFilePathSource
{
	Q_OBJECT

public:
	OpenALConfFile( QObject *parent );
	~OpenALConfFile();

	void start();

	// from Interfaces::ConfigFilePathSource
	QString getFilePath() const;

private slots:
	void onFileChanged();

private:
	void createConfFile();
	void startListening();

private:
	QFileSystemWatcher *watcher;
};

}
