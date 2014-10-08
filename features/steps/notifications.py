from behave import *

@given("TS is running")
def step_impl(context):
	context.ts_client.start()
	context.ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifytalkstatuschange")
	context.ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifycliententerview")
	context.ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifyclientupdated")
	context.ts_client.set_cmd_response(
		"clientnotifyregister schandlerid=0 event=notifyclientuidfromclid")
	context.ts_client.set_cmd_response("whoami", error=(1794, "not connected"))

@when("user starts and logins to WOT")
def step_impl(context):
	context.game.start()
	context.game.login()

@then("\"Connected to TeamSpeak client\" is shown in notification center")
def step_impl(context):
	context.game.notification_center_has_message("Connected to TeamSpeak client")
