from helpers.ts_client_query import TSClientQueryService
from helpers.game_runner import GameRunner
import os

def before_scenario(context, scenario):
	context.ts_client = TSClientQueryService()
	context.game = GameRunner(
		mod_path=os.path.join(
			os.path.dirname(os.path.realpath(__file__)),
				"..", "src", "mods", "tessu_mod.py")
	)

def after_scenario(context, scenario):
	context.ts_client.stop()
	context.game.stop()
