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
#include "ts_helpers.h"

class QTimer;
class QSharedMemory;
class MemoryAreaBuffer;

class SharedMemoryListener : public QObject
{
	Q_OBJECT

public:
	SharedMemoryListener();
	virtual ~SharedMemoryListener();

	void start();
	void stop();

signals:
	void cameraPositionChanged( TS3_VECTOR position );
	void cameraDirectionChanged( TS3_VECTOR direction );
	void clientAdded( anyID clientID, TS3_VECTOR position );
	void clientPositionChanged( anyID clientID, TS3_VECTOR position );
	void clientRemoved( anyID clientID );

private slots:
	void onTimeout();

private:
	bool connectToSharedMemory();

private:
	QTimer* timer;
	QSharedMemory* memory;
	MemoryAreaBuffer* memoryBuffer;
	PositionalAudioData previousData;
};
