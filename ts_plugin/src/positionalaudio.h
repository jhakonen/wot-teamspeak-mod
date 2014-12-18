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

class PositionalAudio : public ModuleBase
{
	Q_OBJECT

public:
	PositionalAudio( const TS3Functions ts3Interface, QObject *parent = 0 );

	int getAudioBackend() const;
	void enable();
	void disable();

	void onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float* volume );
	void onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float* volume );

public slots:
	void onCameraPositionChanged( TS3_VECTOR position );
	void onCameraDirectionChanged( TS3_VECTOR direction );
	void onClientAdded( anyID clientID, TS3_VECTOR position );
	void onClientPositionChanged( anyID clientID, TS3_VECTOR position );
	void onClientRemoved( anyID clientID );

private:
	bool isNotMyClientID( anyID clientID ) const;

private:
	const TS3Functions ts3Interface;
	TS3_VECTOR origo;
	std::map<anyID, TS3_VECTOR> clientPositions;
	bool isEnabled;
};
