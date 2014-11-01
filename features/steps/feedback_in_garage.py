import re

@given("player \"{player_name}\" is logged in")
def step_impl(context, player_name):
	context.game.add_player(player_name)

@when("TS user \"{ts_name}\" player name changes to \"{player_name}\"")
def step_impl(context, ts_name, player_name):
	user = context.ts_client.get_user(ts_name)
	old_wot_name = re.search("<wot_nickname_start>(.+)<wot_nickname_end>", user.metadata).group(1)
	context.ts_client.wait_for_data_in_response(old_wot_name)
	user.metadata = "<wot_nickname_start>{0}<wot_nickname_end>".format(player_name)
