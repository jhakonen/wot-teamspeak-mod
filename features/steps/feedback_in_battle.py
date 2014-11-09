
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

@given("TS user \"{ts_name}\" player name is \"{player_name}\" and has TessuMod installed")
def step_impl(context, player_name, ts_name):
	context.ts_client.add_user(ts_name, metadata="<wot_nickname_start>{0}<wot_nickname_end>".format(player_name))

@given("TS user \"{ts_name}\" is in my channel")
def step_impl(context, ts_name):
	context.ts_client.add_user(ts_name)

@given("TS user \"{ts_name}\" is speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, True)

@given("nick extract pattern \"{pattern}\" is set")
def step_impl(context, pattern):
	context.set_ini_variable("General", "nick_extract_patterns", pattern)

@given("name mapping with TS name \"{ts_name}\" to player name \"{player_name}\" is set")
def step_impl(context, ts_name, player_name):
	context.set_ini_variable("NameMappings", ts_name, player_name)

@when("TS user \"{ts_name}\" starts speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, True)
	context.ts_client.wait_for_data_in_response("notifytalkstatuschange")

@when("TS user \"{ts_name}\" stops speaking")
def step_impl(context, ts_name):
	assert context.game.wait_for_log("Connected to TeamSpeak server", once=False)
	context.ts_client.set_user_speaking(ts_name, False)
	context.ts_client.wait_for_data_in_response("notifytalkstatuschange")

@then("I see speak feedback start for player \"{player_name}\"")
def step_impl(context, player_name):
	assert context.game.is_player_speaking(player_name)

@then("I see speak feedback end for player \"{player_name}\"")
def step_impl(context, player_name):
	assert context.game.is_player_not_speaking(player_name)
