// TessuMod: Mod for integrating TeamSpeak into World of Tanks
// Copyright (C) 2016  Janne Hakonen
//
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 2.1 of the License, or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public
// License along with this library; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
// USA
//
// Mostly copy & paste from http://edn.embarcadero.com/article/20941
//

#include <SDKDDKVer.h>
#include <stdio.h>
#include <tchar.h>
#include <dsound.h>
#include <string>
#include <iostream>
#include <vector>

using namespace std;

struct AudioDevice {
	LPGUID guid;
	wstring description;
	AudioDevice() {
		guid = NULL;
	}
	~AudioDevice() {
		delete guid;
	}
};

typedef vector<AudioDevice*> AudioDevices;

BOOL CALLBACK EnumCallBack(LPGUID guid, LPCTSTR desc,
	LPCTSTR mod, LPVOID list)
{
	AudioDevice *ad = new AudioDevice;
	if (guid == NULL) {
		ad->guid = NULL;
	} else {
		ad->guid = new GUID;
		memcpy(ad->guid, guid, sizeof(GUID));
	}
	ad->description = desc;
	(static_cast<AudioDevices*>(list))->push_back(ad);
	return true;
}

LPDIRECTSOUND pds;

int _tmain(int argc, _TCHAR* argv[]) {
	unsigned int i;
	AudioDevices ads;

	if (argc != 2) {
		wcerr << "Usage: GetDirectSoundDriverGUID.exe <substring of driver's description>" << endl;
		return 1;
	}
	wstring driverPattern = argv[1];

	if (FAILED(DirectSoundEnumerate(EnumCallBack, &ads))) {
		wcerr << "Couldn't enumerate the audio devices" << endl;
		return 1;
	}
	for (i = 0; i < ads.size(); i++) {
		if (ads[i]->description.find(driverPattern) != wstring::npos) {
			WCHAR *strGUID = new WCHAR[64];
			StringFromGUID2(*ads[i]->guid, strGUID, 64);
			wcout << strGUID << endl;
			delete[] strGUID;
			return 0;
		}
	}

	return 1;
}
