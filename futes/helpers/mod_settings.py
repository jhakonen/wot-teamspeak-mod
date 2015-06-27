import ConfigParser
import os

def get_ini_dirpath():
	return os.path.join(os.getcwd(), "res_mods", "configs", "tessu_mod")

def remove_file(path):
	if os.path.exists(path):
		os.remove(path)

def remove_cache_file():
	remove_file(os.path.join(get_ini_dirpath(), "tessu_mod_cache.ini"))

def reset_settings_file():
	if not os.path.exists(get_ini_dirpath()):
		os.makedirs(get_ini_dirpath())
	path = os.path.join(get_ini_dirpath(), "tessu_mod.ini")
	remove_file(path)
	parser = ConfigParser.SafeConfigParser()
	parser.add_section("General")
	parser.set("General", "log_level", "1")
	parser.set("General", "ini_check_interval", "5")
	parser.set("General", "speak_stop_delay", "1")
	parser.set("General", "get_wot_nick_from_ts_metadata", "on")
	parser.set("General", "update_cache_in_replays", "off")
	parser.set("General", "ts_nick_search_enabled", "on")
	parser.set("General", "nick_extract_patterns", "")
	parser.add_section("NameMappings")
	parser.add_section("TSClientQueryService")
	parser.set("TSClientQueryService", "host", "localhost")
	parser.set("TSClientQueryService", "port", "25639")
	parser.set("TSClientQueryService", "polling_interval", "0.1")
	parser.add_section("VoiceChatNotifications")
	parser.set("VoiceChatNotifications", "enabled", "on")
	parser.set("VoiceChatNotifications", "self_enabled", "on")
	parser.add_section("MinimapNotifications")
	parser.set("MinimapNotifications", "enabled", "on")
	parser.set("MinimapNotifications", "self_enabled", "on")
	parser.set("MinimapNotifications", "action", "attackSender")
	parser.set("MinimapNotifications", "repeat_interval", "3.5")
	with open(path, "w") as f:
		parser.write(f)

def set_setting(group, name, value):
	path = os.path.join(get_ini_dirpath(), "tessu_mod.ini")
	parser = ConfigParser.SafeConfigParser()
	parser.read([path])
	parser.set(group, name, value)
	with open(path, "w") as f:
		parser.write(f)
