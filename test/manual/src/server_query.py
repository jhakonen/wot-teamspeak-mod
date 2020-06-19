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
import ts3

SERVER_URL = 'telnet://serveradmin:password123@127.0.0.1:10011'

@contextmanager
def connect():
	with ts3.query.TS3ServerConnection(SERVER_URL) as conn:
		conn.exec_('use', sid=1)
		yield conn

def send_text_message(conn, msg):
	conn.exec_('sendtextmessage',
		targetmode=2,
		target=1,
		msg=msg
	)

def add_client_to_group(conn, client_name, group_name):
	client = find_client(conn, client_name)
	group = find_group(conn, group_name)
	try:
		conn.exec_('servergroupaddclient',
			sgid=group['sgid'],
			cldbid=client['client_database_id']
		)
	except ts3.query.TS3QueryError as error:
		if error.resp.error['id'] != '2561': # Duplicate entry
			raise

def find_client(conn, name):
	result = conn.exec_('clientfind', pattern=name)
	clid = result.parsed[0]['clid']
	result = conn.exec_('clientinfo', clid=clid)
	return dict(result.parsed[0], clid=clid)

def find_group(conn, name):
	result = conn.exec_('servergrouplist')
	for group in result.parsed:
		if group['name'] == name and group['type'] == '1':
			return group

def change_server_property(conn, prop, value):
	conn.exec_('serveredit', **{ prop.lower(): value })
