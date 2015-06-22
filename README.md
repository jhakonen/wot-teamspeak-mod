TessuMod
========
A modification for integrating TeamSpeak into Wargaming's World of Tanks game.

The mod provides visual feedback in-game when a player speaks in TeamSpeak and positions speakers voice in TeamSpeak so that their voice appears to come from their vehicle's direction on battlefield.

The visual feedback includes:
- Normal ingame voice chat notifications under player's name in e.g. training room, platoon, etc. views:  
![](https://github.com/jhakonen/wot-teamspeak-mod/blob/master/docs/wiki/trainingroom.png)
- and in battle (under player's name in side panels, speaker icon above vehicles and focus animation in minimap):  
![](https://github.com/jhakonen/wot-teamspeak-mod/blob/master/docs/wiki/battle_preview.jpg)

For enabling audio positioning you need to [install TessuMod plugin](https://github.com/jhakonen/wot-teamspeak-mod/wiki/TeamSpeak-Plugins#tessumod-plugin) for TeamSpeak. Plugin's installer is included in mod's release archive.

Installation
------------
1. [Download newest release](https://github.com/jhakonen/wot-teamspeak-mod/releases) and extract it to your WOT folder.
2. Download and install TS 3 client from http://www.teamspeak.com/?page=downloads

Usage
-----
1. Start TS client
2. Connect to TS server and join to a channel with your platoon/team mates
3. Start WOT and join a battle with your team mates

Notes on functionality
----------------------
The mod maps your WOT nickname to your TS nickname by inserting your WOT nickname to your TS client's meta data which will be then available to other TessuMods installed to your team mates' games. The presence of that nickname in you meta data enables other players to see you speaking in their WOTs. Respectively presence of the nickname in other TS users' meta data enables you to see them speaking in your WOT game. As such other all your team mates should have TessuMod installed for this to work as expected.

If the WOT nickname isn't present in speaking TS user's meta data then TessuMod, as a fallback solution, tries to find WOT player in the battle with same nickname and sets that as speaking player. Comparison is done in case-insensitive manner.

If none of the players matched then configuration options may have rules which first extract nickname from TS nickname (e.g. if TS nickname has WOT nickname and user's clan tag, or maybe user's real name) and then map the extracted nickname using mapping rules to configured WOT nickname.

The mod also collects successful matches into a cache file (located at res_mods/configs/tessu_mod_cache.ini) and the file is used to match players to TS users if the above mentioned rules fail to provide successful match. The cache stores matched TS users and players by their unique ID values. This helps the mod to remember matches even if user changes his TS nickname.

If still no matching player is found then nothing happens.

License
-------
This mod is licensed with LGPL v2.1.

Development
-----------
With bugs and improvement ideas please use [issues page](https://github.com/jhakonen/wot-teamspeak-mod/issues) to report them.
Also, pull requests are welcome. :)

TODO
----
See [issues page](https://github.com/jhakonen/wot-teamspeak-mod/issues).

Changelog
---------
See [changelog in wiki](https://github.com/jhakonen/wot-teamspeak-mod/wiki/Changelog).
