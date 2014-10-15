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

#include "structures.h"
#include <QDataStream>
#include <iostream>

QDataStream& operator>>( QDataStream &stream, PositionalAudioData& data )
{
	anyID id;
	TS3_VECTOR position;
	quint8 clientCount;
	stream >> data.version
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


bool operator!=( const TS3_VECTOR &vector1, const TS3_VECTOR &vector2 )
{
	return vector1.x != vector2.x || vector1.y != vector2.y || vector1.z != vector2.z;
}


TS3_VECTOR operator-( const TS3_VECTOR &vector1, const TS3_VECTOR &vector2 )
{
	TS3_VECTOR subtracted = vector1;
	subtracted.x -= vector2.x;
	subtracted.y -= vector2.y;
	subtracted.z -= vector2.z;
	return subtracted;
}
