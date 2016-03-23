from collections import namedtuple

class EntitiesFactories(object):

	def addSettings(self, *args, **kwargs):
		pass

g_entitiesFactories = EntitiesFactories()

ViewSettings = namedtuple('ViewSettings', ('alias', 'clazz', 'url', 'type', 'event', 'scope', 'cacheable'))
ViewSettings.__new__.__defaults__ = (None,
 None,
 None,
 None,
 None,
 None,
 False)
