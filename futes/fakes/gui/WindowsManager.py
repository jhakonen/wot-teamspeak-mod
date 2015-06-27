
class WindowsManager(object):

	def __init__(self):
		self.battleWindow = BattleWindow()

class BattleWindow(object):

	def __init__(self):
		self.minimap = Minimap()

class Minimap(object):
	pass

g_windowsManager = WindowsManager()
