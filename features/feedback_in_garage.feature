Feature: Feedback in garage
	In order to see who is speaking
	As a player
	I want to see speak feedback in garage

	Scenario: Player is in training room and his WOT name changes
		Given WOT is running and in garage
		  And TS is running
		  And TS is connected to server
		  And TS user "Erkki Meikalainen" is in my channel
		  And player "TuhoajaErkki" is logged in
		  And TS user "Erkki Meikalainen" player name is "SomeGuy" and has TessuMod installed
		  And TS user "Erkki Meikalainen" is speaking
		 When TS user "Erkki Meikalainen" stops speaking
		  And TS user "Erkki Meikalainen" player name changes to "TuhoajaErkki"
		  And TS user "Erkki Meikalainen" starts speaking
		 Then I see speak feedback start for player "TuhoajaErkki"
		  And no errors occurred
