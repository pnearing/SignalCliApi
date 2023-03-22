#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __typeError__, __socketReceive__, __socketSend__
from .signalProfile import Profile
from .signalTimestamp import Timestamp
from .signalDevices import Devices

Self = TypeVar("Self", bound="Contact")

global DEBUG
DEBUG = True

class Contact(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    accountPath: str,
                    fromDict: Optional[dict] = None,
                    rawContact: Optional[dict] = None,
                    name: Optional[str] = None,
                    number: Optional[str] = None,
                    uuid: Optional[str] = None,
                    profile: Optional[Profile] = None,
                    devices: Optional[Devices] = None,
                    isBlocked: Optional[bool] = None,
                    expiration: Optional[int] = None,
                    isTyping: Optional[bool] = None,
                    lastTypingChange: Optional[Timestamp] = None,
                    lastSeen: Optional[Timestamp] = None,
                    color:Optional[str] = None,
                ) -> None:
    # TODO: Argument checks:
    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._configPath: str = configPath
        self._accountPath: str = accountPath
        self._accountId: str = accountId
    # Set external properties:
        self.name: Optional[str] = name
        self.number: Optional[str] = number
        self.uuid: Optional[str] = uuid
        self.profile: Optional[Profile] = profile
        self.devices: Devices = devices
        self.isBlocked: bool = isBlocked
        self.expiration: Optional[int] = expiration
        self.isTyping: Optional[bool] = isTyping
        self.lastTypingChange: Optional[Timestamp] = lastTypingChange
        self.lastSeen: Optional[Timestamp] = lastSeen
        self.color: Optional[str] = color
        self.isSelf: bool = False
    # Parse from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
        elif (rawContact != None):
            self.__fromRawContact__(rawContact)
    # Mark as self:
        if (self.number == self._accountId):
            self.isSelf = True
            self.name = "Note-To-Self"
    # Catch unknown contact:
        if (self.name == "<UNKNOWN-CONTACT>"):
            if (self.profile != None):
                self.setName(self.profile.name)
                self.name = self.profile.name # Force the name for this session if setting failed.
    # If devices isn't yet set create empty devices:
        if (self.devices == None):
            self.devices = Devices(syncSocket=self._syncSocket, accountId=self.number)

        return

##################
# Init:
##################
    def __fromRawContact__(self,rawContact:dict) -> None:
        # print(rawContact)
        if (rawContact['name'] == ''):
            self.name = None
        else:
            self.name = rawContact['name']
        self.number = rawContact['number']
        self.uuid = rawContact['uuid']
        self.isBlocked = rawContact['isBlocked']
        self.color = rawContact['color']
        if (rawContact['messageExpirationTime'] == 0):
            self.expiration = None
        else:
            self.expiration = rawContact['messageExpirationTime']
        self.profile = Profile(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                    contactId=self.getId(), rawProfile=rawContact['profile'])
        return

##########################
# Overrides:
##########################
    def __eq__(self, __o: Self) -> bool:
        if (isinstance(__o, Contact) == True):
            if (self.number != None and __o.number != None):
                if (self.number == __o.number):
                    return True
            elif (self.uuid != None and __o.uuid != None):
                if (self.uuid == __o.uuid):
                    return True
        return False

#########################
# To / From Dict:
#########################
    def __toDict__(self) -> dict:
        contactDict = {
            'name': self.name,
            'number': self.number,
            'uuid': self.uuid,
            'profile': None,
            'devices': None,
            'isBlocked': self.isBlocked,
            'expiration': self.expiration,
            'isTyping': False,
            'lastTypingChange': None,
            'lastSeen': None,
            'color': self.color,
        }
        if (self.profile != None):
            contactDict['profile'] = self.profile.__toDict__()
        if (self.devices != None):
            contactDict['devices'] = self.devices.__toDict__()
        if (self.lastTypingChange != None):
            contactDict['lastTypingChange'] = self.lastTypingChange.__toDict__()
        if (self.lastSeen != None):
            contactDict['lastSeen'] = self.lastSeen.__toDict__()
        return contactDict

    def __fromDict__(self, fromDict:dict) -> None:
        self.name = fromDict['name']
        self.number = fromDict['number']
        self.uuid = fromDict['uuid']
        self.isBlocked = fromDict['isBlocked']
        self.isTyping = fromDict['isTyping']
        self.expiration = fromDict['expiration']
        self.color = fromDict['color']
    # Load Profile:
        if (fromDict['profile'] != None):
            if (self.number == self._accountId):
                self.profile = Profile(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                        contactId=self.getId(), fromDict=fromDict['profile'])
            else:
                self.profile = Profile(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                    contactId=self.getId(), fromDict=fromDict['profile'])
        else:
            self.profile = None
    # Load Devices:
        if (fromDict['devices'] != None):
            self.devices = Devices(syncSocket=self._syncSocket, accountId=self._accountId, fromDict=fromDict['devices'])
        else:
            self.devices = None
    # Load last typing change:
        if (fromDict['lastTypingChange'] != None):
            self.lastTypingChange = Timestamp(fromDict=fromDict['lastTypingChange'])
        else:
            self.lastTypingChange = None
    # Load last seen:
        if (fromDict['lastSeen'] != None):
            self.lastSeen = Timestamp(fromDict=fromDict['lastSeen'])
        else:
            self.lastSeen = None
        return

########################
# Getters:
########################
    def getId(self) -> str:
        if (self.number != None):
            return self.number
        return self.uuid
    
    def getDisplayName(self) -> str:
        if (self.isSelf == True):
            if (self.profile != None and self.profile.name != ''):
                return self.profile.name
            else:
                return self.name
        if (self.name != None and self.name != '' and self.name != "<UNKNOWN-CONTACT>"):
            return self.name
        elif (self.profile != None and self.profile.name != ''):
            return self.profile.name
        else:
            return "<UNKNOWN-CONTACT>"

###########################
# Setters:
##########################
    def setName(self, name:str) -> bool:
    # If name hasn't changed return false:
        if (self.name == name):
            return False
    # create command object and json command string:
        setNameCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "updateContact",
            "params":{
                "account": self._accountId,
                "recipient": self.getId(),
                "name": name,
            }
        }
        jsonCommandStr = json.dumps(setNameCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj: dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "Signal error while setting name: code %i, message: %s" % (responseObj['error']['code'],
                                                                                        responseObj['error']['message'])
                print(errorMessage, file=sys.stderr)
            return False
    # All is good set name.
        self.name = name
        return True


#########################
# Helpers:
#########################
    def __merge__(self, __o:Self) -> None:
        self.name = __o.name
        self.isBlocked = __o.isBlocked
        self.expiration = __o.expiration
        if (self.profile != None and __o.profile != None):
            self.profile.__merge__(__o.profile)
        elif (self.profile == None and __o.profile != None):
            self.profile = __o.profile
        return

############################
# Methods:
############################
    def seen(self, timeSeen:Timestamp) -> None:
        if (isinstance(timeSeen, Timestamp) == False):
            __typeError__('timeSeen', 'Timestamp', timeSeen)
        if (self.lastSeen != None):
            if (self.lastSeen < timeSeen):
                self.lastSeen = timeSeen
        else:
            self.lastSeen = timeSeen
        return
