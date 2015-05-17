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
#include <functional>

class QWidget;
class QVariant;
class QStringList;

namespace Entity
{
class User;
class Camera;
class Vector;
class Settings;
enum RotateMode;
}

namespace Interfaces
{

class AudioAdapter
{
public:
	typedef std::function<void(QVariant)> Callback;

	virtual ~AudioAdapter() {}
	virtual void positionUser( const Entity::User &user ) = 0;
	virtual void removeUser( const Entity::User &user ) = 0;
	virtual void positionCamera( const Entity::Camera &camera ) = 0;

	virtual void setPlaybackDeviceName( const QString &name ) = 0;
	virtual void setPlaybackVolume( float volume ) = 0;

	virtual void setEnabled( bool enabled ) = 0;

	virtual void setHrtfEnabled( bool enabled ) = 0;
	virtual void setHrtfDataSet( const QString &name ) = 0;
	virtual QStringList getHrtfDataPaths() const = 0;
	virtual void playTestSound( Entity::RotateMode mode, Callback result ) = 0;
	virtual void setLoggingLevel( int level ) = 0;
};

class VoiceChatAdapter
{
public:
	virtual ~VoiceChatAdapter() {}
	virtual quint16 getMyUserId() const = 0;
	virtual QString getPlaybackDeviceName() const = 0;
	virtual float getPlaybackVolume() const = 0;
};

class GameDataAdapter
{
public:
	virtual ~GameDataAdapter() {}
};

class UiAdapter
{
public:
	virtual ~UiAdapter() {}
	virtual void showSettingsUi( const Entity::Settings &settings, const QStringList &hrtfDataNames, QWidget *parent ) = 0;
};

}
