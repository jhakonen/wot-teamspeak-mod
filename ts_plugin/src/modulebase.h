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

#include <QObject>
#include <public_definitions.h>

class ModuleBase : public QObject
{
	Q_OBJECT

public:
	ModuleBase( QObject *parent = 0 )
		: QObject( parent )
	{
	}

	void setServerConnectionHandlerID( uint64 id )
	{
		serverConnectionHandlerID = id;
	}

	uint64 getServerConnectionHandlerID() const
	{
		return serverConnectionHandlerID;
	}

	virtual void init()	{}

	virtual int getAudioBackend() const = 0;
	virtual void onConnectStatusChangeEvent( uint64 /*serverConnectionHandlerID*/, int /*newStatus*/, unsigned int /*errorNumber*/ ) {}
	virtual void onClientMoveEvent( uint64 /*serverConnectionHandlerID*/, anyID /*clientID*/, uint64 /*oldChannelID*/, uint64 /*newChannelID*/, int /*visibility*/, const char * /*moveMessage*/ ) {}
	virtual void onCustom3dRolloffCalculationClientEvent( uint64 /*serverConnectionHandlerID*/, anyID /*clientID*/, float /*distance*/, float* /*volume*/ ) {}
	virtual void onCustom3dRolloffCalculationWaveEvent( uint64 /*serverConnectionHandlerID*/, uint64 /*waveHandle*/, float /*distance*/, float* /*volume*/ ) {}
	virtual void onEditPlaybackVoiceDataEvent( uint64 /*serverConnectionHandlerID*/, anyID /*clientID*/, short* /*samples*/, int /*sampleCount*/, int /*channels*/ ) {}
	virtual void onEditPostProcessVoiceDataEvent( uint64 /*serverConnectionHandlerID*/, anyID /*clientID*/, short* /*samples*/, int /*sampleCount*/, int /*channels*/, const unsigned int* /*channelSpeakerArray*/, unsigned int* /*channelFillMask*/ ) {}
	virtual void onEditMixedPlaybackVoiceDataEvent( uint64 /*serverConnectionHandlerID*/, short* /*samples*/, int /*sampleCount*/, int /*channels*/, const unsigned int* /*channelSpeakerArray*/, unsigned int* /*channelFillMask*/ ) {}

public slots:
	virtual void onCameraPositionChanged( TS3_VECTOR /*position*/ ) {}
	virtual void onCameraDirectionChanged( TS3_VECTOR /*direction*/ ) {}
	virtual void onClientAdded( anyID /*clientID*/, TS3_VECTOR /*position*/ ) {}
	virtual void onClientPositionChanged( anyID /*clientID*/, TS3_VECTOR /*position*/ ) {}
	virtual void onClientRemoved( anyID /*clientID*/ ) {}
	virtual void enable() {}
	virtual void disable() {}

private:
	uint64 serverConnectionHandlerID;
};
