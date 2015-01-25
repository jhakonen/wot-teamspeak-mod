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

#include "ts_helpers.h"
#include <QDataStream>
#include <iostream>
#include <cmath>

PositionalAudioData::PositionalAudioData()
	: version( 0 ), timestamp( 0 ),
	  cameraPosition( createVector( 0, 0, 0 ) ),
	  cameraDirection( createVector( 0, 0, 0 ) )
{
}

QDataStream& operator>>( QDataStream &stream, PositionalAudioData& data )
{
	anyID id;
	TS3_VECTOR position;
	quint8 clientCount;
	stream >> data.version
		   >> data.timestamp
		   >> data.cameraPosition
		   >> data.cameraDirection
		   >> clientCount;
	for ( int i = 0; i < clientCount; i++ )
	{
		stream >> id >> position;
		data.clientPositions[id] = position;
	}
	return stream;
}

QDataStream& operator>>( QDataStream &stream, TS3_VECTOR& vector )
{
	stream >> vector.x >> vector.y >> vector.z;
	return stream;
}

std::ostream& operator<<( std::ostream& stream, const PositionalAudioData& data )
{
	stream << "camera(pos: " << data.cameraPosition << ", "
		   << "dir: " << data.cameraDirection << "), "
		   << "clients: (";
	for ( auto iter = data.clientPositions.cbegin(); iter != data.clientPositions.cend(); ++iter )
	{
		stream << "(id: " << (*iter).first << ", pos: " << (*iter).second << "), ";
	}
	stream << ")";
	return stream;
}

std::ostream& operator<<( std::ostream& stream, const TS3_VECTOR& vector )
{
	stream << "(" << vector.x << ", " << vector.y << ", " << vector.z << ")";
	return stream;
}

TS3_VECTOR createVector( float x, float y, float z )
{
	TS3_VECTOR result;
	result.x = x;
	result.y = y;
	result.z = z;
	return result;
}

bool operator!=( const TS3_VECTOR &vector1, const TS3_VECTOR &vector2 )
{
	return vector1.x != vector2.x || vector1.y != vector2.y || vector1.z != vector2.z;
}


TS3_VECTOR operator-( const TS3_VECTOR &vector1, const TS3_VECTOR &vector2 )
{
	return createVector( vector1.x - vector2.x, vector1.y - vector2.y, vector1.z - vector2.z );
}

TS3_VECTOR operator/( const TS3_VECTOR &vector, float divider )
{
	return createVector( vector.x / divider, vector.y / divider, vector.z / divider );
}


TS3_VECTOR toUnitVector( const TS3_VECTOR &vector )
{
	return vector / getLength( vector );
}


float getLength( const TS3_VECTOR &vector )
{
	return sqrt( pow( vector.x, 2 ) + pow( vector.y, 2 ) + pow( vector.z, 2 ) );
}


TS3_VECTOR crossProduct( const TS3_VECTOR &a, const TS3_VECTOR &b )
{
	return createVector(
		a.y * b.z - a.z * b.y,
		a.z * b.x - a.x * b.z,
		a.x * b.y - a.y * b.x
	);
}

