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

#include "../interfaces/adapters.h"
#include <QObject>

namespace Interfaces
{
class UseCaseFactory;
class VoiceChatDriver;
}

namespace Adapter
{

class VoiceChatAdapter : public QObject, public Interfaces::VoiceChatAdapter
{
	Q_OBJECT

public:
	VoiceChatAdapter( Interfaces::VoiceChatDriver* driver, Interfaces::UseCaseFactory *useCaseFactory, QObject *parent );

	quint16 getMyUserId() const;
	QString getPlaybackDeviceName() const;
	float getPlaybackVolume() const;

private slots:
	void onChatUserAdded( quint16 id );
	void onChatUserRemoved( quint16 id );
	void onPlaybackDeviceChanged();
	void onPlaybackVolumeChanged();
	void onSettingsUiRequested( QWidget *parent );

private:
	Interfaces::VoiceChatDriver* driver;
	Interfaces::UseCaseFactory *useCaseFactory;
};

}
