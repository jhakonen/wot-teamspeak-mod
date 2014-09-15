import sys, os

script_dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir_path, "fakes"))
sys.path.append(os.path.join(script_dir_path, "../src/mods"))

import BigWorld, game
import tessu_mod

BigWorld.loop()

game.fini()