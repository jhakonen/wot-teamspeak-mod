Feature: Notifications in garage
	In order to know that TessuMod works
	As an user
	I want to know that the mod can connect to TeamSpeak client
	
	Background:
		Given TS plugin is installed

	Scenario: TS is running and user starts WOT
		Given TS is running
		 When user starts and logins to WOT
		 Then "Connected to TeamSpeak client" is shown in notification center
		  And no errors occurred

	Scenario: User starts TS while WOT is running
		Given WOT is running and in garage
		 When user starts TS
		 Then "Connected to TeamSpeak client" is shown in notification center
		  And no errors occurred

	Scenario: TS and WOT is running and TS is closed
		Given TS is running
		  And WOT is running and in garage
		  And mod is connected to TS
		 When user closes TS
		 Then "Disconnected from TeamSpeak client" is shown in notification center
		  And no errors occurred

	Scenario: TS plugin is not installed and 3D audio is enabled
		Given TS plugin is not installed
		  And TS is running
		  And 3D audio is enabled
		 When user starts and logins to WOT
		 Then "Connected to TeamSpeak client" is shown in notification center
		  And "TS plugin is not installed" is shown in notification center
		  And "3D audio is disabled" is shown in notification center
		  And no errors occurred

	Scenario: TS plugin is not installed and 3D audio is disabled
		Given TS plugin is not installed
		  And TS is running
		  And 3D audio is disabled
		 When user starts and logins to WOT
		 Then "Connected to TeamSpeak client" is shown in notification center
		  And "3D audio is disabled" is not shown in notification center
		  And no errors occurred

	Scenario: TS plugin is too new and 3D audio is enabled
		Given TS plugin version is newer than mod version 
		  And TS is running
		  And 3D audio is enabled
		 When user starts and logins to WOT
		 Then "Connected to TeamSpeak client" is shown in notification center
		  And "out of date" is shown in notification center
		  And "3D audio is disabled" is shown in notification center
		  And no errors occurred
