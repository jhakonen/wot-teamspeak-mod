# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2020  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from contextlib import contextmanager
import logging
import sys
import time

import click
from tenacity import retry, wait_fixed

import docker_compose
import server_query

MUSIC_BOT_NAME = 'TS3AudioBot'

# Enable to debug server_query
# logging.basicConfig(level=logging.DEBUG)

@click.group(help='''
	Creates manual test environment which includes TeamSpeak server, database
	for it, and a music bot. The bot will automatically connect to the server
	on environment start up. This tool provides also basic commands for
	controlling the bot.
	''')
def main():
	pass

@main.command(help='Starts manual test environment')
def env_up():
	try:
		docker_compose.up()
		print('')
		print('TeamSpeak server is listening at \'localhost\', use your TeamSpeak client to connect to the server.')
		print('ServerAdmin privilege key for gaining admin rights:')
		print(' ', docker_compose.search_logs(r'token=(\S+)')[1])
		music_bot_info = get_music_bot_info()
		print('Music bot:')
		print('  Name:      ', music_bot_info['client_nickname'])
		print('  Client ID: ', music_bot_info['clid'])
		print('  Unique ID: ', music_bot_info['client_unique_identifier'])
		print('  Channel ID:', music_bot_info['cid'])

		with server_query.connect() as conn:
			server_query.change_server_property(conn,
				'VIRTUALSERVER_NAME',
				'Tessumod manual test server'
			)
			server_query.add_client_to_group(conn, MUSIC_BOT_NAME, 'Server Admin')
			server_query.send_text_message(conn, '!repeat all')

	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@retry(wait=wait_fixed(1))
def get_music_bot_info():
	with server_query.connect() as conn:
		return server_query.find_client(conn, MUSIC_BOT_NAME)

@main.command(help='Shows log output from TS server, DB and music bot')
def env_logs():
	docker_compose.logs()

@main.command(help='Brings down the manual test environment and destroys it, '
	+ 'removing all settings')
def env_down():
	try:
		docker_compose.down()
	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@main.command(help='Brings down the manual test environment')
def env_stop():
	try:
		docker_compose.stop()
	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@main.command(help='Starts playback of audio stream')
@click.argument('url')
def play(url):
	with server_query.connect() as conn:
		server_query.send_text_message(conn, f'!play {url}')

@main.command(help='Pause or unpause current playback')
def pause():
	with server_query.connect() as conn:
		server_query.send_text_message(conn, '!pause')

if __name__ == '__main__':
	main()
