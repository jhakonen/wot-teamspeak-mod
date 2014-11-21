
@when("user starts TS")
def step_impl(context):
	context.ts_client.start()

@given("TS is running")
def step_impl(context):
	context.ts_client.start()

@when("user closes TS")
def step_impl(context):
	context.ts_client.stop()

@given("WOT is running and in garage")
def step_impl(context):
	context.game.start()
	context.game.login()

@given("mod is connected to TS")
def step_impl(context):
	context.ts_client.wait_for_a_command()

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
