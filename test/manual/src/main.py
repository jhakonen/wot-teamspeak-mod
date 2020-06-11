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

import sys

import click

import docker_compose
import server_query

@click.group()
def cli():
	pass

@cli.command()
def up():
	try:
		docker_compose.up()
		print('')
		print('ServerAdmin privilege key:',
			docker_compose.search_logs(r'token=(\S+)')[1]
		)
	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@cli.command()
def down():
	try:
		docker_compose.down()
	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@cli.command()
def build():
	try:
		docker_compose.build()
	except FileNotFoundError as error:
		print(error)
		sys.exit(1)

@cli.command()
def play():
	server_query.send_text_message(
		'!play /testaudio/Bennett__Bravo__Mehrl__Olivera__Taveira__Italiano_-_16_-_chalchihuitl.mp3'
	)

@cli.command()
def stop():
	server_query.send_text_message('!stop')

if __name__ == '__main__':
	cli()
