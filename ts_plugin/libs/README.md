# Contents

This folder contains OpenAL Soft 1.16.0 ready built libraries.

The contents are:
- OpenAL32.dll - 32bit library
- OpenAL32.pdb - 32bit library debugging symbols
- OpenAL64.dll - 64bit library
- OpenAL64.pdb - 64bit library debugging symbols
- changes.patch - additional changes made to the sources before building the libraries

# Building
The libraries have been built with Visual Studio 2012 Express, using its command line prompts.

From VS2012 x86 Native Tools Command Prompt:

    cmake -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLIBNAME=OpenAL32 -DALSOFT_BACKEND_WINMM=OFF -DALSOFT_BACKEND_MMDEVAPI=OFF -DALSOFT_BACKEND_WAVE=OFF path\to\sources
    nmake

From VS2012 x64 Cross Tools Command Prompt:

    cmake -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLIBNAME=OpenAL32 -DALSOFT_BACKEND_WINMM=OFF -DALSOFT_BACKEND_MMDEVAPI=OFF -DALSOFT_BACKEND_WAVE=OFF path\to\sources
    nmake
