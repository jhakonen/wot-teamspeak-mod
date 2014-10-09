Feature: Notifications in garage
	In order to know that TessuMod works
	As an user
	I want to know that the mod can connect to TeamSpeak client
	
	Scenario: TS is running and user starts WOT
		Given TS is running
		When user starts and logins to WOT
		Then "Connected to TeamSpeak client" is shown in notification center
		And no errors occurred