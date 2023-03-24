#!/usr/bin/env python3

global CAN_PREVIEW
CAN_PREVIEW: bool = False

from typing import Optional, Iterable
try:
    from linkpreview import link_preview
    CAN_PREVIEW = True
except ModuleNotFoundError:
    pass

import urllib.request
import hashlib
import os
import shutil
import sys

from .signalAttachment import Attachment
from .signalCommon import __typeError__

global DEBUG
DEBUG: bool = True

class Preview(object):
    def __init__(self,
                    configPath: str,
                    fromDict:dict[str, object] = None,
                    rawPreview:dict[str, object] = None,
                    generatePreview: bool = False,
                    url: Optional[str] = None,
                    title: Optional[str] = None,
                    description: Optional[str] = None,
                    image: Optional[Attachment|str] = None,
                ) -> None:
    # Check config_path:
        if (isinstance(configPath, str) == False):
            __typeError__("config_path", "str", configPath)
    # Check from_dict:
        if (fromDict != None and isinstance(fromDict, dict) == False):
            __typeError__("from_dict", "dict", fromDict)
    # Check rawPreview:
        if (rawPreview != None and isinstance(rawPreview, dict) == False):
            __typeError__("rawPreview", "dict", rawPreview)
    # Check generate preview:
        if (isinstance(generatePreview, bool) == False):
            __typeError__("generatePreview", "bool", generatePreview)
    # Check url:
        if (url != None and isinstance(url, str) == False):
            __typeError__("url", "str", url)
    # Check title:
        if (title != None and isinstance(title, str) == False):
            __typeError__("title", "str", title)
    # Check description:
        if (description != None and isinstance(description, str) == False):
            __typeError__("description", "str", description)
    # Check image:
        if (image != None and isinstance(image, Attachment) == False and isinstance(image, str) == False):
            __typeError__("image", "Attachment | str", image)
# Set internal Vars:
        self._configPath = configPath
# Set external properties:
        self.url: Optional[str] = url
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.image: Attachment
        if (isinstance(image, Attachment) == True):
            self.image = image
        elif(isinstance(image, str) == True):
            self.image = Attachment(configPath=configPath, localPath=image)
# Parse from_dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
# Parse raw preview:
        elif (rawPreview != None):
            self.__fromRawPreview__(rawPreview)
# Generate raw preview from url:
        elif (generatePreview == True):
            if (self.url == None):
                errorMessage = "If generatePreview is True, url must be defined."
                raise RuntimeError(errorMessage)
            if (CAN_PREVIEW == True):
                self.__generatePreview__()
        return

####################
# Init:
####################
    def __fromRawPreview__(self, rawPreview:dict[str, object]) -> None:
        # print(rawPreview)
        self.url = rawPreview['url']
        self.title = rawPreview['title']
        self.description = rawPreview['description']
        self.image = None
        if (rawPreview['image'] != None):
            self.image = Attachment(self._configPath, rawAttachment=rawPreview['image'])
        return

    def __generatePreview__(self) -> None:
    # Generate preview:
        preview = link_preview(self.url)
    # Set title:
        self.title = preview.title
    # Set description:
        self.description = preview.description
    # Create the directory to store preview images if it doesn't exist:
        previewPath = os.path.join(self._configPath, 'previews')
        if (os.path.exists(previewPath) == False):
            try:
                os.mkdir(previewPath)
            except Exception as e:
                errorMessage = "FATAL: Failed to create preview directory '%s': %s" % (previewPath, str(e.args))
                raise RuntimeError(errorMessage)
    # Create the filename by hashing the url, and create the absolute path:
        hashResult = hashlib.md5(preview.image.encode())
        previewImageFilename = hashResult.hexdigest()
        previewImageFilePath = os.path.join(previewPath, previewImageFilename)
    # Check if the file exists and create the attachment:
        if (os.path.exists(previewImageFilePath) == True):
            self.image = Attachment(self._configPath, localPath=previewImageFilePath)
            return
# Download the image:
    # Try to open the url:
        try:
            response = urllib.request.urlopen(preview.image)
        except Exception as e:
            if (DEBUG == True):
                errorMessage = "Failed to open url: '%s': %s" % (preview.image, str(e.args))
                print(errorMessage, file=sys.stderr)
            self.image = None
            return
    # Try to open the destination file:
        try:
            fileHandle = open(previewImageFilePath, 'wb')
        except Exception as e:
            if (DEBUG == True):
                errorMessage = "Failed to open file '%s' for writing(binary): %s" % (previewImageFilePath, str(e.args))
                print(errorMessage, file=sys.stderr)
            self.image = None
            return
    # Copy the data to the file:
        shutil.copyfileobj(response, fileHandle)
        fileHandle.close()
    # Create the attachment:
        self.image = Attachment(configPath=self._configPath, localPath=previewImageFilePath)
        return

######################
# To / From Dict:
######################
    def __toDict__(self) -> dict[str, object]:
        previewDict = {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "image": None,
        }
        if (self.image != None):
            previewDict['image'] = self.image.__toDict__()
        return previewDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
        self.url = fromDict['url']
        self.title = fromDict['title']
        self.description = fromDict['description']
        self.image = None
        if (fromDict['image'] != None):
            self.image = Attachment(configPath=self._configPath, fromDict=fromDict['image'])
        return