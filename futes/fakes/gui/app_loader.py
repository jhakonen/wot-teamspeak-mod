
class AppLoader(object):

	def getDefBattleApp(self):
		return g_battleWindow

class BattleWindow(object):

	def __init__(self):
		self.minimap = Minimap()

class Minimap(object):

	def showActionMarker(self, vehicle_id, action):
		pass

g_battleWindow = BattleWindow()

g_appLoader = AppLoader()
