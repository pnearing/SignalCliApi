#!/usr/bin/env python3

from typing import TypeVar, Optional, Iterable
import socket
import json
import sys

from signalAttachment import Attachment
from signalCommon import __typeError__, __socketReceive__, __socketSend__
from signalContacts import Contacts
from signalContact import Contact
from signalDevices import Devices
from signalDevice import Device
from signalGroups import Groups
from signalGroup import Group
from signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Message")

global DEBUG
DEBUG: bool = True

class Message(object):
    TYPE_NOT_SET: int = 0
    TYPE_SENT_MESSAGE: int = 1
    TYPE_RECEIVED_MESSAGE: int = 2
    TYPE_TYPING_MESSAGE: int = 3
    TYPE_RECEIPT_MESSAGE: int = 4
    TYPE_STORY_MESSAGE: int = 5
    TYPE_PAYMENT_MESSAGE: int = 6
    TYPE_REACTION_MESSAGE: int = 7
    TYPE_GROUP_UPDATE_MESSAGE: int = 8
    TYPE_SYNC_MESSAGE: int = 9
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId:str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    fromDict: Optional[dict] = None,
                    rawMessage: Optional[dict] = None,
                    sender: Optional[Contact] = None,
                    recipient: Optional[Contact | Group] = None,
                    device: Optional[Device] = None,
                    timestamp: Optional[Timestamp] = None,
                    messageType: int = TYPE_NOT_SET,
                    isDelivered: bool = False,
                    timeDelivered: Optional[Timestamp] = None,
                    isRead: bool = False,
                    timeRead: Optional[Timestamp] = None,
                    isViewed: bool = False,
                    timeViewed: Optional[Timestamp] = None,
                ) -> None:
    # Arg Type Checks:
        if (isinstance(commandSocket, socket.socket) == False):
            __typeError__('commandSocket', 'socket', commandSocket)
        if (isinstance(accountId, str) == False):
            __typeError__('accountId', 'str', accountId)
        if (isinstance(configPath, str) == False):
            __typeError__('configPath', 'str', configPath)
        if (isinstance(contacts, Contacts) == False):
            __typeError__("contacts" "Contacts", contacts)
        if (isinstance(groups, Groups) == False):
            __typeError__("groups", "Groups", groups)
        if (isinstance(devices, Devices) == False):
            __typeError__("devices", "Devices", devices)
        if (isinstance(thisDevice, Device) == False):
            __typeError__("thisDevice", "Device", thisDevice)
        if (fromDict != None and isinstance(fromDict, dict) == False):
            __typeError__("fromDict", "dict", fromDict)
        if (rawMessage != None and isinstance(rawMessage, dict) == False):
            __typeError__("rawMessage", "dict", rawMessage)
        if (sender != None and isinstance(sender, Contact) == False):
            __typeError__("sender", "Contact", sender)
        if (recipient != None and isinstance(recipient, Contact) == False and isinstance(recipient, Group) == False):
            __typeError__("recipient", "Contact | Group", recipient)
        if (device != None and isinstance(device, Device) == False):
            __typeError__("device", "Device", device)
        if (timestamp != None and isinstance(timestamp, Timestamp) == False):
            __typeError__("timestamp", "Timestamp", timestamp)
        if (isinstance(messageType, int) == False):
            __typeError__("messageType", "int", messageType)
        if (isinstance(isDelivered, bool) == False):
            __typeError__("isDelivered", "bool", isDelivered)
        if (timeDelivered != None and isinstance(timeDelivered, Timestamp) == False):
            __typeError__("timeDelivered", "Timestamp", timeDelivered)
        if (isinstance(isRead, bool) == False):
            __typeError__("isRead", "bool", isRead)
        if (timeRead != None and isinstance(timeRead, Timestamp) == False):
            __typeError__("timeRead", "Timestamp", timeRead)
        if (isinstance(isViewed, bool) == False):
            __typeError__("isViewed", "bool", isViewed)
        if (timeViewed != None and isinstance(timeViewed, Timestamp) == False):
            __typeError__("timeViewed", "Timestamp", timeViewed)
    # Set internal vars:
        self._commandSocket: socket.socket = commandSocket
        self._accountId: str = accountId
        self._configPath: str = configPath
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Devices = devices
        self._thisDevice: Device = thisDevice
    # Set external properties:
        self.sender:Contact = sender
        self.recipient: Contact | Group = recipient
        self.recipientType: Optional[str] = None
        self.device:Device = device
        self.timestamp:Timestamp = timestamp
        self.messageType: int = messageType
        self.isDelivered: bool = isDelivered
        self.timeDelivered: Optional[Timestamp] = timeDelivered
        self.isRead: bool = isRead
        self.timeRead: Optional[Timestamp] = timeRead
        self.isViewed: bool = isViewed
        self.timeViewed: Optional[Timestamp] = timeViewed
    # Parse from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from raw Message:
        elif (rawMessage != None):
            self.__fromRawMessage__(rawMessage)
            self.sender.seen(self.timestamp)
            self.device.seen(self.timestamp)
            if (self.recipientType == 'contact'):
                self.recipient.seen(self.timestamp)
    # Set recipient type
        if (self.recipient != None):
            if (isinstance(self.recipient, Contact) == True):
                self.recipientType = 'contact'
            elif (isinstance(self.recipient, Group) == True):
                self.recipientType = 'group'
        return
#######################
# Init:
#######################
    def __fromRawMessage__(self, rawMessage:dict) -> None:
        print("Message.__fromRawMessage__")
    # Parse Sender
        added, self.sender = self._contacts.__getOrAdd__(rawMessage['sourceName'], rawMessage['source'])
        if (added == True):
            self._contacts.__save__()
    # Parse recipient:
        self.recipient = None
        if ('dataMessage' in rawMessage.keys()):
            dataMessage:dict[str, object] = rawMessage['dataMessage']
            if ('groupInfo' in dataMessage.keys()):
                added, self.recipient = self._groups.__getOrAdd__("<UNKNOWN-GROUP>", dataMessage['groupInfo']['groupId'])
                self.recipientType = 'group'
        if (self.recipient == None):
            self.recipient = self._contacts.getSelf()
            self.recipientType = 'contact'
    # Parse device:
        added, self.device = self.sender.devices.__getOrAdd__("<UNKNOWN-DEVICE>", rawMessage['sourceDevice'])
        if (added == True):
            self._contacts.__save__()
    # Parse Timestamp:
        self.timestamp = Timestamp(timestamp=rawMessage['timestamp'])
        return

#########################
# Overrides:
#########################
    def __eq__(self, __o: Self) -> bool:
        if (isinstance(__o, Message) == True):
        # Check sender:
            if (self.sender != __o.sender):
                return False
        # Check recipients:
            if (self.recipientType != __o.recipientType):
                return False
            if (self.recipient != __o.recipient):
                return False
        # Check Timestamp
            if (self.timestamp != __o.timestamp):
                return False
        # Check device:
            if (self.device != __o.device):
                return False
        # Check message type:
            if (self.messageType != __o.messageType):
                return False
        # Check Delivered (is and time):
            if (self.isDelivered != __o.isDelivered):
                return False
            if (self.timeDelivered != __o.timeDelivered):
                return False
        # Check Read (is and time):
            if (self.isRead != __o.isRead):
                return False
            if (self.timeRead != __o.timeRead):
                return False
        # Check Viewed (is and time):
            if (self.isViewed != __o.isViewed):
                return False
            if (self.timeViewed != __o.timeViewed):
                return False
        return False

##################################
# To / From dict:
##################################
    def __toDict__(self) -> dict:
        messageDict = {
            'sender': None,
            'recipient': None,
            'recipientType': self.recipientType,
            'device': None,
            'timestamp': None,
            'messageType': self.messageType,
            'isDelivered': self.isDelivered,
            'timeDelivered': None,
            'isRead': self.isRead,
            'timeRead': None,
            'isViewed': self.isViewed,
            'timeViewed': None,
        }
        if (self.sender != None):
            messageDict['sender'] = self.sender.getId()
        if (self.recipient != None):
            messageDict['recipient'] = self.recipient.getId()
        if (self.device != None):
            messageDict['device'] = self.device.id
        if (self.timestamp != None):
            messageDict['timestamp'] = self.timestamp.__toDict__()
        if (self.timeDelivered != None):
            messageDict['timeDelivered'] = self.timeDelivered.__toDict__()
        if (self.timeRead != None):
            messageDict['timeRead'] = self.timeRead.__toDict__()
        if (self.timeViewed != None):
            messageDict['timeViewed'] = self.timeViewed.__toDict__()
        return messageDict

    def __fromDict__(self, fromDict:dict) -> None:
    # Parse sender:
        added, self.sender = self._contacts.__getOrAdd__(name="<UNKNOWN-CONTACT>", id=fromDict['sender'])
    # Parse reciient type:
        self.recipientType = fromDict['recipientType']
    # Parse recipient:
        if (fromDict['recipient'] != None):
            if (self.recipientType == 'contact'):
                added, self.recipient = self._contacts.__getOrAdd__(name="<UNKNOWN-CONTACT>", id=fromDict['recipient'])
            elif (self.recipientType == 'group'):
                added, self.recipient = self._groups.__getOrAdd__(name="<UNKNOWN-GROUP>", id=fromDict['recipient'])
            else:
                raise ValueError("invalid recipient type in fromDict: %s" % self.recipientType)
    # Parse device:

        added, self.device = self.sender.devices.__getOrAdd__("<UNKNOWN-DEVICE>", fromDict['device'])
        if (added == True):
            self._contacts.__save__()
    # Parse timestamp:
        self.timestamp = Timestamp(fromDict=fromDict['timestamp'])
    # Parse message Type:
        self.messageType = fromDict['messageType']
    # Parse Delivered: (is and time)
        self.isDelivered = fromDict['isDelivered']
        if (fromDict['timeDelivered'] != None):
            self.timeDelivered = Timestamp(fromDict=fromDict['timeDelivered'])
        else:
            self.timeDelivered = None
    # Parse read (is and time):
        self.isRead = fromDict['isRead']
        if (fromDict['timeRead'] != None):
            self.timeRead = Timestamp(fromDict=fromDict['timeRead'])
        else:
            self.timeRead = None
    # Parse viewed (is and time):
        self.isViewed = fromDict['isViewed']
        if (fromDict['timeViewed'] != None):
            self.timeViewed = Timestamp(fromDict=fromDict['timeViewed'])
        else:
            self.timeViewed = None
        return
###############################
# Methods:
###############################
    def markDelivered(self, when: Timestamp) -> None:
        self.isDelivered = True
        self.timeDelivered = when
        return

    def markRead(self, when: Timestamp) -> None:
        self.isRead = True
        self.timeRead = when
        return

    def markViewed(self, when: Timestamp) -> None:
        self.isViewed = True
        self.timeViewed = when
        return
