#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __socket_receive__, __socket_send__
from .signalContacts import Contacts
from .signalContact import Contact
from .signalTimestamp import Timestamp
global DEBUG
DEBUG: bool = True

Self = TypeVar("Self", bound="Group")

class Group(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    accountContacts: Contacts,
                    fromDict: Optional[dict] = None,
                    rawGroup: Optional[dict] = None,
                    id: Optional[str] = None,
                    name: Optional[str] = None,
                    description: Optional[str] = None,
                    isBlocked: Optional[bool] = False,
                    isMember: Optional[bool] = False,
                    expiration: Optional[int] = None,
                    link: Optional[str] = None,
                    members: Optional[list[Contact]] = [],
                    pendingMembers: Optional[list[Contact]] = [],
                    requestingMembers: Optional[list[Contact]] = [],
                    admins: Optional[list[Contact]] = [],
                    banned: Optional[list[Contact]] = [],
                    permissionAddMember: Optional[str] = None,
                    permissionEditDetails: Optional[str] = None,
                    permissionSendMessage: Optional[str] = None,
                    lastSeen: Optional[Timestamp] = None,
                ) -> None:
    # TODO: Argument checks
    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._configPath: str = configPath
        self._accountId: str = accountId
        self._contacts: Contacts = accountContacts
        self._isValid: bool = True
    # Set external properties:
        self.id : str = id
        self.name: Optional[str] = name
        self.description : Optional[str] = description
        self.isBlocked: bool = isBlocked
        self.isMember: bool = isMember
        self.expiration: Optional[int] = expiration
        self.link: Optional[str] = link
        self.members: list[Contact] = members
        self.pending: list[Contact] = pendingMembers
        self.requesting: list[Contact] = requestingMembers
        self.admins: list[Contact] = admins
        self.banned: list[Contact] = banned
        self.permissionAddMember: str = permissionAddMember
        self.permissionEditDetails: str = permissionEditDetails
        self.permissionSendMessage: str = permissionSendMessage
        # self.last_seen: Optional[Timestamp] = last_seen
    # Parse from_dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse rawGroup:
        elif (rawGroup != None):
            self.__fromRawGroup__(rawGroup)
    # Group object was created without rawGroup or from_dict, see if we can get details from signal:
        else:
            if (self.id != None):
                self._isValid = self.__sync__()
            else:
                self._isValid = False
        return

#################
# Init:
#################

    def __fromRawGroup__(self, rawGroup:dict) -> None:
        # print(rawGroup)
        self.id = rawGroup['id']
        if (rawGroup['name'] == ''):
            self.name = None
        else:
            self.name = rawGroup['name']
        if (rawGroup['description'] == ''):
            self.description = None
        else:
            self.description = rawGroup['description']
        self.isBlocked = rawGroup['is_blocked']
        self.isMember = rawGroup['isMember']
        if (rawGroup['messageExpirationTime'] == 0):
            self.expiration = None
        else:
            self.expiration = rawGroup['messageExpirationTime']
        self.link = rawGroup['groupInviteLink']
        self.permissionAddMember = rawGroup['permissionAddMember']
        self.permissionEditDetails = rawGroup['permissionEditDetails']
        self.permissionSendMessage = rawGroup['permissionSendMessage']
    # Parse members:
        self.members = []
        for contactDict in rawGroup['members']:
            added, contact = self._contacts.__getOrAdd__(
                                                            "<UNKNOWN-CONTACT>",
                                                            number=contactDict['number'],
                                                            uuid=contactDict['uuid']
                                                        )
            self.members.append(contact)
    # Parse pending:
        self.pending = []
        for contactDict in rawGroup['pendingMembers']:
            added, contact = self._contacts.__getOrAdd__(
                                                            "<UNKNOWN-CONTACT>",
                                                            number=contactDict['number'],
                                                            uuid=contactDict['uuid']
                                                        )
            self.pending.append(contact)
    # Parse requesting:
        self.requesting = []
        for contactDict in rawGroup['requestingMembers']:
            added, contact = self._contacts.__getOrAdd__(
                                                            "<UNKNOWN-CONTACT>",
                                                            number=contactDict['number'],
                                                            uuid=contactDict['uuid']
                                                        )
            self.requesting.append(contact)
    # Parse admins:
        self.admins = []
        for contactDict in rawGroup['admins']:
            added, contact = self._contacts.__getOrAdd__(
                                                            "<UNKNOWN-CONTACT>",
                                                            number=contactDict['number'],
                                                            uuid=contactDict['uuid']
                                                        )
            self.admins.append(contact)
    # Parse banned:
        self.banned = []
        for contactDict in rawGroup['banned']:
            added, contact = self._contacts.__getOrAdd__(
                                                            "<UNKNOWN-CONTACT>",
                                                            number=contactDict['number'],
                                                            uuid=contactDict['uuid']
                                                        )
            self.banned.append(contact)
        return

######################
# Overrides:
######################
    def __eq__(self, __o: Self) -> bool:
        if (isinstance(__o, Group) == True):
            if (self.id == __o.id):
                return True
        return False
###################################
# To / From Dict:
###################################
    def __toDict__(self) -> dict:
        groupDict = {
            'id' : self.id,
            'name': self.name,
            'description': self.description,
            'is_blocked': self.isBlocked,
            'isMember': self.isMember,
            'expiration': self.expiration,
            'link': self.link,
            'permAddMember': self.permissionAddMember,
            'permEditDetails': self.permissionEditDetails,
            'permSendMessage': self.permissionSendMessage,
            'members': [],
            'pending': [],
            'requesting': [],
            'admins': [],
            'banned': [],
        }
        for contact in self.members:
            groupDict['members'].append(contact.get_id())
        for contact in self.pending:
            groupDict['pending'].append(contact.get_id())
        for contact in self.requesting:
            groupDict['requesting'].append(contact.get_id())
        for contact in self.admins:
            groupDict['admins'].append(contact.get_id())
        for contact in self.banned:
            groupDict['banned'].append(contact.get_id())
        return groupDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        self.id = fromDict['id']
        self.name = fromDict['name']
        self.description = fromDict['description']
        self.isBlocked = fromDict['is_blocked']
        self.isMember = fromDict['isMember']
        self.expiration = fromDict['expiration']
        self.link = fromDict['link']
        self.permissionAddMember = fromDict['permAddMember']
        self.permissionEditDetails = fromDict['permEditDetails']
        self.permissionSendMessage = fromDict['permSendMessage']
    # Parse members:
        self.members = []
        for contactId in fromDict['members']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=contactId)
            self.members.append(contact)
    # Parse Pending:
        self.pending = []
        for contactId in fromDict['pending']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=contactId)
            self.pending.append(contact)
    # Parse requesting:
        self.requesting = []
        for contactId in fromDict['requesting']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=contactId)
            self.requesting.append(contact)
    # Parse admins:
        self.admins = []
        for contactId in fromDict['admins']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=contactId)
            self.admins.append(contact)
    # Parse banned:
        self.banned = []
        for contactId in fromDict['banned']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=contactId)
            self.banned.append(contact)
        return

#################
# Helpers:
#################

    def __merge__(self, __o:Self) -> None:
        self.name = __o.name
        self.description = __o.description
        self.isBlocked = __o.isBlocked
        self.isMember = __o.isMember
        self.expiration = __o.expiration
        self.link = __o.link
        self.permissionAddMember = __o.permissionAddMember
        self.permissionEditDetails = __o.permissionEditDetails
        self.permissionSendMessage = __o.permissionSendMessage
        self.members = __o.members
        self.pending = __o.pending
        self.requesting = __o.requesting
        self.admins = __o.admins
        self.banned = __o.banned
        return
########################
# Sync:
########################
    def __sync__(self) -> bool:
    # Create command object and json command string:
        listGroupCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listGroups",
            "params": {
                "account": self._accountId,
                "groupId": self.id,
            }
        }
        jsonCommandStr = json.dumps(listGroupCommandObj) + '\n'
    # Communicate with signal:
        __socket_send__(self._syncSocket, jsonCommandStr)
        responseStr = __socket_receive__(self._syncSocket)
    # Parse response:
        responseObj: dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage= "signal error during group __sync__: code: %i message: %s" % (responseObj['error']['code'],
                                                                                            responseObj['error']['message'])
                print(errorMessage, file=sys.stderr)
            return False
        rawGroup = responseObj['result'][0]
        self.__fromRawGroup__(rawGroup)
        return True

########################################
# Getters:
######################################
    def getId(self) -> str:
        return self.id
    
    def getDisplayName(self, maxLen:Optional[int]=None) -> str:
        if (maxLen != None and maxLen <= 0):
            raise ValueError("maxLen must be greater than zero")
        displayName = ''
        if (self.name != None and self.name != '' and self.name != '<UNKNOWN-GROUP>'):
            displayName = self.name
        else:
            for contact in self.members:
                displayName = displayName + contact.get_display_name() + ', '
            displayName = displayName[:-2]
        if (maxLen != None and len(displayName) > maxLen):
                displayName = displayName[:maxLen]
        return displayName
