#!/usr/bin/env python3

from typing import Optional, Iterator
import sys
import os
import json

global DEBUG
DEBUG: bool = True
#############################################################################################
class Sticker(object):
    def __init__(self,
                    packId: str,
                    packPath: str,
                    fromDict: Optional[dict[str, object]] = None,
                    fromManifest: Optional[dict[str, str]] = None,
                    id: Optional[int] = None,
                    emoji: Optional[str] = None,
                    filePath: Optional[str] = None,
                    contentType: Optional[str] = None,
                ) -> None:
    # TODO: Argument checks:
    # Set internal vars:
        self._packId: str = packId
        self._packPath: str = packPath
    # Set external properties:
        self.id: int = id
        self.emoji: str = emoji
        self.filePath: str = filePath
        self.contentType: str = contentType
    # Parse fromDict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from manifest file:
        if (fromManifest != None):
            self.__fromManifest__(fromManifest)
        return
##########################
# Init:
##########################
    def __fromManifest__(self, fromManifest:dict[str, str]) -> None:
        self.id = fromManifest['id']
        self.emoji = fromManifest['emoji']
        fileName = fromManifest['file']
        self.filePath = os.path.join(self._packPath, fileName)
        self.contentType = fromManifest['contentType']
        return

#######################
# Overrides:
#######################
    def __eq__(self, __o: object) -> bool:
        if (isinstance(__o, Sticker) == True):
            if (self.id != None and __o.id != None):
                if (self.id == __o.id):
                    return True
        return False
    
    def __str__(self) -> str:
        stickerString = "%s:%i" % (self._packId, self.id)
        return stickerString
    
#######################
# To / From Dict:
#######################
    def __toDict__(self) -> dict[str, object]:
        stickerDict = {
            "_packId": self._packId,
            "id": self.id,
            "emoji": self.emoji,
            "filePath": self.filePath,
            "contentType": self.contentType
        }
        return stickerDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
        self._packId = fromDict['_packId']
        self.id = fromDict['id']
        self.emoji = fromDict['emoji']
        self.filePath = fromDict['filePath']
        self.contentType = fromDict['contentType']
        return

#############################################################################################
class StickerPack(object):
    def __init__(self,
                    packId: str,
                    packPath: str,
                    fromDict: Optional[dict[str, object]] = None,
                    fromManifest: Optional[dict[str, object]] = None,
                    title: Optional[str] = None,
                    author: Optional[str] = None,
                    cover: Optional[Sticker] = None,
                    stickers: Optional[list[Sticker] | tuple[Sticker]] = None,
                ) -> None:
    # TODO: Argument checks:
    # Set internal Vars:
        self._packPath: str = packPath
    # Set external properties:
        self.packId: str = packId
        self.title: str = title
        self.author: str = author
        self.cover: Sticker = cover
        self.stickers: list[Sticker] = stickers
    # Parse fromDict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from Manifest:
        elif (fromManifest != None):
            self.__fromManifest__(fromManifest)
        return

########################
# Init:
########################
    def __fromManifest__(self, manifestDict:dict[str, object]) -> None:
        self.title = manifestDict['title']
        self.author = manifestDict['author']
        self.cover = Sticker(packId=self.packId, packPath=self._packPath, fromManifest=manifestDict['cover'])
        self.stickers = []
        for stickerDict in manifestDict['stickers']:
            sticker = Sticker(packId=self.packId, packPath=self._packPath, fromManifest=stickerDict)
            self.stickers.append(sticker)
        return

#####################
# Overrides:
#####################
    def __getitem__(self, index:str | int) -> Sticker:
        if (isinstance(index, str) == True):
            for sticker in self.stickers:
                if (sticker.emoji == index):
                    return sticker
            raise IndexError("index %s not found" % index)
        elif (isinstance(index, int) == True):
            return self.stickers[index]
        else:
            raise TypeError("index must be of type str or int")

    def __iter__(self) -> Iterator[Sticker]:
        return iter(self.stickers)

####################
# To / From Dict:
####################
    def __toDict__(self) -> dict:
        stickerPackDict = {
            'packId': self.packId,
            'title': self.title,
            'author': self.author,
            'cover': None,
            'stickers': [],
        }
        if (self.cover != None):
            stickerPackDict['cover'] = self.cover.__toDict__()
        for sticker in self.stickers:
            stickerPackDict['stickers'].append(sticker.__toDict__())
        return stickerPackDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
        self.packId = fromDict['packId']
        self.title = fromDict['title']
        self.author = fromDict['author']
        if (fromDict['cover'] != None):
            self.cover = Sticker(packId=self.packId, packPath=self._packPath, fromDict=fromDict['cover'])
        else:
            self.cover = None
        self.stickers = []
        for stickerDict in fromDict['stickers']:
            self.stickers.append(Sticker(packId=self.packId, packPath=self._packPath, fromDict=stickerDict))
        return
#######################
# Getters:
#######################
    def getById(self, id:int):
        for sticker in self.stickers:
            if (sticker.id == id):
                return sticker
        return None
#############################################################################################
class StickerPacks(object):
    def __init__(self,
                    configPath: str,
                ) -> None:
    # TODO: Argument checks:
    # Set internal vars:
        self._configPath = configPath
    # Set external properties:
        self.packs: list[StickerPack] = []
    # Load Known sticker packs:
        self.__load__()
        if (DEBUG == True and len(self.packs) == 0):
            warningMessage = "WARNING: No stickers loaded, sending stickers will be disabled until they are recieved."
            print(warningMessage, file=sys.stderr)
        return

##################
# Load:
##################
    def __load__(self) -> None:
    # Verify stickers path exists:
        stickersPath = os.path.join(self._configPath, 'stickers')
        if (os.path.exists(stickersPath) == False):
            if (DEBUG == True):
                errorMessage = "FATAL: sticker path '%s' doesn't exist." % stickersPath
                print(errorMessage, file=sys.stderr)
            return
    # Get the pack id's and verify len is not 0:
        packIds: list[str] = os.listdir(stickersPath)
        if (len(packIds) == 0):
            if (DEBUG == True):
                errorMessage = "FATAL: no stickers sync'd"
                print(errorMessage, file=sys.stderr)
            return
    # Load the manifest files from the sticker packs:
        self.packs = []
        for packId in packIds:
            packPath = os.path.join(stickersPath, packId)
            manifestPath = os.path.join(packPath, 'manifest.json')
        # Try to open the file:
            try:
                fileHandle = open(manifestPath, 'r')
            except Exception as e:
                if (DEBUG == True):
                    errorMessage = "FATAL: Unable to open mainfest file '%s' for reading: %s" % (manifestPath, str(e.args))
                    print(errorMessage, file=sys.stderr)
                continue
        # Try to load the json from the file:
            try:
                manifestDict: dict[str, object] = json.loads(fileHandle.read())
            except json.JSONDecodeError as e:
                if (DEBUG == True):
                    errorMessage = "FATAL: Couldn't load json from '%s': %s" % (manifestPath, e.msg)
                    print(errorMessage, file=sys.stderr)
                continue
        # Close the file and load the pack:
            fileHandle.close()
            pack = StickerPack(packId=packId, packPath=packPath, fromManifest=manifestDict)
            self.packs.append(pack)
        return
###########################
# Helpers:
###########################
    def __update__(self) -> None:
    # Verify stickers path exists:
        stickersPath = os.path.join(self._configPath, 'stickers')
        if (os.path.exists(stickersPath) == False):
            if (DEBUG == True):
                errorMessage = "DEBUG: sticker path '%s' doesn't exist." % stickersPath
                print(errorMessage, file=sys.stderr)
            return
    # Get the pack id's and verify len is not 0:
        packIds: list[str] = os.listdir(stickersPath)
        if (len(packIds) == 0):
            errorMessage = "FATAL: no stickers sync'd"
            raise RuntimeError(errorMessage)
    # Check to see if there is a new id:
        knownPackIds = [pack.packId for pack in self.packs] # Gather old id's
        for packId in packIds:
            if (packId not in knownPackIds):
                packPath = os.path.join(stickersPath, packId)
                manifestPath = os.path.join(packPath, 'manifest.json')
            # Try to open the file:
                try:
                    fileHandle = open(manifestPath, 'r')
                except Exception as e:
                    if (DEBUG == True):
                        errorMessage = "DEBUG: Unable to open mainfest file '%s' for reading: %s" % (manifestPath, str(e.args))
                        print(errorMessage, file=sys.stderr)
                    continue
            # Try to load the json from the file:
                try:
                    manifestDict: dict[str, object] = json.loads(fileHandle.read())
                except json.JSONDecodeError as e:
                    if (DEBUG == True):
                        errorMessage = "DEBUG: Couldn't load json from '%s': %s" % (manifestPath, e.msg)
                        print(errorMessage, file=sys.stderr)
                    continue
            # Close the file and load the pack:
                fileHandle.close()
                pack = StickerPack(packId=packId, packPath=packPath, fromManifest=manifestDict)
                self.packs.append(pack)
        return

########################
# Getters:
########################
    def getPackByName(self, name:str) -> Optional[StickerPack]:
        for pack in self.packs:
            if (pack.title == name):
                return pack
        return None
    
    def getPackById(self, id:str) -> Optional[StickerPack]:
        for pack in self.packs:
            if (pack.packId == id):
                return pack
        return None
    
    def getSticker(self, packId:str, stickerId:int) -> Optional[Sticker]:
        pack = self.getPackById(packId)
        if (pack == None): 
            return None
        sticker = pack.getById(stickerId)
        return sticker