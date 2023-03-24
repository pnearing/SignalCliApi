#!/usr/bin/env python3

from typing import TypeVar, Optional
import mimetypes
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, find_xdg_open
from .signalThumbnail import Thumbnail

Self = TypeVar("Self", bound="Attachment")

class Attachment(object):
    def __init__(self,
                    configPath: str,
                    fromDict: Optional[dict] = None,
                    rawAttachment: Optional[dict] = None,
                    contentType: Optional[str] = None,
                    filename: Optional[str] = None,
                    size: Optional[int] = None,
                    localPath: Optional[str] = None,
                    thumbnail: Optional[Thumbnail] = None,
                ) -> None:
    # Check config_path:
        if (isinstance(configPath, str) == False):
            __type_error__("config_path", "str", configPath)
    # Check from_dict:
        if (fromDict != None and isinstance(fromDict, dict) == False):
            __type_error__("from_dict", "dict[str, object]", fromDict)
    # Check raw Attachment:
        if (rawAttachment != None and isinstance(rawAttachment, dict) == False):
            __type_error__("rawAttachment", "dict[str, object]", rawAttachment)
    # Check content type:
        if (contentType != None and isinstance(contentType, str) == False):
            __type_error__("contentType", "str", contentType)
    # Check filename:
        if (filename != None and isinstance(filename, str) == False):
            __type_error__("filename", "str", filename)
    # Check size:
        if (size != None and isinstance(size, int) == False):
            __type_error__("size", "int", size)
    # Check localPath:
        if (localPath != None and isinstance(localPath, str) == False):
            __type_error__("localPath", "str", localPath)
    # Check thumbnail:
        if (thumbnail != None and isinstance(thumbnail, Thumbnail) == False):
            __type_error__("thumbnail", "Thumbnail", thumbnail)

    # Set internal vars:
        self._configPath: str = configPath
        self._xdgopenPath: Optional[str] = find_xdg_open()
    # Set external vars:
        self.contentType: Optional[str] = contentType
        self.fileName: Optional[str] = filename
        self.size: Optional[int] = size
        self.localPath: Optional[str] = localPath
        self.exists: bool = False
        if (localPath != None):
            self.exists = os.path.exists(localPath)
        self.thumbnail: Thumbnail = thumbnail
    # Parse fromdict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from raw Attachemnt
        elif (rawAttachment != None):
            self.__fromRawAttachment__(rawAttachment)
    # Set properties from local path:
        else:
            if (self.localPath != None):
                self.exists = os.path.exists(self.localPath)
                if (self.exists == True):
                    self.contentType = mimetypes.guess_type(localPath)
                    self.fileName = os.path.split(localPath)[-1]
                    self.size = os.path.getsize(localPath)
            else:
                self.exists = False
        return

    def __fromRawAttachment__(self, rawAttachment:dict) -> None:
        print(rawAttachment.keys())
        # raise NotImplemented
        self.contentType = rawAttachment['contentType']
        self.fileName = rawAttachment['filename']
        if ('size' in rawAttachment.keys()):
            self.size = rawAttachment['size']
        else:
            self.size = None
        if ('contact_id' in rawAttachment.keys()):
            self.localPath = os.path.join(self._configPath, 'attachments', rawAttachment['contact_id'])
            self.exists = os.path.exists(self.localPath)
        else:
            self.localPath = None
            self.exists = False
        self.thumbnail = None
        if ('thumbnail' in rawAttachment.keys()):
            self.thumbnail = Thumbnail(configPath=self._configPath, rawThumbnail=rawAttachment['thumbnail'])
        return

#########################
# To / From Dict:
#########################
    def __toDict__(self) -> dict:
        attachmentDict = {
            'contentType': self.contentType,
            'fileName': self.fileName,
            'size': self.size,
            'localPath': self.localPath,
            'thumbnail': None,
        }
        if (self.thumbnail != None):
            attachmentDict['thumbnail'] = self.thumbnail.__toDict__()
        return attachmentDict

    def __fromDict__(self, fromDict:dict) -> None:
        self.contentType = fromDict['contentType']
        self.id = fromDict['contact_id']
        self.fileName = fromDict['fileName']
        self.size = fromDict['size']
        self.localPath = fromDict['localPath']
        if (self.localPath != None):
            self.exists = os.path.exists(self.localPath)
        else:
            self.exists = False
        self.thumbnail = None
        if (fromDict['thumbnail'] != None):
            self.thumbnail = Thumbnail(configPath=self._configPath, fromDict=fromDict['thumbnail'])
        return
########################
# Getters:
########################
    def getFilePath(self) -> Optional[str]:
        if (self.localPath != None):
            return self.localPath
        if (self.thumbnail != None and self.thumbnail.localPath != None):
            return self.thumbnail.localPath
        return None
########################
# Methods:
########################
    def display(self) -> bool:
        if (self._xdgopenPath == None):
            return False
        if (self.localPath != None and self.exists == True):
            try:
                check_call([self._xdgopenPath, self.localPath])
                return True
            except CalledProcessError:
                return False
        elif(self.thumbnail != None):
            return self.thumbnail.display()
        return False