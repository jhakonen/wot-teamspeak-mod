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
#include "ts_helpers.h"

#include <public_errors.h>
#include <iostream>

static int lastDistance = 0;

PositionalAudio::PositionalAudio( const TS3Functions ts3Interface, QObject *parent )
	: ModuleBase( parent ), ts3Interface( ts3Interface ), isEnabled( false )
{
}

int PositionalAudio::providesAudioBackend() const
{
	return BuiltInBackend;
}

void PositionalAudio::enable()
{
	isEnabled = true;
}

void PositionalAudio::disable()
{
	isEnabled = false;
}

void PositionalAudio::onCustom3dRolloffCalculationClientEvent( uint64 serverConnectionHandlerID, anyID clientID, float distance, float *volume )
{
	Q_UNUSED( serverConnectionHandlerID );
	if( isEnabled )
	{
		*volume = 1.0;
		if ( lastDistance != (int)distance )
		{
			lastDistance = distance;
			std::cout << "distance: " << clientID << " :: " << distance << std::endl;
		}
	}
}

void PositionalAudio::onCustom3dRolloffCalculationWaveEvent( uint64 serverConnectionHandlerID, uint64 waveHandle, float distance, float *volume )
{
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( waveHandle );
	Q_UNUSED( distance );
	if( isEnabled )
	{
		*volume = 1.0;
	}
}

void PositionalAudio::onCameraPositionChanged( TS3_VECTOR position )
{
	origo = position;
	if( isEnabled )
	{
		std::cout << "onCameraPositionChanged(): " << position << std::endl;
		for ( auto iter = clientPositions.cbegin(); iter != clientPositions.cend(); ++iter )
		{
			TS3_VECTOR relativePosition = (*iter).second - origo;
			anyID clientID = (*iter).first;
			ts3Interface.channelset3DAttributes( getServerConnectionHandlerID(), clientID, &relativePosition );
		}
	}
}

void PositionalAudio::onCameraDirectionChanged( TS3_VECTOR direction )
{
	if( isEnabled )
	{
		std::cout << "onCameraDirectionChanged(): " << direction << std::endl;
		// cannot calculate up-vector if both x and z are zero
		if( direction.x == 0 && direction.z == 0 )
		{
			return;
		}

		TS3_VECTOR position = {0, 0, 0};
		TS3_VECTOR up = toUnitVector( crossProduct( direction, createVector( direction.z, 0, -direction.x ) ) );
		ts3Interface.systemset3DListenerAttributes( getServerConnectionHandlerID(), &position, &direction, &up );
	}
}

void PositionalAudio::onClientAdded( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		clientPositions[clientID] = position;
		if( isEnabled )
		{
			std::cout << "onClientAdded(): " << clientID << ", " << position << std::endl;
			TS3_VECTOR relativePosition = position - origo;
			ts3Interface.channelset3DAttributes( getServerConnectionHandlerID(), clientID, &relativePosition );
		}
	}
}

void PositionalAudio::onClientPositionChanged( anyID clientID, TS3_VECTOR position )
{
	if( isNotMyClientID( clientID ) )
	{
		clientPositions[clientID] = position;
		if( isEnabled )
		{
			TS3_VECTOR relativePosition = position - origo;
			std::cout << "onClientPositionChanged(): " << clientID << ", " << relativePosition << std::endl;
			ts3Interface.channelset3DAttributes( getServerConnectionHandlerID(), clientID, &relativePosition );
		}
	}
}

void PositionalAudio::onClientRemoved( anyID clientID )
{
	clientPositions.erase( clientID );
	if( isEnabled && isNotMyClientID( clientID ) )
	{
		std::cout << "onClientRemoved(): " << clientID << std::endl;
		TS3_VECTOR zero = {0, 0, 0};
		ts3Interface.channelset3DAttributes( getServerConnectionHandlerID(), clientID, &zero );
	}
}

bool PositionalAudio::isNotMyClientID( anyID clientID ) const
{
	anyID myID;
	if( ts3Interface.getClientID( getServerConnectionHandlerID(), &myID ) != ERROR_ok )
	{
		return false;
	}
	return myID != clientID;
}
