Feature: Feedback in battle
	In order to see who is speaking
	As a player
	I want to see speak feedback in players lists
	and a speaker icon above other players' tanks

	Scenario: Player starts speaking
		Given WOT is running and in battle
		And TS is running
		And TS is connected to server
		And player "TuhoajaErkki" is in battle
		And player "TuhoajaErkki" TS name is "Erkki Meikalainen" and has TessuMod installed
		When TS user "Erkki Meikalainen" starts speaking
		Then I see speak feedback start for player "TuhoajaErkki"

	Scenario: Player stops speaking
		Given WOT is running and in battle
		And TS is running
		And TS is connected to server
		And player "TuhoajaErkki" is in battle
		And player "TuhoajaErkki" TS name is "Erkki Meikalainen" and has TessuMod installed
		And TS user "Erkki Meikalainen" is speaking
		When TS user "Erkki Meikalainen" stops speaking
		Then I see speak feedback end for player "TuhoajaErkki"
