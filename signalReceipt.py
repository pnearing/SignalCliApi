#!/usr/bin/env python3

from typing import Optional, Iterable
import socket

from signalCommon import __typeError__
from signalContact import Contact
from signalContacts import Contacts
from signalDevice import Device
from signalDevices import Devices
from signalGroup import Group
from signalGroups import Groups
from signalMessage import Message
from signalTimestamp import Timestamp

class Receipt(Message):
    TYPE_DELIVERY: int = 1
    TYPE_READ: int = 2
    TYPE_VIEWED: int = 3
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId: str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups, devices:
                    Devices, thisDevice: Device,
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
                    when: Optional[Timestamp] = None,
                    receiptType: int = Message.TYPE_NOT_SET,
                    timestamps: Optional[Iterable[Timestamp]] = None,
                ) -> None:
# Argument Checks:
    # Check when:
        if (when != None and isinstance(when, Timestamp) == False):
            __typeError__("when", "Timestamp", when)
    # Check receipt Type:
        if (isinstance(receiptType, int) == False):
            __typeError__("receiptType", "int", receiptType)
    # Check Timestamps:
        timestampList: list[Timestamp] = []
        if (timestamps != None):
            if (isinstance(timestamps, Iterable) == False):
                __typeError__("timestamps", "Iterable[Timestamp]", timestamps)
            i = 0
            for targetTimestamp in timestamps:
                if (isinstance(targetTimestamp, Timestamp) == False):
                    __typeError__("timestamps[%i]" % i, "Timestamp", targetTimestamp)
                timestampList.append(targetTimestamp)
                i = i + 1
# Set external properties:
    # Set when:
        self.when: Timestamp = when
    # Set receipt Type:
        self.receiptType = receiptType
    # Set target timestamps:
        self.timestamps: list[Timestamp] = timestampList
    # Set body:
        self.body: str = ''
# Run super init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, sender, recipient, device, timestamp, Message.TYPE_RECEIPT_MESSAGE, isDelivered,
                            timeDelivered, isRead, timeRead, isViewed, timeViewed)
# Mark as read, viewed and delivered:
        if (self.timestamp != None):
            super().markDelivered(self.timestamp)
            super().markRead(self.timestamp)
            super().markViewed(self.timestamp)
# Update the body:
        self.__updateBody__()
        return

##########################
# Init:
#########################
    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        receiptMessage: dict[str, object] = rawMessage['receiptMessage']
    # Load when:
        self.when = Timestamp(timestamp=receiptMessage['when'])
    # Load receipt type:
        if (receiptMessage['isDelivery'] == True):
            self.receiptType = self.TYPE_DELIVERY
        elif (receiptMessage['isRead'] == True):
            self.receiptType = self.TYPE_READ
        elif (receiptMessage['isViewed'] == True):
            self.receiptType = self.TYPE_VIEWED
        else:
            errorMessage = "Unknown receipt type... receiptMessage= %s" % str(receiptMessage)
            raise RuntimeError(errorMessage)
    # Load target timestamps:
        self.timestamps = []
        for targetTimestamp in receiptMessage['timestamps']:
            self.timestamps.append(Timestamp(timestamp=targetTimestamp))
        return

##########################
# To / From Dict:
##########################
    def __toDict__(self) -> dict:
        receiptDict = super().__toDict__()
    # Store when:
        receiptDict['when'] = None
        if (self.when != None):
            receiptDict['when'] = self.when.__toDict__()
    # Store receipt type:
        receiptDict['receiptType'] = self.receiptType
    # Store target timestamps:
        receiptDict['timestamps'] = []
        for timestamp in self.timestamps:
            receiptDict['timestamps'].append( timestamp.__toDict__() )
        return receiptDict
    
    def __fromDict__(self, fromDict: dict) -> None:
        super().__fromDict__(fromDict)
    # Load when:
        self.when = None
        if (fromDict['when'] != None):
            self.when = Timestamp(fromDict=fromDict['when'])
    # Load receipt Type:
        self.receiptType = fromDict['receiptType']
    # Load target timestamps:
        self.timestamps = []
        for timestampDict in fromDict['timestamps']:
            self.timestamps.append( Timestamp(fromDict=timestampDict) )
        return
#########################
# Helpers:
#########################
    def __updateBody__(self) -> None:
        timestampStrs = [timestamp.getDisplayTime() for timestamp in self.timestamps]
        timestampsStr = ', '.join(timestampStrs)
        if (self.receiptType == self.TYPE_DELIVERY):
            self.body = "The messages: %s have been delivered to: %s 's device: %s" % ( 
                                                                                    timestampsStr,
                                                                                    self.sender.getDisplayName(),
                                                                                    self.device.getDisplayName(),
                                                                                )
        elif (self.receiptType == self.TYPE_READ):
            self.body = "The messages: %s have been read by: %s on device: %s" % (
                                                                                    timestampsStr,
                                                                                    self.sender.getDisplayName(),
                                                                                    self.device.getDisplayName(),
                                                                                )
        elif (self.receiptType == self.TYPE_VIEWED):
            self.body = "The messages: %s have been viewed by: %s on device: %s" % (
                                                                                    timestampsStr,
                                                                                    self.sender.getDisplayName(),
                                                                                    self.device.getDisplayName(),
                                                                                )
        else:
            self.body = "Invalid receipt."
        return
###########################
# Methods:
###########################
