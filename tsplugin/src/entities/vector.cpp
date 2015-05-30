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

#include "vector.h"
#include <cmath>
#include <ostream>

namespace Entity
{

Vector::Vector( qreal x, qreal y, qreal z )
	: x( x ), y( y ), z( z )
{
}

Vector Vector::getUnit() const
{
	return *this / getLength();
}

qreal Vector::getLength() const
{
	return sqrt( pow( x, 2 ) + pow( y, 2 ) + pow( z, 2 ) );
}

Vector Vector::crossProduct( const Vector &other ) const
{
	return Vector(
		y * other.z - z * other.y,
		z * other.x - x * other.z,
		x * other.y - y * other.x
	);
}

Vector Vector::operator/( qreal divider ) const
{
	return Vector( x / divider, y / divider, z / divider );
}

Vector Vector::operator-( const Vector &other ) const
{
	return Vector( x - other.x, y - other.y, z - other.z );
}

bool Vector::operator==( const Vector &other ) const
{
	return x == other.x && y == other.y && z == other.z;
}

bool Vector::operator!=( const Vector &other ) const
{
	return !operator==( other );
}

std::ostream& operator<<( std::ostream& stream, const Vector& vector )
{
	stream << "(" << vector.x << ", " << vector.y << ", " << vector.z << ")";
	return stream;
}

}
