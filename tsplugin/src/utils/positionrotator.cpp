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

#include "positionrotator.h"
#include "../entities/vector.h"
#include "../entities/enums.h"

#include <QTimer>
#include <cmath>

namespace
{
const int TEST_UPDATE_INTERVAL = 100; // ms
const int TEST_DURATION        = 10000; // ms
const qreal PI                 = 3.14159265358979323846;
const qreal TEST_DISTANCE      = 10; // meters
const int START_ANGLE          = -90;
}

PositionRotator::PositionRotator( QObject *parent )
	: QObject( parent ), timer( new QTimer( this ) )
{
	connect( timer, SIGNAL(timeout()), this, SLOT(onTimeout()) );
	timer->setInterval( TEST_UPDATE_INTERVAL );
	timer->setSingleShot( false );
}

void PositionRotator::start( Entity::RotateMode mode )
{
	if( timer->isActive() )
	{
		return;
	}
	rotateMode = mode;
	angle = START_ANGLE;
	timer->start();
	emit started();
	emit positionChanged( getPosition() );
}

void PositionRotator::stop()
{
	timer->stop();
	emit finished();
}

void PositionRotator::onTimeout()
{
	if( angle >= 360 + START_ANGLE )
	{
		timer->stop();
		emit finished();
	}
	else
	{
		angle += 360.0 / (qreal)TEST_DURATION * (qreal)timer->interval();
		emit positionChanged( getPosition() );
	}
}

Entity::Vector PositionRotator::getPosition() const
{
	qreal radAngle = angle * PI / 180.0;
	switch( rotateMode )
	{
	case Entity::RotateXAxis:
		return Entity::Vector(
			0,
			TEST_DISTANCE * sin( radAngle ),
			TEST_DISTANCE * cos( radAngle )
		);

	case Entity::RotateYAxis:
		return Entity::Vector(
			TEST_DISTANCE * cos( radAngle ),
			0,
			TEST_DISTANCE * sin( radAngle )
		);

	case Entity::RotateZAxis:
		return Entity::Vector(
			TEST_DISTANCE * cos( radAngle ),
			TEST_DISTANCE * sin( radAngle ),
			0
		);
	}
	return Entity::Vector();
}
