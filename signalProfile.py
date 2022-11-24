#!/usr/bin/env python3

from typing import TypeVar, Optional
import os
import json
import sys
import socket

from signalCommon import __typeError__, __socketReceive__, __socketSend__
from signalTimestamp import Timestamp

global DEBUG
DEBUG:bool = True

Self = TypeVar("Self", bound="Profile")

class Profile(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    contactId: str,
                    accountPath:str|None = None,
                    fromDict:dict|None = None,
                    rawProfile:dict|None = None,
                    givenName:str|None = None,
                    familyName:str|None = None,
                    about:str|None = None,
                    emoji:str|None = None,
                    coinAddress:str|None = None,
                    avatar:str|None = None,
                    lastUpdate:Timestamp|None = None,
                    isAccountProfile:bool = False,
                    doLoad:bool = False,
                ) -> None:
    # TODO: Check args:

    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._configPath: str = configPath
        self._accountId: str = accountId
        self._contactId: str = contactId
        self._profileFilePath: Optional[str]
        if (accountPath != None):
            self._profileFilePath = os.path.join(accountPath, 'profile.json')
        else:
            self._profileFilePath = None
        self._fromSignal: bool = False
        self._isAccountProfile: bool = isAccountProfile
    # Set external vars:
        self.givenName: Optional[str] = givenName
        self.familyName: Optional[str] = familyName
        self.name: str = ''
        self.about: Optional[str] = about
        self.emoji: Optional[str] = emoji
        self.coinAddress: Optional[str] = coinAddress
        self.avatar: Optional[str] = avatar
        self.lastUpdate: Optional[Timestamp] = lastUpdate
    # Parse from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from raw profile:
        elif (rawProfile != None):
            self._fromSignal = True
            self.__fromRawProfile__(rawProfile)
    # Do load from file:
        elif (doLoad == True):
            try:
                self.__load__()
            except RuntimeError:
                if (DEBUG == True):
                    print("INFO: Creating empty profile for account: %s" % self._accountId, file=sys.stderr)
                self.__save__()
    # Find avatar:
        self.__findAvatar__()
        if (self._isAccountProfile == True):
            self.__save__()
        return

    def __fromRawProfile__(self, rawProfile:dict) -> None:
        # print (rawProfile)
        self.givenName = rawProfile['givenName']
        self.familyName = rawProfile['familyName']
        self.__setName__()
        self.about = rawProfile['about']
        self.emoji = rawProfile['aboutEmoji']
        self.coinAddress = rawProfile['mobileCoinAddress']
        if (rawProfile['lastUpdateTimestamp'] == 0):
            self.lastUpdate = None
        else:
            self.lastUpdate = Timestamp(timestamp=rawProfile['lastUpdateTimestamp'])
        self.__findAvatar__()
        return

######################
# To / From Dict:
######################

    def __toDict__(self) -> dict:
        profileDict = {
            'givenName': self.givenName,
            'familyName': self.familyName,
            'about': self.about,
            'emoji': self.emoji,
            'coinAddress': self.coinAddress,
            'avatar': self.avatar,
            'lastUpdate': None,
        }
        if (self.lastUpdate != None):
            profileDict['lastUpdate'] = self.lastUpdate.__toDict__()
        return profileDict

    def __fromDict__(self, fromDict:dict) -> None:
    # Set properties:
        self.givenName = fromDict['givenName']
        self.familyName = fromDict['familyName']
        self.__setName__()
        self.about = fromDict['about']
        self.emoji = fromDict['emoji']
        self.coinAddress = fromDict['coinAddress']
        self.avatar = fromDict['avatar']
        self.__findAvatar__()
        if (fromDict['lastUpdate'] != None):
            self.lastUpdate = Timestamp(fromDict=fromDict['lastUpdate'])
        else:
            self.lastUpdate = fromDict['lastUpdate']
        return

#####################################
# Save / Load:
####################################
    def __save__(self) -> bool:
    # Checks:
        if (self._isAccountProfile == False):
            if (DEBUG == True):
                errorMessage = "WARNING: Not account profile cannot save."
                print(errorMessage, file=sys.stderr)
            return False
        if (self._profileFilePath == None):
            if (DEBUG == True):
                errorMessage = "WARNING: File path not set, cannot save."
                print(errorMessage, file=sys.stderr)
            return False
    # Create json string to save:
        profileDict:dict = self.__toDict__()
        profileJson:str = json.dumps(profileDict)
    # Open the file:
        try:
            fileHandle = open(self._profileFilePath, 'w')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open '%s' for writing: %s" % (self._profileFilePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Write to the file and close it.
        fileHandle.write(profileJson)
        fileHandle.close()
        return True


    def __load__(self) -> bool:
    # Do checks:
        if (self._profileFilePath == None):
            if (DEBUG == True):
                errorMessage = "WARNING: Profile file path not set, cannot load."
                print(errorMessage, file=sys.stderr)
            return False
        if (self._isAccountProfile == False):
            if (DEBUG == True):
                errorMessage = "WARNING: Not account profile, cannot load."
                print(errorMessage, file=sys.stderr)
            return False
    # Try to open file:
        try:
            fileHandle = open(self._profileFilePath, 'r')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open file '%s' for reading: %s" % (self._profileFilePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Try to load the json:
        try:
            profileDict = json.loads(fileHandle.read())
        except json.JSONDecodeError as e:
            errorMessage = "FATAL: Couldnt load json from '%s': %s" % (self._profileFilePath, e.msg)
            raise RuntimeError(errorMessage)
    # Load from dict:
        self.__fromDict__(profileDict)
        return True

#######################
# Helper methods:
#######################
    def __findAvatar__(self) -> bool:
        if (self.avatar != None):
            if (os.path.exists(self.avatar) == False):
                if (DEBUG == True):
                    errorMessage = "WARNIING: Couldn't find avatar: '%s', searching..." % self.avatar
                    print(errorMessage, file=sys.stderr)
                self.avatar = None
    # Try profile avatar:
        if (self.avatar == None):
            avatarFileName = 'profile-' + self._contactId
            avatarFilePath = os.path.join(self._configPath, 'avatars', avatarFileName)
            if (os.path.exists(avatarFilePath) == True):
                self.avatar = avatarFilePath
    # Try contact avatar:
        if (self.avatar == None):
            avatarFileName = 'contact-' + self._contactId
            avatarFilePath = os.path.join(self._configPath, 'avatars', avatarFileName)
            if (os.path.exists(avatarFilePath) == True):
                self.avatar = avatarFilePath
        if (self.avatar != None):
            return True
        return False

    def __setName__(self) -> None:
        if (self.givenName == None and self.familyName == None):
            self.name = ''
        elif (self.givenName !=None and self.familyName != None):
            self.name = ' '.join([self.givenName, self.familyName])
        elif (self.givenName != None):
            self.name = self.givenName
        elif (self.familyName != None):
            self.name = self.familyName
        return

    def __merge__(self, __o:Self) -> None:
    # TODO: rewrite to be more mergey
        self.givenName = __o.givenName
        self.familyName = __o.familyName
        self.about = __o.about
        self.emoji = __o.emoji
        self.coinAddress = __o.coinAddress
        self.lastUpdate = __o.lastUpdate
        if (self._isAccountProfile == True):
            self.__save__()
        return

###############################
# Setters:
###############################
    def setGivenName(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.givenName == value):
            return False
    # Create set given name object and json command string:
        setGivenNameObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "givenName": value,
            }
        }
        jsonCommandStr = json.dumps(setGivenNameObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
        # print(responseObj)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting given name. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.givenName = value
        return True

    def setFamilyName(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.familyName == value):
            return False
    # Create command object and json command string:
        setFamilyNameCommandObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "familyName": value,
            }
        }
        jsonCommandStr = json.dumps(setFamilyNameCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting family name. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.familyName = value
        return True
    
    def setAbout(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.about == value):
            return False
    # Create command object and json command string:
        setAboutCommandObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "about": value,
            }
        }
        jsonCommandStr = json.dumps(setAboutCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting about. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.about = value
        return True

    def setEmoji(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.emoji == value):
            return False
    # Create command object and json command string:
        setEmojiCommandObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "aboutEmoji": value,
            }
        }
        jsonCommandStr = json.dumps(setEmojiCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting emoji. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.emoji = value
        return True

    def setCoinAddress(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.coinAddress == value):
            return False
    # Create command object and json command string:
        setCoinAddressCommandObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "mobileCoinAddress": value,
            }
        }
        jsonCommandStr = json.dumps(setCoinAddressCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting coin address. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.coinAddress = value
        return True
    
    def setAvatar(self, value:str) -> bool:
        if (isinstance(value, str) == False):
            __typeError__("value", "str", value)
        if (self._isAccountProfile == False):
            return False
        if (self.avatar == value):
            return False
    # Create command object and json command string:
        setAvatarCommandObj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._accountId,
                "avatar": value,
            }
        }
        jsonCommandStr = json.dumps(setAvatarCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while setting avatar. Code: %i Message: %s" % (
                                                                                            responseObj['error']['code'],
                                                                                            responseObj['error']['message']
                                                                                        )
                print(errorMessage, file=sys.stderr)
            return False
    # Set the property
        self.avatar = value
        return True
