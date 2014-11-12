import urllib
import json

def get_json_url(url):
	return json.loads(urllib.urlopen(url).read())

releases = get_json_url("https://api.github.com/repos/jhakonen/wot-teamspeak-mod/releases")
for release in releases:
	for asset in release["assets"]:
		print "File '{0}' has been downloaded {1} times.".format(asset["name"], asset["download_count"])
