# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2014  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

TARGET = tessumod_plugin
TEMPLATE = lib
QT += widgets

INCLUDEPATH += include

SOURCES += \
    src/ui/settingsdialog.cpp \
    src/entities/settings.cpp \
    src/entities/user.cpp \
    src/entities/vector.cpp \
    src/entities/camera.cpp \
    src/usecases/usecasefactory.cpp \
    src/usecases/usecases.cpp \
    src/storages/userstorage.cpp \
    src/storages/camerastorage.cpp \
    src/adapters/audioadapter.cpp \
    src/adapters/voicechatadapter.cpp \
    src/adapters/gamedataadapter.cpp \
    src/storages/adapterstorage.cpp \
    src/storages/settingsstorage.cpp \
    src/drivers/inisettingsfile.cpp \
    src/drivers/openalbackend.cpp \
    src/drivers/teamspeakplugin.cpp \
    src/drivers/wotconnector.cpp \
    src/adapters/uiadapter.cpp \
    src/main.cpp \
    src/libs/openal.cpp

HEADERS +=\
    src/ui/settingsdialog.h \
    src/entities/settings.h \
    src/entities/user.h \
    src/entities/vector.h \
    src/entities/camera.h \
    src/usecases/usecasefactory.h \
    src/usecases/usecases.h \
    src/interfaces/storages.h \
    src/interfaces/usecasefactory.h \
    src/interfaces/adapters.h \
    src/storages/userstorage.h \
    src/storages/camerastorage.h \
    src/interfaces/drivers.h \
    src/adapters/audioadapter.h \
    src/adapters/voicechatadapter.h \
    src/adapters/gamedataadapter.h \
    src/storages/adapterstorage.h \
    src/storages/settingsstorage.h \
    src/drivers/inisettingsfile.h \
    src/drivers/openalbackend.h \
    src/drivers/teamspeakplugin.h \
    src/drivers/wotconnector.h \
    src/adapters/uiadapter.h \
    src/entities/enums.h \
    src/libs/openal.h

RESOURCES += \
	resources.qrc

FORMS += \
    src/ui/settingsdialog.ui
