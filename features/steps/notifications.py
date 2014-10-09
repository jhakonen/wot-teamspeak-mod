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

@then("\"{message}\" is shown in notification center")
def step_impl(context, message):
	assert context.game.notification_center_has_message(message)

@then("no errors occurred")
def step_impl(context):
	for log in context.game.get_logs():
		assert log[0] != "ERROR", "Error in log output: {0}".format(log)
		assert log[0] != "EXCEPTION", "Exception in log output: {0}".format(log)
