#!/usr/bin/env python3

from typing import Optional
import socket
import sys
from datetime import timedelta

from signalAttachment import Attachment
from signalContact import Contact
from signalContacts import Contacts
from signalDevice import Device
from signalDevices import Devices
from signalGroup import Group
from signalGroups import Groups
from signalMentions import Mentions
from signalMessage import Message
from signalPreview import Preview
from signalSticker import Sticker, StickerPacks
from signalTimestamp import Timestamp

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
        self.sentMessageType: Optional[int] = None
        self.sentRecipient: Optional[Contact|Group] = None
        self.sentTimestamp: Optional[Timestamp] = None
        self.sentBody: Optional[str] = None
        self.sentExpiry: Optional[timedelta] = None
        self.sentMentions: Optional[Mentions] = None
        self.sentAttachments: Optional[list[Attachment]] = None
        self.sentPreview: Optional[Preview] = None
        self.sentSticker: Optional[Sticker] = None
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
            sentMessageDict: dict[str, object] = rawSyncMessage['sentMessage']
        # Set sync type:
            self.syncType = self.TYPE_SENT_MESSAGE_SYNC
        # Set sent message type:
            if ('groupInfo' in sentMessageDict.keys() and sentMessageDict['groupInfo']['type'] == 'UPDATE'):
                self.sentMessageType = self.SENT_TYPE_GROUP_UPDATE_MESSAGE
            else:
                self.sentMessageType = self.SENT_TYPE_SENT_MESSAGE
        # Set recipient:
            if ('groupInfo' in sentMessageDict.keys()):
                added, self.sentRecipient = self._groups.__getOrAdd__("<UNKNOWN-GROUP>", sentMessageDict['groupInfo']['groupId'])
            else:
                added, self.sentRecipient = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", sentMessageDict['destination'])
        # Set Mentions:
            if ('mentions' in sentMessageDict.keys()):
                self.sentMentions = Mentions(contacts=self._contacts, rawMentions=sentMessageDict['mentions'])
        # Set Attachments:
            if ('attachments' in sentMessageDict.keys()):
                self.sentAttachments = []
                for rawAttachment in sentMessageDict['attachments']:
                    self.sentAttachments.append(Attachment(configPath=self._configPath, rawAttachment=rawAttachment))
        # Set preview:
            if ('previews' in sentMessageDict.keys()):
                rawPreview = sentMessageDict['previews'][0]
                preview = Preview(configPath=self._configPath, rawPreview=rawPreview)
                self.sentPreview = preview
        # Set sticker:
            if ('sticker' in sentMessageDict.keys()):
                self.sentSticker = self._stickerPacks.getSticker(
                                                    packId=sentMessageDict['sticker']['packId'],
                                                    stickerId=sentMessageDict['sticker']['stickerId'],
                                                )
        # Set Timestamp:
            self.sentTimestamp = Timestamp(sentMessageDict['timestamp'])
        # Set body:
            self.sentBody = sentMessageDict['message']
        # Set expiry
            if ( sentMessageDict['expiresInSeconds'] == 0):
                self.sentExpiry = None
            else:
                self.sentExpiry = timedelta(seconds=sentMessageDict['expiresInSeconds'])
    ########## Blocked Numbers / Groups #############
        elif ('blockedNumbers' in rawSyncMessage.keys()):
            self.syncType = self.TYPE_BLOCKED_SYNC
            # print(rawSyncMessage['blockedNumbers'])
            # print(rawSyncMessage['blockedGroupIds'])
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
    # store sentMesageType:
        syncMessageDict['sentMessageType'] = self.sentMessageType
    # store receipient and recipient type:
        if (self.sentRecipient == None):
            syncMessageDict['sentRecipient'] = None
            syncMessageDict['sentRecipientType'] = None
        elif (isinstance(self.sentRecipient, Contact) == True):
            syncMessageDict['sentRecipient'] = self.sentRecipient.getId()
            syncMessageDict['sentRecipientType'] = 'contact'
        elif (isinstance(self.sentRecipient, Group) == True):
            syncMessageDict['sentRecipient'] = self.sentRecipient.getId()
            syncMessageDict['sentRecipientType'] = 'group'
    # Store sent timestamp:
        syncMessageDict['sentTimestamp'] = None
        if (self.sentTimestamp != None):
            syncMessageDict['sentTimestamp'] = self.sentTimestamp.__toDict__()
    # Store the body:
        syncMessageDict['sentBody'] = self.sentBody
    # Store the expiry:
        syncMessageDict['sentExpiry'] = None
        if (self.sentExpiry != None):
            syncMessageDict['sentExpiry'] = self.sentExpiry.seconds
    # Store the mentions:
        syncMessageDict['sentMentions'] = None
        if (self.sentMentions != None):
            syncMessageDict['sentMentions'] = self.sentMentions.__toDict__()
    # Store the attachments:
        syncMessageDict['sentAttachments'] = None
        if (self.sentAttachments != None):
            syncMessageDict['sentAttachments'] = []
            for attachment in self.sentAttachments:
                syncMessageDict['sentAttachments'].append(attachment.__toDict__())
    # Store the preview:
        syncMessageDict['sentPreview'] = None
        if (self.sentPreview != None):
            syncMessageDict['sentPreview'] = self.sentPreview.__toDict__()
    # Store the sticker:
        syncMessageDict['sentSticker'] = None
        if (self.sentSticker != None):
            syncMessageDict['sentSticker'] = {
                                                'packId': self.sentSticker._packId,
                                                'stickerId': self.sentSticker.id,
                                            }
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
    # Load sent message type:
        self.sentMessageType = fromDict['sentMessageType']
    # Load recipient:
        if (fromDict['sentRecipientType'] == 'contact'):
            added, self.sentRecipient = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", fromDict['sentRecipient'])
        elif (fromDict['sentRecipientType'] == 'group'):
            added, self.sentRecipient = self._groups.__getOrAdd__("<UNKOWN-GROUP>", fromDict['sentRecipient'])
    # Load sent timestamp:
        self.sentTimestamp = None
        if (fromDict['sentTimestamp'] != None):
            self.sentTimestamp = Timestamp(fromDict=fromDict['sentTimestamp'])
    # Load body:
        self.sentBody = fromDict['sentBody']
    # Load expiry:
        self.sentExpiry = None
        if (fromDict['sentExpiry'] != None):
            self.sentExpiry = timedelta(seconds=fromDict['sentExpiry'])
    # Load Mentions:
        self.sentMentions = None
        if (fromDict['sentMentions'] != None):
            self.sentMentions = Mentions(contacts=self._contacts, fromDict=fromDict['sentMentions'])
    # Load attachments:
        self.sentAttachments = None
        if (fromDict['sentAttachments'] != None):
            self.sentAttachments = []
            for attachmentDict in fromDict['sentAttachments']:
                self.sentAttachments.append(Attachment(configPath=self._configPath, fromDict=attachmentDict))
    # Load sticker:
        self.sentSticker = None
        if (fromDict['sentSticker'] != None):
            self.sentSticker = self._stickerPacks.getSticker(
                                                        packId=fromDict['sentSticker']['packId'],
                                                        stickerId=fromDict['sentAttachments']['stickerId'],
                                                    )
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