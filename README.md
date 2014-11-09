TessuMod
========

JHakonen's mod for integrating TeamSpeak(TS) into World of Tanks (WOT).

This mod enables ingame notifications when a player speaks in TS. The notifications include:
- Normal ingame voice chat notifications:
  - green wave animations under player's name at garage in e.g. training room, platoon, etc. views,
  - green wave animations at battle in the player panels,
  - speaker icon on top of a tank in battle
- Notication in minimap around speaking player's tank marker

Compatible with WOT version 0.9.4. 

Installation
------------
1. [Download the mod](http://db.orangedox.com/JhI1RNg8D2UYCgEyF4/TessuMod-0.3.4.zip) and extract it to your WOT folder.
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

Execute in command prompt:

    package.py

Extract generated zip-archive to your WOT folder.

Easy one liner (using 7-zip's command line tool 7za.exe) to compile and install to WOT, e.g:

    package.py && 7za x TessuMod*.zip -oE:\Games\World_of_Tanks -y

Tests
-----
TessuMod has a battery of unit and behaviour tests.

To execute them you need:
 * Windows
 * Command Prompt
 * Python 2.7
 * [Behave](http://pythonhosted.org/behave/install.html) test runner
 * [Coverage.py](https://pypi.python.org/pypi/coverage)
 * [Nose](https://nose.readthedocs.org/en/latest)

Execute behavior tests in command prompt with:

    behave

Coverage report is shown at end of the execution and is also generated in html form to coverage_report subfolder.

For unit tests execute in command prompt:

    nosetests

TODO
----
- Add settings ui using ModSettingsAPI
- Add 3D positional audio support (need a new TS plugin for this)

Changelog
---------
Version 0.4.0, master:
- Added caching of matched TS users and players.
- Added unit and behavior tests.
- Added coverage reporting for behavior tests.
- Added support to WOT version 0.9.4.

Version 0.3.3, 12.10.2014:
- Removed logging spam while speaking in garage.

Version 0.3.2, 7.10.2014:
- Fixed regression: 'not connected' -spam in system notification center.

Version 0.3.1, 6.10.2014:
- Refactored client query handling to use asynchat.
- Client query connection is now closed and reconnected if an API error occurs.
- Fixed mapping rules not working for TS nick with space in name.
- Fixed client query handling breaking if recv() didn't return full line.
- Fixed client query commands sent before welcome message was fully received.

Version 0.3.0, 3.10.2014:
- Fixed speak indicators left active if TS was closed while someone was speaking.
- Added configuration options.

Version 0.2.0, 25.9.2014:
- Added notification to minimap when player is speaking.
- Reduced amount of logging spam in python.log.
- Fixed wot nickname not updating to teamspeak client if the client wasn't connected to teamspeak server before entering garage or battle.

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

