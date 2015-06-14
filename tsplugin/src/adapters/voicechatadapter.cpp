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

#include "voicechatadapter.h"
#include "../interfaces/drivers.h"
#include "../interfaces/usecasefactory.h"

namespace Adapter
{

VoiceChatAdapter::VoiceChatAdapter( Interfaces::VoiceChatDriver* driver, Interfaces::UseCaseFactory *useCaseFactory, QObject *parent )
	: QObject( parent ), driver( driver ), useCaseFactory( useCaseFactory )
{
	connect( driver->qtObj(), SIGNAL(chatUserAdded(quint16)),
			 this,            SLOT(onChatUserAdded(quint16)) );
	connect( driver->qtObj(), SIGNAL(chatUserRemoved(quint16)),
			 this,            SLOT(onChatUserRemoved(quint16)) );
	connect( driver->qtObj(), SIGNAL(playbackDeviceChanged()),
			 this,            SLOT(onPlaybackDeviceChanged()) );
	connect( driver->qtObj(), SIGNAL(playbackVolumeChanged()),
			 this,            SLOT(onPlaybackVolumeChanged()) );
	connect( driver->qtObj(), SIGNAL(settingsUiRequested(QWidget*)),
			 this,            SLOT(onSettingsUiRequested(QWidget*)) );
	connect( driver->qtObj(), SIGNAL(pluginHelpRequested()),
			 this,            SLOT(onPluginHelpRequested()) );
}

quint16 VoiceChatAdapter::getMyUserId() const
{
	return driver->getMyUserId();
}

QString VoiceChatAdapter::getPlaybackDeviceName() const
{
	return driver->getPlaybackDeviceName();
}

float VoiceChatAdapter::getPlaybackVolume() const
{
	return driver->getPlaybackVolume();
}

void VoiceChatAdapter::onChatUserAdded( quint16 id )
{
	useCaseFactory->addChatUser( id );
}

void VoiceChatAdapter::onChatUserRemoved( quint16 id )
{
	useCaseFactory->removeChatUser( id );
}

void VoiceChatAdapter::onPlaybackDeviceChanged()
{
	useCaseFactory->changePlaybackDevice();
}

void VoiceChatAdapter::onPlaybackVolumeChanged()
{
	useCaseFactory->changePlaybackVolume();
}

void VoiceChatAdapter::onSettingsUiRequested( QWidget *parent )
{
	useCaseFactory->showSettingsUi( parent );
}

void VoiceChatAdapter::onPluginHelpRequested()
{
	useCaseFactory->showPluginHelp();
}

}
