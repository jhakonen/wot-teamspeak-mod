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
#include <QPointer>

#include "openal.h"

class OALDevice;
class OALContext;
class OALSource;

class OALLibrary : public QObject
{
	Q_OBJECT

public:
	OALLibrary( QObject *parent = 0 );
	~OALLibrary();

	OALDevice *createDevice( const QString &name );

private:
	QList<QPointer<OALDevice>> devices;
};

class OALDevice : public QObject
{
	Q_OBJECT
	friend class OALLibrary;

public:
	~OALDevice();
	OALContext *createContext( ALCint frequency, bool hrtfEnabled );

	operator ALCdevice*() const;

private:
	OALDevice( const QString &name, OALLibrary *parent );

	ALCdevice *device;
	QList<QPointer<OALContext>> contexts;
};

class OALContext : public QObject
{
	Q_OBJECT
	friend class OALDevice;

public:
	~OALContext();
	OALSource *createSource();

	ALuint getFrequency() const;

	void setListenerOrientation( ALfloat forwardX, ALfloat forwardY, ALfloat forwardZ, ALfloat upX, ALfloat upY, ALfloat upZ );
	void setListenerGain( ALfloat gain );
	void setListenerVelocity( ALfloat x, ALfloat y, ALfloat z );
	void setListenerPosition( ALfloat x, ALfloat y, ALfloat z );

	operator ALCcontext*() const;

private:
	OALContext( OALDevice *parent );
	OALContext( ALCint frequency, bool hrtfEnabled, OALDevice *parent );

	OALDevice *device;
	ALCcontext *context;
	QList<QPointer<OALSource>> sources;
};

class OALSource : public QObject
{
	Q_OBJECT
	friend class OALContext;

public:
	~OALSource();

	void setRolloffFactor( ALfloat factor );
	void setPosition( ALfloat x, ALfloat y, ALfloat z );
	void setRelative( bool relative );
	void setLooping( bool looping );

	bool isPlaying() const;

	void playbackAudioData(ALenum format, const ALvoid *data, ALsizei size, ALsizei frequency );
	void queueAudioData( ALenum format, const ALvoid *data, ALsizei size, ALsizei frequency );

	void play();
	void stop();

protected:
	void timerEvent( QTimerEvent *event );

private:
	OALSource( OALContext *parent );
	void cleanupProcessedBuffers();

	ALuint source;
	OALContext *context;
	ALuint playbackBuffer;
};
