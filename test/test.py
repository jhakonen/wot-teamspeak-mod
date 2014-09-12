import sys
sys.path.append("fakes")
sys.path.append("../src/mods")
import BigWorld, game
import tessu_mod

BigWorld.loop()

game.fini()