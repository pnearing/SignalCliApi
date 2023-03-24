#!/usr/bin/env python3

from typing import Optional, Iterable
import socket

from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalTimestamp import Timestamp

class Receipt(Message):
    TYPE_DELIVERY: int = 1
    TYPE_READ: int = 2
    TYPE_VIEWED: int = 3
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups, devices:
                    Devices, this_device: Device,
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
                 when: Optional[Timestamp] = None,
                 receiptType: int = Message.TYPE_NOT_SET,
                 timestamps: Optional[Iterable[Timestamp]] = None,
                 ) -> None:
# Argument Checks:
    # Check when:
        if (when != None and isinstance(when, Timestamp) == False):
            __type_error__("when", "Timestamp", when)
    # Check receipt Type:
        if (isinstance(receiptType, int) == False):
            __type_error__("receiptType", "int", receiptType)
    # Check Timestamps:
        timestampList: list[Timestamp] = []
        if (timestamps != None):
            if (isinstance(timestamps, Iterable) == False):
                __type_error__("timestamps", "Iterable[Timestamp]", timestamps)
            i = 0
            for targetTimestamp in timestamps:
                if (isinstance(targetTimestamp, Timestamp) == False):
                    __type_error__("timestamps[%i]" % i, "Timestamp", targetTimestamp)
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
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_RECEIPT_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
# Mark as read, viewed and delivered:
        if (self.timestamp != None):
            super().mark_delivered(self.timestamp)
            super().mark_read(self.timestamp)
            super().mark_viewed(self.timestamp)
# Update the body:
        self.__updateBody__()
        return

##########################
# Init:
#########################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        receiptMessage: dict[str, object] = raw_message['receiptMessage']
    # Load when:
        self.when = Timestamp(timestamp=receiptMessage['when'])
    # Load receipt type:
        if (receiptMessage['isDelivery'] == True):
            self.receiptType = self.TYPE_DELIVERY
        elif (receiptMessage['is_read'] == True):
            self.receiptType = self.TYPE_READ
        elif (receiptMessage['is_viewed'] == True):
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
    def __to_dict__(self) -> dict:
        receiptDict = super().__to_dict__()
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
    
    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
    # Load when:
        self.when = None
        if (from_dict['when'] != None):
            self.when = Timestamp(fromDict=from_dict['when'])
    # Load receipt Type:
        self.receiptType = from_dict['receiptType']
    # Load target timestamps:
        self.timestamps = []
        for timestampDict in from_dict['timestamps']:
            self.timestamps.append( Timestamp(fromDict=timestampDict) )
        return
#########################
# Helpers:
#########################
    def __updateBody__(self) -> None:
        timestampStrs = [timestamp.get_display_time() for timestamp in self.timestamps]
        timestampsStr = ', '.join(timestampStrs)
        if (self.receiptType == self.TYPE_DELIVERY):
            self.body = "The messages: %s have been delivered to: %s 's device: %s" % ( 
                                                                                    timestampsStr,
                                                                                    self.sender.get_display_name(),
                                                                                    self.device.get_display_name(),
                                                                                )
        elif (self.receiptType == self.TYPE_READ):
            self.body = "The messages: %s have been read by: %s on device: %s" % (
                                                                                    timestampsStr,
                                                                                    self.sender.get_display_name(),
                                                                                    self.device.get_display_name(),
                                                                                )
        elif (self.receiptType == self.TYPE_VIEWED):
            self.body = "The messages: %s have been viewed by: %s on device: %s" % (
                                                                                    timestampsStr,
                                                                                    self.sender.get_display_name(),
                                                                                    self.device.get_display_name(),
                                                                                )
        else:
            self.body = "Invalid receipt."
        return
###########################
# Methods:
###########################
