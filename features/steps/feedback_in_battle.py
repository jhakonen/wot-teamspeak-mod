
@given("WOT is running and in battle")
def step_impl(context):
	context.game.start()
	context.game.enter_battle()

@given("TS is connected to server")
def step_impl(context):
	context.ts_client.set_connected_to_server(True)

@given("player \"{player_name}\" is in battle")
def step_impl(context, player_name):
	context.game.add_player(player_name)

@given("player \"{player_name}\" TS name is \"{ts_name}\" and has TessuMod installed")
def step_impl(context, player_name, ts_name):
	context.ts_client.add_user(ts_name, metadata="client_meta_data=<wot_nickname_start>{0}<wot_nickname_end>".format(player_name))

@given("user \"{ts_name}\" is in TS")
def step_impl(context, ts_name):
	context.ts_client.add_user(ts_name)

@given("TS user \"{ts_name}\" is speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, True)
	assert context.game.wait_for_log("TEST_SUITE: setPlayerTalking() called")

@when("TS user \"{ts_name}\" starts speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, True)
	assert context.game.wait_for_log("TEST_SUITE: setPlayerTalking() called")

@when("TS user \"{ts_name}\" stops speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, False)
	assert context.game.wait_for_log("TEST_SUITE: setPlayerTalking() called")

@then("I see speak feedback start for player \"{player_name}\"")
def step_impl(context, player_name):
	assert context.game.is_player_speaking(player_name)

@then("I see speak feedback end for player \"{player_name}\"")
def step_impl(context, player_name):
	assert context.game.is_player_not_speaking(player_name)
