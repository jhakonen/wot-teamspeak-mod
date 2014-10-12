Feature: Feedback in battle
	In order to see who is speaking
	As a player
	I want to see speak feedback in players lists
	and a speaker icon above other players' tanks

	Background: Player is in battle and TS is connected to server
		Given WOT is running and in battle
		  And TS is running
		  And TS is connected to server

	Scenario: Another player starts speaking
		Given player "TuhoajaErkki" is in battle
		  And player "TuhoajaErkki" TS name is "Erkki Meikalainen" and has TessuMod installed
		 When TS user "Erkki Meikalainen" starts speaking
		 Then I see speak feedback start for player "TuhoajaErkki"
		  And no errors occurred

	Scenario: Another player stops speaking
		Given player "TuhoajaErkki" is in battle
		  And player "TuhoajaErkki" TS name is "Erkki Meikalainen" and has TessuMod installed
		  And TS user "Erkki Meikalainen" is speaking
		 When TS user "Erkki Meikalainen" stops speaking
		 Then I see speak feedback end for player "TuhoajaErkki"
		  And no errors occurred

	Scenario: TS user with matching name starts speaking
		Given player "TuhoajaErkki" is in battle
		  And user "TuhoajaERKKI" is in TS
		 When TS user "TuhoajaERKKI" starts speaking
		 Then I see speak feedback start for player "TuhoajaErkki"
		  And no errors occurred

	Scenario: TS user with matching extract rule starts speaking
		Given player "TuhoajaErkki" is in battle
		  And nick extract pattern "\[.+\] ([\S]+)" is set
		  And user "[T-BAD] TuhoajaERKKI / Erkki Meikalainen" is in TS
		 When TS user "[T-BAD] TuhoajaERKKI / Erkki Meikalainen" starts speaking
		 Then I see speak feedback start for player "TuhoajaErkki"
		  And no errors occurred
