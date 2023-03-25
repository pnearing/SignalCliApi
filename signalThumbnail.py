#!/usr/bin/env python3

from typing import Optional
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, find_xdg_open

class Thumbnail(object):
    def __init__(self,
                    configPath: str,
                    fromDict: Optional[dict[str, object]] = None,
                    rawThumbnail: Optional[dict[str, object]] = None,
                    contentType: Optional[str] = None,
                    filename: Optional[str] = None,
                    localPath: Optional[str] = None,
                    size: Optional[int] = None,
                ) -> None:
    # TODO Argument checks
    # Set internal vars:
        self._configPath: str = configPath
        self._xdgopenPath: Optional[str] = find_xdg_open()
    # Set external properties:
        self.contentType: str = contentType
        self.filename: str = filename
        self.localPath: str = localPath
        self.exists: bool = False
        if (localPath != None):
            self.exists = os.path.exists(localPath)
        self.size: int = size
    # Parse from_dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse raw thumbnail:
        elif (rawThumbnail != None):
            self.__fromRawThumbnail__(rawThumbnail)
        return

###################
# Init:
###################
    def __fromRawThumbnail__(self, rawThumbnail:dict[str, object]) -> None:
        # print(rawThumbnail)
        self.contentType = rawThumbnail['content_type']
        self.filename = rawThumbnail['filename']
        self.localPath = os.path.join(self._configPath, 'attachments', rawThumbnail['contact_id'])
        self.exists = os.path.exists(self.localPath)
        self.size = rawThumbnail['size']
        return

############################
# To / From dict:
############################
    def __toDict__(self) -> dict[str, object]:
        thumbnailDict = {
            'content_type': self.contentType,
            'filename': self.filename,
            'local_path': self.localPath,
            'size': self.size,
        }
        return thumbnailDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
        self.contentType = fromDict['content_type']
        self.filename = fromDict['filename']
        self.localPath = fromDict['local_path']
        self.exists = False
        if (self.localPath != None):
            self.exists = os.path.exists(self.localPath)
        else:
            self.exists = False
        self.size = fromDict['size']
        return

############################
# Methods:
############################
    def display(self) -> bool:
        if (self._xdgopenPath == None):
            return False
        if (self.exists == False):
            return False
        try:
            check_call([self._xdgopenPath, self.localPath])
        except CalledProcessError:
            return False
        return True