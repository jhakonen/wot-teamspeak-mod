
def reset_fake():
	global g_battleWindow
	global g_appLoader
	g_battleWindow = BattleWindow()
	g_appLoader = AppLoader()

class AppLoader(object):

	def getDefBattleApp(self):
		return g_battleWindow

class BattleWindow(object):

	def __init__(self):
		self.minimap = Minimap()

class Minimap(object):
	pass

reset_fake()
