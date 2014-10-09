from behave import *
import time

@when("user starts TS")
def step_impl(context):
	time.sleep(1)
	context.ts_client.start()
	set_ts_client_not_connected_to_server_responses(context.ts_client)

@given("TS is running")
def step_impl(context):
	context.ts_client.start()
	set_ts_client_not_connected_to_server_responses(context.ts_client)

@when("user closes TS")
def step_impl(context):
	context.ts_client.stop()

@given("WOT is running and in garage")
def step_impl(context):
	context.game.start()
	context.game.login()

@when("user starts and logins to WOT")
def step_impl(context):
	time.sleep(1)
	context.game.start()
	context.game.login()

@then("\"{message}\" is shown in notification center")
def step_impl(context, message):
	assert context.game.notification_center_has_message(message)

@then("no errors occurred")
def step_impl(context):
	for log in context.game.get_logs():
		assert log[0] != "ERROR", "Error in log output: {0}".format(log)
		assert log[0] != "EXCEPTION", "Exception in log output: {0}".format(log)

def set_ts_client_not_connected_to_server_responses(ts_client):
	ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifytalkstatuschange")
	ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifycliententerview")
	ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifyclientupdated")
	ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifyclientuidfromclid")
	ts_client.set_cmd_response("whoami", error=(1794, "not connected"))
