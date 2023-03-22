#!/usr/bin/env python3

from typing import Optional
import socket
import sys

from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalSticker import StickerPacks
from .signalTimestamp import Timestamp

global DEBUG
DEBUG: bool = True

class SyncMessage(Message):
# Sync message types:
    TYPE_CONTACT_SYNC: int = 1
    TYPE_GROUPS_SYNC: int = 2
    TYPE_SENT_MESSAGE_SYNC: int = 3
    TYPE_READ_MESSAGE_SYNC: int = 4
    TYPE_BLOCKED_SYNC: int = 5
# Sent message mesage types:
    SENT_TYPE_SENT_MESSAGE: int = 1
    SENT_TYPE_GROUP_UPDATE_MESSAGE: int = 2
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId: str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    stickerPacks: StickerPacks,
                    fromDict: Optional[dict] = None,
                    rawMessage: Optional[dict] = None,
                    sender: Optional[Contact] = None,
                    recipient: Optional[Contact | Group] = None,
                    device: Optional[Device] = None,
                    timestamp: Optional[Timestamp] = None,
                    isDelivered: bool = False,
                    timeDelivered: Optional[Timestamp] = None,
                    isRead: bool = False,
                    timeRead: Optional[Timestamp] = None,
                    isViewed: bool = False,
                    timeViewed: Optional[Timestamp] = None,
                    syncType: int = Message.TYPE_NOT_SET,
                ) -> None:
# TODO: Argument checks:
# Set internal properties:
    # Set sticker packs:
        self._stickerPacks: StickerPacks = stickerPacks
# Set external properties:
    # Set sync type:
        self.syncType: int = syncType
    # Set sent message properties:
        self.rawSentMessage: Optional[dict[str,object]] = None
    # Set read messages list:
        self.readMessages: list[tuple[Contact, Timestamp]] = []
    # Set blocked Contacts and group lists:
        self.blockedContacts: list[str] = []
        self.blockedGroups: list[str] = []
# Run super Init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, sender, recipient, device, timestamp, Message.TYPE_SYNC_MESSAGE, isDelivered,
                            timeDelivered, isRead, timeRead, isViewed, timeViewed)
# Mark viewed delivered and read:
        super().markDelivered(self.timestamp)
        super().markRead(self.timestamp)
        super().markViewed(self.timestamp)
        return

######################
# Init:
######################
    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        # print("DEBUG: %s" % __name__)
        rawSyncMessage: dict[str, object] = rawMessage['syncMessage']
    ######## Read messages #########
        if ('readMessages' in rawSyncMessage.keys()):
            # print(rawSyncMessage['readMessages'])
            self.syncType = self.TYPE_READ_MESSAGE_SYNC
            readMessageList: list[dict[str, object]] = rawSyncMessage['readMessages']
            self.readMessages: list[tuple[Contact, Timestamp]] = []
            for readMessageDict in readMessageList:
                added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", readMessageDict['sender'])
                timestamp = Timestamp(timestamp=readMessageDict['timestamp'])
                self.readMessages.append( (contact, timestamp) )
    ######### Sent message ########
        elif ('sentMessage' in rawSyncMessage.keys()):
            print(rawSyncMessage['sentMessage'])
            self.syncType = self.TYPE_SENT_MESSAGE_SYNC
            self.rawSentMessage = rawMessage
    ########## Blocked Numbers / Groups #############
        elif ('blockedNumbers' in rawSyncMessage.keys()):
            self.syncType = self.TYPE_BLOCKED_SYNC
            self.blockedContacts = []
            for contactId in rawSyncMessage['blockedNumbers']:
                self.blockedContacts.append(contactId)
            self.blockedGroups = []
            for groupId in rawSyncMessage['blockedGroupIds']:
                self.blockedGroups.append(groupId)
        elif ('type' in rawSyncMessage.keys()):
    ########### Group sync #################
            if (rawSyncMessage['type'] == "GROUPS_SYNC"):
                self.syncType = self.TYPE_GROUPS_SYNC
                # print("Groups sync message")
    ########### Contacts Sync ###############
            elif (rawSyncMessage['type'] == "CONTACTS_SYNC"):
                self.syncType = self.TYPE_CONTACT_SYNC
                # print("Contacts sync message")
            else:
                if (DEBUG == True):
                    debugMessage = "Unrecognized type: %s OBJ: %s" % (rawSyncMessage['type'], str(rawSyncMessage))
                    print(debugMessage, file=sys.stderr)
        return 
    
###########################
# To / From Dict:
###########################
    def __toDict__(self) -> dict:
        syncMessageDict = super().__toDict__()
# Store sync type:
        syncMessageDict['syncType'] = self.syncType
# Store sent message properties:
        syncMessageDict['rawSentMessage'] = self.rawSentMessage
# Store the read messages list:
    # Store the list as a list of tuples[contactID:str, timestampDict:dict]
        syncMessageDict['readMessages'] = []
        for (contact, timestamp) in self.readMessages:
            targetMessageTuple = ( contact.getId(), timestamp.__toDict__() )
            syncMessageDict['readMessages'].append(targetMessageTuple)
# Store Blocked contacts and groups lists:
        syncMessageDict['blockedContacts'] = self.blockedContacts
        syncMessageDict['blockedGroups'] = self.blockedGroups
        return syncMessageDict
    
    def __fromDict__(self, fromDict: dict) -> None:
        super().__fromDict__(fromDict)
    # Load sync type:
        self.syncType = fromDict['syncType']
# Load sent message properties:
        self.rawSentMessage = fromDict['rawSentMessage']
# Set read messages list:
    # Load read messages:
        self.readMessages = []
        for (contactId, timestampDict) in fromDict['readMessages']:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", contactId)
            timestamp = Timestamp(fromDict=timestampDict)
            self.readMessages.append( (contact, timestamp) )
# Set blocked groups and contacts:
        self.blockedContacts = fromDict['blockedContacts']
        self.blockedGroups = fromDict['blockedGroups']

        return