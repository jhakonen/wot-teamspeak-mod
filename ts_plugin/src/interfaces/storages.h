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

namespace Entity
{
class User;
class Camera;
class Settings;
}

namespace Interfaces
{

class AudioAdapter;
class VoiceChatAdapter;
class GameDataAdapter;
class UiAdapter;

class AdapterStorage
{
public:
	virtual ~AdapterStorage() {}
	virtual Interfaces::AudioAdapter* getAudio( int backend ) const = 0;
	virtual Interfaces::AudioAdapter* getTestAudio( int backend ) const = 0;
	virtual Interfaces::VoiceChatAdapter* getVoiceChat() const = 0;
	virtual Interfaces::GameDataAdapter* getGameData() const = 0;
	virtual Interfaces::UiAdapter* getUi() const = 0;
};

class UserStorage
{
public:
	virtual ~UserStorage() {}
	virtual bool has( quint16 id ) const = 0;
	virtual Entity::User get( quint16 id ) const = 0;
	virtual QList<Entity::User> getAll() const = 0;
	virtual void set( const Entity::User &user ) = 0;
	virtual void remove( quint16 id ) = 0;
};

class CameraStorage
{
public:
	virtual ~CameraStorage() {}
	virtual Entity::Camera get() const = 0;
	virtual void set( const Entity::Camera &camera ) = 0;
};

class SettingsStorage
{
public:
	virtual ~SettingsStorage() {}
	virtual Entity::Settings get() const = 0;
	virtual void set( const Entity::Settings &settings ) = 0;
};

}
