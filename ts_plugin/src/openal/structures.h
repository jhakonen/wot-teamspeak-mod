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

#pragma once
#include "../entities/vector.h"
#include <QString>

namespace OpenAL {

/**
 * The OutputInfo class contains information of output device.
 *
 * The information within identifies OpenAL output device and context and any
 * parameters required at creation time of those.
 *
 * The OutputInfo object is immutable after construction and only provides
 * getters.
 */
class OutputInfo
{
public:
	/**
	 * Default constructor.
	 * Builds an invalid OutputDevice object.
	 */
	OutputInfo();

	/**
	 * Parametrized constructor.
	 * Builds a valid OutputDevice object.
	 *
	 * @param deviceName  name of device (as provided by TeamSpeak)
	 * @param sampleRate  context's output sampling rate (e.g. 44100)
	 * @param hrtfEnabled true if HRTF should be enabled, false if not
	 */
	OutputInfo( const QString &deviceName, quint32 sampleRate, bool hrtfEnabled );

	/**
	 * Returns true if object is valid or false if invalid.
	 */
	bool isValid() const;

	/**
	 * Returns device name.
	 */
	const QString& getDeviceName() const;

	/**
	 * Returns output sampling rate
	 */
	quint32 getSampleRate() const;

	/**
	 * Returns true if HRTF is enabled, false if not.
	 */
	bool isHrtfEnabled() const;

	/**
	 * Returns true if contents of self are considered lesser than contents
	 * of @a other.
	 *
	 * Required for compatibility as a key in QMap.
	 *
	 * @param other OutputInfo object
	 * @return true if lesser than
	 */
	bool operator<( const OutputInfo &other ) const;

	/**
	 * Returns true if contents of self are same as contents of @a other.
	 *
	 * @param other OutputInfo object
	 * @return true if object contents are same
	 */
	bool operator==( const OutputInfo &other ) const;

	/**
	 * Returns true if contents of self are not same as contents of @a other.
	 *
	 * @param other OutputInfo object
	 * @return true if object contents are not same
	 */
	bool operator!=( const OutputInfo &other ) const;

private:
	bool valid;
	QString deviceName;
	quint32 sampleRate;
	bool hrtfEnabled;
};

/**
 * The SourceInfo class identifies and contains information of audio source.
 *
 * The information within identifies OpenAL audio source and any parameters
 * which are applied to the said source.
 *
 * ID-parameter is what indentifies the audio source. The ID-value is tied to
 * the underlying OpenAL source object and any other parameters in SourceInfo
 * are applied to that source object. Any changed parameters in SourceInfo are
 * applied to a existing source object if one exists.
 *
 * In case the source doesn't exist then a new source object is created and
 * tied to the provided SourceInfo ID-value. The source object will exist as
 * long as the library is not reset().
 *
 * The SourceInfo object is immutable after construction and only provides
 * getters.
 */
class SourceInfo
{
public:
	/**
	 * Default constructor.
	 * Builds an invalid SourceInfo object.
	 */
	SourceInfo();

	/**
	 * Parametrized constructor.
	 * Builds a valid SourceInfo object.
	 *
	 * @param outputInfo    output device and context where the source lies
	 * @param id            ID which ties source and the info together
	 * @param position      position of the source in 3D world
	 * @param rolloffFactor factor for adjusting effect of distance to sound volume
	 * @param relative      true if the source is relative to listener
	 * @param streaming     true if audio data is streamed to source
	 */
	SourceInfo( const OutputInfo &outputInfo, quint32 id, const Entity::Vector &position, qreal rolloffFactor, bool relative, bool streaming );

	/**
	 * Returns true if object is valid or false if invalid.
	 */
	bool isValid() const;

	/**
	 * Returns output info which identifies used OpenAL context and device.
	 */
	const OutputInfo& getOutputInfo() const;

	/**
	 * Returns ID value which ties SourceInfo to underlying OpenAL source.
	 */
	quint32 getId() const;

	/**
	 * Returns position of the audio source in 3D world.
	 * The position should be provided in right handed coordinate system.
	 */
	const Entity::Vector& getPosition() const;

	/**
	 * Returns fctor for adjusting effect of distance to sound volume.
	 */
	qreal getRolloffFactor() const;

	/**
	 * Returns true if the source's position is a relative position based on
	 * listener.
	 *
	 * False is returned if source is absolutely positioned in the 3D system.
	 */
	bool isRelative() const;

	/**
	 * Returns true if OpenAL should stream any audio data provided via
	 * playAudio() to the source.
	 *
	 * If not, then playAudio() starts playback of the provided audio data from
	 * start and loops the data until stopAudio() is called.
	 */
	bool isStreaming() const;

private:
	bool valid;
	OutputInfo outputInfo;
	quint32 id;
	Entity::Vector position;
	qreal rolloffFactor;
	bool relative;
	bool streaming;
};

/**
 * The ListenerInfo contains information of audio listener.
 *
 * The information within provides parameters which affects the listener
 * within OpenAL.
 *
 * The ListenerInfo object is immutable after construction and only provides
 * getters.
 */
class ListenerInfo
{
public:
	/**
	 * Default constructor.
	 * Builds an invalid ListenerInfo object.
	 */
	ListenerInfo();

	/**
	 * Parametrized constructor.
	 * Builds a valid ListenerInfo object.
	 *
	 * @param outputInfo output device and context where the listener lies
	 * @param forward  listener's looking direction (unit vector)
	 * @param up       direction perpendicularly up-wards from looking direction (unit vector)
	 * @param velocity speed of the listener
	 * @param position position of the listener in 3D world
	 * @param gain     volume multiplier
	 */
	ListenerInfo( const OutputInfo &outputInfo, const Entity::Vector &forward, const Entity::Vector &up, const Entity::Vector &velocity, const Entity::Vector &position, qreal gain );

	/**
	 * Returns true if object is valid or false if invalid.
	 */
	bool isValid() const;

	/**
	 * Returns output info which identifies used OpenAL context and device.
	 */
	const OutputInfo& getOutputInfo() const;

	/**
	 * Returns unit vector which indicates listener's looking direction.
	 */
	const Entity::Vector& getForward() const;

	/**
	 * Returns unit vector which is perpendicularly up-wards from looking
	 * direction.
	 */
	const Entity::Vector& getUp() const;

	/**
	 * Returns speed of the listener.
	 */
	const Entity::Vector& getVelocity() const;

	/**
	 * Returns position of the listener in 3D world.
	 * The position should be provided in right handed coordinate system.
	 */
	const Entity::Vector& getPosition() const;

	/**
	 * Returns volume multiplier value.
	 */
	qreal getGain() const;

private:
	bool valid;
	OutputInfo outputInfo;
	Entity::Vector forward;
	Entity::Vector up;
	Entity::Vector velocity;
	Entity::Vector position;
	qreal gain;
};

/**
 * The AudioData class container holds audio data.
 */
class AudioData
{
public:
	/**
	 * Parametrized constructor.
	 * Builds a valid ListenerInfo object.
	 *
	 * @param channelCount number of channels (1 = mono, 2 = stereo, etc...)
	 * @param sampleSize   size of sample in bits (8 or 16)
	 * @param dataSize     size of the audio data in bytes
	 * @param sampleRate   sampling rate of the data (e.g. 44100)
	 * @param data         pointer to the audio data
	 */
	AudioData( quint8 channelCount, quint8 sampleSize, quint32 dataSize, quint32 sampleRate, const void *data );

	/**
	 * Returns count of channels in the audio data.
	 */
	quint8 getChannelCount() const;

	/**
	 * Returns size of one sample in bits.
	 */
	quint8 getSampleSize() const;

	/**
	 * Returns size of the audio data in bytes.
	 */
	quint32 getDataSize() const;

	/**
	 * Returns sampling rate of the audio data in Hz.
	 */
	quint32 getSampleRate() const;

	/**
	 * Returns pointer to the audio data.
	 */
	const void *getData() const;

private:
	quint8 channelCount;
	quint8 sampleSize;
	quint32 dataSize;
	quint32 sampleRate;
	const void *data;
};

/**
 * The Failure exception class is thrown from OpenAL calls to indicate an error.
 */
class Failure
{
public:
	/**
	 * Class constructor.
	 *
	 * @param error error string
	 */
	Failure( const QString &error )
		: error( error )
	{
	}

	/**
	 * Returns error string which describes what went wrong.
	 */
	QString what() const
	{
		return error;
	}

private:
	QString error;
};

}
