#! /usr/bin/env python3

from typing import Optional, Iterator
import socket
import json

from .signalCommon import __socket_receive__, __socket_send__
from .signalGroup import Group
from .signalContacts import Contacts
# from signalSyncMessage import SyncMessage

global DEBUG
DEBUG: bool = True

class Groups(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    accountContacts: Contacts,
                    fromDict: Optional[dict] = None,
                    doSync: bool = False
                ) -> None:
    # TODO: Arg checks:
    # Set internal vars:
        self._syncSocket : socket.socket = syncSocket
        self._configPath: str = configPath
        self._accountId: str = accountId
        self._contacts: Contacts = accountContacts
        self._groups: list[Group] = []
    # Load from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Load from signal
        if (doSync == True):
            self.__sync__()

        return
############################
# Overrides:
############################
    def __iter__(self) -> Iterator[Group]:
        return iter(self._groups)

############################
# To / From Dict:
############################
    def __toDict__(self) -> dict[str, object]:
        groupsDict = {
            "groups": []
        }
        for group in self._groups:
            groupsDict["groups"].append(group.__toDict__())
        return groupsDict
    
    def __fromDict__(self, fromDict:dict):
        self._groups = []
        for groupDict in fromDict['groups']:
            group = Group(syncSocket=self._syncSocket, configPath=self._configPath, accountId= self._accountId,
                            accountContacts=self._contacts, fromDict=groupDict)
            self._groups.append(group)
        return

###################################
# Sync with signal:
##################################
    def __sync__(self) -> bool:
    # Create command object and json command string:
        listGroupsCommandObj = {
            "jsonrpc": "2.0",
            "contact_id":0,
            "method": "listGroups",
            "params": {
                "account": self._accountId,
            }
        }
        jsonCommandStr = json.dumps(listGroupsCommandObj) + '\n'
    # Communicate with signal:
        __socket_send__(self._syncSocket, jsonCommandStr)
        responseString = __socket_receive__(self._syncSocket)
    # Parse response:
        responseObj: dict = json.loads(responseString)
        # print(responseObj)
    # Check for error:
        if ('error' in responseObj.keys()):
            return False
    # Parse result:
        groupAdded = False
        for rawGroup in responseObj['result']:
            newGroup = Group(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                            accountContacts=self._contacts, rawGroup=rawGroup)
            oldGroup = self.getById(newGroup.id)
            if (oldGroup == None):
                self._groups.append(newGroup)
                groupAdded = True
            else:
                oldGroup.__merge__(newGroup)
            
        return groupAdded
##############################
# Helpers:
##############################
    def __parseSyncMessage__(self, syncMessage) -> None: # sync_message type SyncMessage
        if (syncMessage.syncType == 5): # SyncMessage.TYPE_BLOCKED_SYNC
            for groupId in syncMessage.blockedGroups:
                added, group = self.__getOrAdd__("<UNKNOWN-GROUP>", groupId)
                group.isBlocked = True
        else:
            errorMessage = "groups can only parse sync message of type: SyncMessage.TYPE_BLOCKED_SYNC."
            raise TypeError(errorMessage)
##############################
# Getters:
##############################
    def getById(self, id:str) -> Optional[Group]:
        for group in self._groups:
            if (group.id == id):
                return group
        return None
    
    def getByName(self, name:str) -> Optional[Group]:
        for group in self._groups:
            if (group.name == name):
                return group
        return None
####################################
# Helpers:
###################################
    def __getOrAdd__(self, name:str, id:str) -> tuple[bool, Group]:
        # self.__sync__()
        oldGroup = self.getById(id)
        if (oldGroup != None):
            return (False, oldGroup)
        newGroup = Group(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                        accountContacts=self._contacts, name=name, id=id)
        self._groups.append(newGroup)
        return (True, newGroup)