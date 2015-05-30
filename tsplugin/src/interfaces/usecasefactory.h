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

namespace Entity
{
class Vector;
class Settings;
}

namespace Interfaces
{

class UseCaseFactory
{
public:
	typedef std::function<void(QVariant)> Callback;

	virtual ~UseCaseFactory() {}
	virtual void applicationInitialize() = 0;
	virtual void positionUser( quint16 id, const Entity::Vector& position ) = 0;
	virtual void positionCamera( const Entity::Vector& position, const Entity::Vector& direction ) = 0;
	virtual void addGameUser( quint16 id ) = 0;
	virtual void removeGameUser( quint16 id ) = 0;
	virtual void addChatUser( quint16 id ) = 0;
	virtual void removeChatUser( quint16 id ) = 0;
	virtual void changePlaybackDevice() = 0;
	virtual void changePlaybackVolume() = 0;
	virtual void showSettingsUi( QWidget *parent ) = 0;
	virtual void saveSettings( const Entity::Settings &settings ) = 0;
	virtual void playTestAudioWithSettings( const Entity::Settings &settings, Callback result ) = 0;
};

}
