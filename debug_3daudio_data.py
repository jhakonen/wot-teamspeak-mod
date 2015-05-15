'''
This script provides human readable print out of the 3D audio positioning data
that TessuMod passes over to its TS plugin.
'''

import mmap
import struct
import datetime
import os
import time

def pretty_float(value):
	return "{0:.1f}".format(value)

def pretty_timestamp(value):
	return datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")

try:
	shmem = mmap.mmap(0, 1024, "TessuModTSPlugin3dAudio", mmap.ACCESS_READ)
	while True:
		os.system("cls")

		shmem.seek(0)
		version, timestamp, camera_pos_x, camera_pos_y, camera_pos_z, camera_dir_x, camera_dir_y, camera_dir_z, client_count = struct.unpack("=HI3f3fB", shmem.read(2+4+3*4+3*4+1))
		print "         VERSION:", version
		print "            TIME:", pretty_timestamp(timestamp)
		print " CAMERA POSITION:", (pretty_float(camera_pos_x), pretty_float(camera_pos_y), pretty_float(camera_pos_z))
		print "CAMERA DIRECTION:", (pretty_float(camera_dir_x), pretty_float(camera_dir_y), pretty_float(camera_dir_z))
		print "    CLIENT COUNT:", client_count

		for client_index in range(0, client_count):
			client_id, x, y, z = struct.unpack("=h3f", shmem.read(2+3*4))
			print "CLIENT[ {0} ] :: ID: {1}, POSITION: {2}".format(
				client_index,
				client_id,
				(pretty_float(x), pretty_float(y), pretty_float(z))
			)

		time.sleep(0.1)

finally:
	if shmem:
		shmem.close()
