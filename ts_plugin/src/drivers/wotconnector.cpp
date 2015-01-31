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

#include "wotconnector.h"
#include "../entities/vector.h"
#include <QTimer>
#include <QSharedMemory>
#include <QDateTime>
#include <iostream>
#include <QIODevice>

namespace {

const int TIME_LIMIT = 5;

class MyDataStream : public QDataStream
{
public:
	MyDataStream( QIODevice* device )
		: QDataStream( device )
	{
		setVersion( QDataStream::Qt_5_2 );
		setByteOrder( QDataStream::LittleEndian );
		setFloatingPointPrecision( QDataStream::SinglePrecision );
	}
};

class MemoryAreaBuffer : public QIODevice
{
public:
	MemoryAreaBuffer( QObject *parent = 0 )
	: QIODevice( parent ), memoryData( 0 ), memorySize( 0 )
	{
	}

	void setMemoryArea( void* data, int size )
	{
		memoryData = data;
		memorySize = size;
	}

	virtual bool open( OpenMode mode )
	{
		return QIODevice::open( mode | Unbuffered );
	}

protected:
	virtual qint64 readData( char* data, qint64 maxSize )
	{
		if ( isOpen() )
		{
			qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
			memcpy( data, (char*)memoryData + pos(), size );
			return size;
		}
		return -1;
	}

	virtual qint64 writeData( const char* data, qint64 maxSize )
	{
		if ( isOpen() )
		{
			qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
			memcpy( (char*)memoryData + pos(), data, size );
			return size;
		}
		return -1;
	}

private:
	void* memoryData;
	qint64 memorySize;
};

struct PositionalAudioData
{
	PositionalAudioData()
		: version( 0 ), timestamp( 0 )
	{
	}

	quint16 version;
	quint32 timestamp;
	Entity::Vector cameraPosition;
	Entity::Vector cameraDirection;
	QMap<quint16, Entity::Vector> clientPositions;
};

QDataStream& operator>>( QDataStream &stream, Entity::Vector& vector )
{
	float x, y, z;
	stream >> x >> y >> z;
	vector.x = x;
	vector.y = y;
	vector.z = z;
	return stream;
}

QDataStream& operator>>( QDataStream &stream, PositionalAudioData& data )
{
	quint16 id;
	Entity::Vector position;
	quint8 clientCount;
	stream >> data.version
		   >> data.timestamp
		   >> data.cameraPosition
		   >> data.cameraDirection
		   >> clientCount;
	for( int i = 0; i < clientCount; i++ )
	{
		stream >> id >> position;
		data.clientPositions[id] = position;
	}
	return stream;
}

}

namespace Driver
{

class WotConnectorPrivate
{
public:
	WotConnectorPrivate( WotConnector *q )
		: timer( new QTimer( q ) ), memory( new QSharedMemory( q ) )
	{
	}

	bool connectToSharedMemory()
	{
		if ( memory->create( 1024 ) == false )
		{
			if ( memory->error() == QSharedMemory::AlreadyExists )
			{
				return memory->attach();
			}
			return false;
		}
		return true;
	}

	QTimer* timer;
	QSharedMemory* memory;
	MemoryAreaBuffer* memoryBuffer;
	PositionalAudioData previousData;
};

WotConnector::WotConnector( QObject *parent )
	: QObject( parent ), d_ptr( new WotConnectorPrivate( this ) )
{
	Q_D( WotConnector );
	connect( d->timer, SIGNAL(timeout()), this, SLOT(onTimeout()) );
	d->timer->setInterval( 100 );
	d->timer->setSingleShot( false );
	d->memory->setNativeKey( "TessuModTSPlugin3dAudio" );
}

WotConnector::~WotConnector()
{
	Q_D( WotConnector );
	stop();
	delete d;
}

void WotConnector::initialize()
{
	start();
}

void WotConnector::start()
{
	Q_D( WotConnector );
	d->timer->start();
	if ( d->connectToSharedMemory() == false )
	{
		QString message = "Failed to connect to shared memory, reason: "
				+ d->memory->errorString();
		std::cout << message.toStdString() << std::endl;
		stop();
		return;
	}
	d->memoryBuffer = new MemoryAreaBuffer( this );
	d->memoryBuffer->setMemoryArea( d->memory->data(), d->memory->size() );
	if ( d->memoryBuffer->open( QIODevice::ReadWrite ) == false )
	{
		std::cout << "Failed to open buffer" << std::endl;
		return;
	}
	MyDataStream stream( d->memoryBuffer );
	stream << (quint16) 1; // version
}

void WotConnector::stop()
{
	Q_D( WotConnector );
	d->timer->stop();
}

QObject *WotConnector::qtObj()
{
	return this;
}

void WotConnector::onTimeout()
{
	Q_D( WotConnector );
	d->memoryBuffer->seek( 0 );
	MyDataStream stream( d->memoryBuffer );
	PositionalAudioData data;
	stream >> data;

	if( ( QDateTime::currentDateTime().toTime_t() - data.timestamp ) > TIME_LIMIT )
	{
		data.cameraPosition = Entity::Vector();
		data.cameraDirection = Entity::Vector();
		data.clientPositions.clear();
	}

	if( data.cameraPosition != d->previousData.cameraPosition )
	{
		emit gameCameraPositionChanged( data.cameraPosition );
	}
	if( data.cameraDirection != d->previousData.cameraDirection )
	{
		emit gameCameraDirectionChanged( data.cameraDirection );
	}
	foreach( quint16 id, data.clientPositions.keys() )
	{
		Entity::Vector pos = data.clientPositions[id];
		if ( d->previousData.clientPositions.contains( id ) )
		{
			if ( d->previousData.clientPositions[id] != pos )
			{
				emit gameUserPositionChanged( id, pos );
			}
		}
		else
		{
			emit gameUserAdded( id );
			emit gameUserPositionChanged( id, pos );
		}
	}
	foreach( quint16 id, d->previousData.clientPositions.keys() )
	{
		if ( !data.clientPositions.contains( id ) )
		{
			emit gameUserRemoved( id );
		}
	}

	d->previousData = data;
}

}
