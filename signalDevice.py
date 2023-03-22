#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket

from .signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Device")

class Device(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    accountId: str,
                    accountDevice: Optional[int] = None,
                    rawDevice: Optional[dict] = None,
                    fromDict: Optional[dict] = None,
                    id: Optional[int] = None,
                    name: Optional[str] = None,
                    created: Optional[Timestamp] = None,
                    lastSeen: Optional[Timestamp] = None,
                    isAccountDevice: Optional[bool] = None,
                    isPrimaryDevice: Optional[bool] = None,
                ) -> None:
    # TODO: Argument checks
    # Set internal vars:    
        self._syncSocket: socket.socket = syncSocket
        self._accountId: str = accountId
    # Set external properties:
        self.id: int = id
        self.name: Optional[str] = name
        self.created: Optional[Timestamp] = created
        self.lastSeen: Optional[Timestamp] = lastSeen
        self.isAccountDevice: Optional[bool] = isAccountDevice
        self.isPrimaryDevice: Optional[bool] = isPrimaryDevice
    # Parse Raw device:
        if (rawDevice != None):
            self.__fromRawDevice__(rawDevice)
            if (self.id == accountDevice): self.isAccountDevice = True
            if (self.id == 1): self.isPrimaryDevice = True
    # Parse from dict:
        elif (fromDict != None):
            self.__fromDict__(fromDict)
    # Otherwise assume all values have been specified.
        else:
            if (self.id != None and accountDevice != None and self.id == accountDevice): self.isAccountDevice = True
            if (self.id != None and self.id == 1): self.isPrimaryDevice = True
        return

    def __fromRawDevice__(self, rawDevice:dict) -> None:
        # print(rawDevice)
        self.id = rawDevice['id']
        self.name = rawDevice['name']
        if (rawDevice['createdTimestamp'] != None):
            self.created = Timestamp(timestamp=rawDevice['createdTimestamp'])
        else:
            self.created = None
        if (rawDevice['lastSeenTimestamp'] != None):
            self.lastSeen = Timestamp(timestamp=rawDevice['lastSeenTimestamp'])
        else:
            self.lastSeen = None
        return

    def __merge__(self, __o:Self) -> None:
        if (self.name == None):
            self.name = __o.name
        if (self.created != __o.created):
            self.created = __o.created
        if (self.lastSeen != None and __o.lastSeen != None):
            if (self.lastSeen < __o.lastSeen):
                self.lastSeen = __o.lastSeen
            elif (self.lastSeen == None and __o.lastSeen != None):
                self.lastSeen = __o.lastSeen
        return
##########################
# To / From dict:
##########################
    def __toDict__(self) -> dict:
        deviceDict = {
            'id': self.id,
            'name': self.name,
            'created': None,
            'lastSeen': None,
            'isAccountDevice': self.isAccountDevice,
            'isPrimaryDevice': self.isPrimaryDevice,
        }
        if (self.created != None):
            deviceDict['created'] = self.created.__toDict__()
        if (self.lastSeen != None):
            deviceDict['lastSeen'] = self.lastSeen.__toDict__()
        return deviceDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        self.id = fromDict['id']
        self.name = fromDict['name']
        if (fromDict['created'] != None):
            self.created = Timestamp(fromDict=fromDict['created'])
        else:
            self.created = None
        if (fromDict['lastSeen'] != None):
            self.lastSeen = Timestamp(fromDict=fromDict['lastSeen'])
        else:
            self.lastSeen = None
        self.isAccountDevice = fromDict['isAccountDevice']
        self.isPrimaryDevice = fromDict['isPrimaryDevice']
        return

########################
# Methods:
########################
    def seen(self, timeSeen:Timestamp) -> None:
        if (self.lastSeen != None):
            if (self.lastSeen < timeSeen):
                self.lastSeen = timeSeen
        else:
            self.lastSeen = timeSeen
        return
    
    def getDisplayName(self):
        returnStr = "%i<%s>" % (self.id, self.name)