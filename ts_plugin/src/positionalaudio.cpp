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

#include "positionalaudio.h"
#include "structures.h"

#include <public_errors.h>
#include <iostream>

PositionalAudio::PositionalAudio( const TS3Functions ts3Interface, QObject *parent )
	: QObject( parent ), ts3Interface( ts3Interface )
{
}

void PositionalAudio::setServerConnectionHandlerID( uint64 id )
{
	serverConnectionHandlerID = id;
}

void PositionalAudio::onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float *volume )
{
	Q_UNUSED( serverConnectionHandlerID );
	*volume = 1.0;
	std::cout << "distance: " << clientID << " :: " << distance << std::endl;
}

void PositionalAudio::onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float *volume )
{
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( waveHandle );
	Q_UNUSED( distance );
	*volume = 1.0;
}

void PositionalAudio::onCameraPositionChanged( TS3_VECTOR position )
{
	std::cout << "onCameraPositionChanged(): " << position << std::endl;
	origo = position;
	for ( auto iter = clientPositions.cbegin(); iter != clientPositions.cend(); ++iter )
	{
		TS3_VECTOR relativePosition = (*iter).second - origo;
		anyID clientID = (*iter).first;
		ts3Interface.channelset3DAttributes( serverConnectionHandlerID, clientID, &relativePosition );
	}
}

void PositionalAudio::onCameraDirectionChanged( TS3_VECTOR direction )
{
	std::cout << "onCameraDirectionChanged(): " << direction << std::endl;
	TS3_VECTOR position = {0, 0, 0};
	TS3_VECTOR up = {0, 1, 0};
	ts3Interface.systemset3DListenerAttributes( serverConnectionHandlerID, &position, &direction, &up );
}

void PositionalAudio::onClientAdded( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		TS3_VECTOR relativePosition = position - origo;
		std::cout << "onClientAdded(): " << clientID << ", " << position << std::endl;
		clientPositions[clientID] = position;
		ts3Interface.channelset3DAttributes( serverConnectionHandlerID, clientID, &relativePosition );
	}
}

void PositionalAudio::onClientPositionChanged( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		TS3_VECTOR relativePosition = position - origo;
		clientPositions[clientID] = position;
		std::cout << "onClientPositionChanged(): " << clientID << ", " << relativePosition << std::endl;
		ts3Interface.channelset3DAttributes( serverConnectionHandlerID, clientID, &relativePosition );
	}
}

void PositionalAudio::onClientRemoved( anyID clientID )
{
	std::cout << "onClientRemoved(): " << clientID << std::endl;
	clientPositions.erase( clientID );
	if( isNotMyClientID( clientID ) )
	{
		TS3_VECTOR zero = {0, 0, 0};
		ts3Interface.channelset3DAttributes( serverConnectionHandlerID, clientID, &zero );
	}
}

bool PositionalAudio::isNotMyClientID( anyID clientID ) const
{
	anyID myID;
	if( ts3Interface.getClientID( serverConnectionHandlerID, &myID ) != ERROR_ok )
	{
		return false;
	}
	return myID != clientID;
}
