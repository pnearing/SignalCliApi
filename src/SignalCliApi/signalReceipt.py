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
DEBUG: bool = False


class Receipt(Message):
    """Class to store a receipt."""
    TYPE_DELIVERY: int = 1
    TYPE_READ: int = 2
    TYPE_VIEWED: int = 3

    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
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
                 receipt_type: int = Message.TYPE_NOT_SET,
                 timestamps: Optional[Iterable[Timestamp]] = None,
                 ) -> None:
        # Argument Checks:
        # Check when:
        if when is not None and not isinstance(when, Timestamp):
            __type_error__("when", "Timestamp", when)
        # Check receipt Type:
        if not isinstance(receipt_type, int):
            __type_error__("receipt_type", "int", receipt_type)
        # Check Timestamps:
        timestampList: list[Timestamp] = []
        if timestamps is not None:
            if not isinstance(timestamps, Iterable):
                __type_error__("timestamps", "Iterable[Timestamp]", timestamps)
            i = 0
            for targetTimestamp in timestamps:
                if not isinstance(targetTimestamp, Timestamp):
                    __type_error__("timestamps[%i]" % i, "Timestamp", targetTimestamp)
                timestampList.append(targetTimestamp)
                i += 1
        # Set external properties:
        # Set when:
        self.when: Timestamp = when
        # Set receipt Type:
        self.receiptType = receipt_type
        # Set target timestamps:
        self.timestamps: list[Timestamp] = timestampList
        # Set body:
        self.body: str = ''
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_RECEIPT_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
        # Mark as read, viewed and delivered:
        if self.timestamp is not None:
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
        receipt_message: dict[str, object] = raw_message['receiptMessage']
        # Load when:
        self.when = Timestamp(timestamp=receipt_message['when'])
        # Load receipt type:
        if receipt_message['isDelivery']:
            self.receiptType = self.TYPE_DELIVERY
        elif receipt_message['isRead']:
            self.receiptType = self.TYPE_READ
        elif receipt_message['isViewed']:
            self.receiptType = self.TYPE_VIEWED
        else:
            errorMessage = "Unknown receipt type... receiptMessage= %s" % str(receipt_message)
            raise RuntimeError(errorMessage)
        # Load target timestamps:
        self.timestamps = []
        for target_timestamp in receipt_message['timestamps']:
            self.timestamps.append(Timestamp(timestamp=target_timestamp))
        return

    ##########################
    # To / From Dict:
    ##########################
    def __to_dict__(self) -> dict:
        receipt_dict = super().__to_dict__()
        # Store when:
        receipt_dict['when'] = None
        if self.when is not None:
            receipt_dict['when'] = self.when.__to_dict__()
        # Store receipt type:
        receipt_dict['receiptType'] = self.receiptType
        # Store target timestamps:
        receipt_dict['timestamps'] = []
        for timestamp in self.timestamps:
            receipt_dict['timestamps'].append(timestamp.__to_dict__())
        return receipt_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Load when:
        self.when = None
        if from_dict['when'] is not None:
            self.when = Timestamp(from_dict=from_dict['when'])
        # Load receipt Type:
        self.receiptType = from_dict['receiptType']
        # Load target timestamps:
        self.timestamps = []
        for timestampDict in from_dict['timestamps']:
            self.timestamps.append(Timestamp(from_dict=timestampDict))
        return

    #########################
    # Helpers:
    #########################
    def __updateBody__(self) -> None:
        timestamp_strs = [timestamp.get_display_time() for timestamp in self.timestamps]
        timestamps_str = ', '.join(timestamp_strs)
        if self.receiptType == self.TYPE_DELIVERY:
            self.body = "The messages: %s have been delivered to: %s 's device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        elif self.receiptType == self.TYPE_READ:
            self.body = "The messages: %s have been read by: %s on device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        elif self.receiptType == self.TYPE_VIEWED:
            self.body = "The messages: %s have been viewed by: %s on device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        else:
            self.body = "Invalid receipt."
        return
###########################
# Methods:
###########################
