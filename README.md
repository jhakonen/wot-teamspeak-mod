TessuMod
========

JHakonen's mod for integrating TeamSpeak(TS) into World of Tanks (WOT).

This mod enables ingame notifications when a player speaks in TS. The notifications include:
- Normal ingame voice chat notifications:
  - green wave animations under player's name at garage in e.g. training room, platoon, etc. views,
  - green wave animations at battle in the player panels,
  - speaker icon on top of a tank in battle
- Notication in minimap around speaking player's tank marker

Compatible with WOT version 0.9.7. 

Installation
------------
1. [Download the mod](https://github.com/jhakonen/wot-teamspeak-mod/releases/download/0.5.3/TessuMod-0.5.3.zip) and extract it to your WOT folder.
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
