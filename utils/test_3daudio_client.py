import mmap
import struct
import time
import random
import math

def create_position_at_angle_horizontally(distance, angle):
	'''Rotates client position around listener horizontally.'''
	rad_angle = math.radians(angle)
	pos = (distance * math.cos(rad_angle), 0, distance * math.sin(rad_angle))
	return pos

def create_position_at_angle_vertically(distance, angle):
	'''Rotates client position around listener vertically.'''
	rad_angle = math.radians(angle)
	pos = (0, distance * math.sin(rad_angle), distance * math.cos(rad_angle))
	return pos


def create_random_position(multiplier):
	return (random.uniform(0, multiplier), random.uniform(0, multiplier), random.uniform(0, multiplier))

def pack_float_vector(vector):
	return struct.pack("3f", float(vector[0]), float(vector[1]), float(vector[2]))

shmem = None

try:
	shmem = mmap.mmap(0, 1024, "TessuModTSPlugin3dAudio", mmap.ACCESS_WRITE)
	angle = 0

	while True:
		shmem.seek(0)

		data = []
		#data.append(pack_float_vector(create_random_position(1000)))
		#data.append(pack_float_vector(create_random_position(1000)))
		data.append(struct.pack("I", int(time.time())))
		data.append(pack_float_vector((0, 0, 0)))
		data.append(pack_float_vector((0, 0, 1)))
		data.append(struct.pack("B", 10))
		for id in range(0, 10):
			data.append(struct.pack("H", id))
			data.append(pack_float_vector(create_position_at_angle_horizontally(100, angle)))
			#data.append(pack_float_vector((0, 0, 0)))
			#data.append(pack_float_vector(create_random_position(1000)))
		data = "".join(data)
		shmem.write(data)
		time.sleep(0.1)
		angle += 2

finally:
	if shmem:
		shmem.close()
