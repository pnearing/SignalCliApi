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
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 stickerPacks: StickerPacks,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 is_delivered: bool = False,
                 time_delivered: Optional[Timestamp] = None,
                 is_read: bool = False,
                 time_read: Optional[Timestamp] = None,
                 is_viewed: bool = False,
                 time_viewed: Optional[Timestamp] = None,
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
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_SYNC_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
# Mark viewed delivered and read:
        super().mark_delivered(self.timestamp)
        super().mark_read(self.timestamp)
        super().mark_viewed(self.timestamp)
        return

######################
# Init:
######################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        # print("DEBUG: %s" % __name__)
        rawSyncMessage: dict[str, object] = raw_message['sync_message']
    ######## Read messages #########
        if ('readMessages' in rawSyncMessage.keys()):
            # print(rawSyncMessage['readMessages'])
            self.syncType = self.TYPE_READ_MESSAGE_SYNC
            readMessageList: list[dict[str, object]] = rawSyncMessage['readMessages']
            self.readMessages: list[tuple[Contact, Timestamp]] = []
            for readMessageDict in readMessageList:
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", readMessageDict['sender'])
                timestamp = Timestamp(timestamp=readMessageDict['timestamp'])
                self.readMessages.append( (contact, timestamp) )
    ######### Sent message ########
        elif ('sentMessage' in rawSyncMessage.keys()):
            print(rawSyncMessage['sentMessage'])
            self.syncType = self.TYPE_SENT_MESSAGE_SYNC
            self.rawSentMessage = raw_message
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
    def __to_dict__(self) -> dict:
        syncMessageDict = super().__to_dict__()
# Store sync type:
        syncMessageDict['syncType'] = self.syncType
# Store sent message properties:
        syncMessageDict['rawSentMessage'] = self.rawSentMessage
# Store the read messages list:
    # Store the list as a list of tuples[contactID:str, timestampDict:dict]
        syncMessageDict['readMessages'] = []
        for (contact, timestamp) in self.readMessages:
            targetMessageTuple = (contact.get_id(), timestamp.__to_dict__())
            syncMessageDict['readMessages'].append(targetMessageTuple)
# Store Blocked contacts and groups lists:
        syncMessageDict['blockedContacts'] = self.blockedContacts
        syncMessageDict['blockedGroups'] = self.blockedGroups
        return syncMessageDict
    
    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
    # Load sync type:
        self.syncType = from_dict['syncType']
# Load sent message properties:
        self.rawSentMessage = from_dict['rawSentMessage']
# Set read messages list:
    # Load read messages:
        self.readMessages = []
        for (contactId, timestampDict) in from_dict['readMessages']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)
            timestamp = Timestamp(fromDict=timestampDict)
            self.readMessages.append( (contact, timestamp) )
# Set blocked groups and contacts:
        self.blockedContacts = from_dict['blockedContacts']
        self.blockedGroups = from_dict['blockedGroups']

        return