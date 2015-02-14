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

#include <QtGlobal>
#include <QVariant>

namespace Entity
{
class Vector;
enum Channels;
}

namespace Interfaces
{

class AudioDriver
{
public:
	virtual ~AudioDriver() {}
	virtual void setEnabled( bool enabled ) = 0;
	virtual bool isEnabled() const = 0;

	virtual void removeUser( quint16 id ) = 0;
	virtual void positionUser( quint16 id, const Entity::Vector &position ) = 0;
	virtual void positionCamera( const Entity::Vector &position, const Entity::Vector &forward, const Entity::Vector &up ) = 0;

	virtual void setPlaybackDeviceName( const QString &name ) = 0;
	virtual void setPlaybackVolume( float volume ) = 0;

	virtual void setChannels( Entity::Channels channels ) = 0;
	virtual void setHrtfEnabled( bool enabled ) = 0;
	virtual void setHrtfDataSet( const QString &name ) = 0;
	virtual void playTestSound( const QString &filePath ) = 0;
	virtual void positionTestSound( const Entity::Vector &position ) = 0;
	virtual void stopTestSound() = 0;
};

class VoiceChatDriver
{
public:
	virtual ~VoiceChatDriver() {}
	virtual quint16 getMyUserId() const = 0;
	virtual QObject* qtObj() = 0;
	virtual QString getPlaybackDeviceName() const = 0;
	virtual float getPlaybackVolume() const = 0;
};

class SettingsDriver
{
public:
	virtual ~SettingsDriver() {}
	virtual QVariant get( const QString &section, const QString &name, const QVariant &defaultValue = QVariant() ) = 0;
	virtual void set( const QString &section, const QString &name, const QVariant &value ) = 0;
};

class GameDataDriver
{
public:
	virtual ~GameDataDriver() {}
	virtual QObject* qtObj() = 0;
};

class AudioSink
{
public:
	virtual ~AudioSink() {}
	virtual void onEditPlaybackVoiceDataEvent( quint16 id, short *samples, int sampleCount, int channels ) = 0;
};

}
