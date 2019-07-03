import BigWorld
import debug_utils
import helpers.dependency
import gui.app_loader
import gui.SystemMessages
import messenger.proto.events
import messenger.storage
import notification.NotificationMVC
import PlayerEvents
import VOIP.VOIPManager

def reset():
	BigWorld.reset_fake()
	debug_utils.reset_fake()
	helpers.dependency.reset_fake()
	gui.app_loader.reset_fake()
	gui.SystemMessages.reset_fake()
	messenger.proto.events.reset_fake()
	messenger.storage.reset_fake()
	notification.NotificationMVC.reset_fake()
	PlayerEvents.reset_fake()
	VOIP.VOIPManager.reset_fake()
