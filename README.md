TessuMod
========

JHakonen's mod for integrating TeamSpeak(TS) into World of Tanks (WOT).

WOT has already a support for voice communication which can be enabled from settings. When a player speaks his name in battle's player list has a green wave animation which shows current speaker. There is also a green speaker icon above the speaking player's tank. This mod enables those functionalities for TS as well.

Compatible with WOT version 0.9.2. 

Installation
------------
1. [Download the mod](http://db.orangedox.com/OK9gTmNzSWICsZAFVG/TessuMod-0.1.2.zip) and extract it to your WOT folder.
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

If still no matching WOT player is found then nothing happens.

License
-------
This mod is licensed with LGPL v2.1.

Development
-----------
With bugs and improvement ideas please use the Issues to report them.
Also, pull requests are welcome. :)

To build the mod, you will need:
 * Windows
 * Command Prompt
 * Python 2.7

1. Run package.py
2. Extract generated zip-archive to your WOT folder

Easy one liner (using 7-zip's command line tool 7za.exe) to compile and install to WOT, e.g:

    package.py && 7za x TessuMod*.zip -oE:\Games\World_of_Tanks -y

Changelog
---------
Version 0.1.2, 15.9.2014:
- Fixed battle failing to start if TS client wasn't running.
- Fixed WOT hanging a second every time the mod tried to (re)connect to TS.
- Fixed speak indicators not working on first run (with the mod) in garage before joining a battle.
- Improved CameraNode.pyc so that it is more compatible with other mods.
- Reduced amount of logging spam in python.log.

Version 0.1.1, 14.9.2014:
- Fixed speak indicators in garage either not shown, or after battle stuck always on

Version 0.1.0, 14.9.2014:
- first version

