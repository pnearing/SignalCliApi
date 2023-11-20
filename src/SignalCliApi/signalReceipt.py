#!/usr/bin/env python3
"""
File: signalReceipt.py
Store and handle a signal receipt message.
"""
import logging
from typing import Optional, Iterable, Any
import socket

from .signalCommon import __type_error__, MessageTypes, ReceiptTypes
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalTimestamp import Timestamp


class Receipt(Message):
    """
    Class to store a receipt.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 ) -> None:
        """
        Initialize a Receipt.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The Device object for the device we're using.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__()
        :param raw_message: Optional[dict[str, Any]]: The dict provided by signal.
        :param sender: Optional[Contact]: The sender of the receipt.
        :param recipient: Optional[Contact | Group]: The recipient of the receipt.
        :param device: Optional[Device]: The device this receipt was generated from.
        :param timestamp: Optional[Timestamp]: The timestamp of the receipt.
        """
        # Set external properties:
        # Set when:
        self.when: Optional[Timestamp] = None
        """When this was read / veiwed / delivered."""
        # Set receipt Type:
        self.receipt_type: ReceiptTypes = ReceiptTypes.NOT_SET
        """The type of receipt."""
        # Set target timestamps:
        self.timestamps: list[Timestamp] = []
        """The timestamps this applies to."""
        # Set body:
        self.body: str = ''
        """The body of the message."""
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, MessageTypes.RECEIPT)

        # Mark this receipt as read, viewed and delivered:
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
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        :raises RuntimeError: On an unknown receipt type sent by signal.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_raw_message__.__name__)
        super().__from_raw_message__(raw_message)
        receipt_message: dict[str, Any] = raw_message['receiptMessage']
        # Load when:
        self.when = Timestamp(timestamp=receipt_message['when'])
        # Load receipt type:
        if receipt_message['isDelivery']:
            self.receipt_type = ReceiptTypes.DELIVER
        elif receipt_message['isRead']:
            self.receipt_type = ReceiptTypes.READ
        elif receipt_message['isViewed']:
            self.receipt_type = ReceiptTypes.VIEWED
        else:

            error_message: str = "Unknown receipt type... receiptMessage= %s" % str(receipt_message)
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Load target timestamps:
        self.timestamps = []
        for target_timestamp in receipt_message['timestamps']:
            self.timestamps.append(Timestamp(timestamp=target_timestamp))
        return

    ##########################
    # To / From Dict:
    ##########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this receipt.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        receipt_dict = super().__to_dict__()
        # Store when:
        receipt_dict['when'] = None
        if self.when is not None:
            receipt_dict['when'] = self.when.__to_dict__()
        # Store receipt type:
        receipt_dict['receiptType'] = self.receipt_type.value
        # Store target timestamps:
        receipt_dict['timestamps'] = []
        for timestamp in self.timestamps:
            receipt_dict['timestamps'].append(timestamp.__to_dict__())
        return receipt_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        # Load when:
        self.when = None
        if from_dict['when'] is not None:
            self.when = Timestamp(from_dict=from_dict['when'])
        # Load receipt Type:
        self.receipt_type = ReceiptTypes(from_dict['receiptType'])
        # Load target timestamps:
        self.timestamps = []
        for timestampDict in from_dict['timestamps']:
            self.timestamps.append(Timestamp(from_dict=timestampDict))
        return

    #########################
    # Helpers:
    #########################
    def __updateBody__(self) -> None:
        """
        Update the body of the message.
        :return: None
        """
        timestamp_strs: list[str] = [timestamp.get_display_time() for timestamp in self.timestamps]
        timestamps_str: str = ', '.join(timestamp_strs)
        if self.receipt_type == ReceiptTypes.DELIVER:
            self.body = "The messages: %s have been delivered to: %s 's device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        elif self.receipt_type == ReceiptTypes.READ:
            self.body = "The messages: %s have been read by: %s on device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        elif self.receipt_type == ReceiptTypes.VIEWED:
            self.body = "The messages: %s have been viewed by: %s on device: %s" % (
                timestamps_str,
                self.sender.get_display_name(),
                self.device.get_display_name(),
            )
        else:
            self.body = "Invalid receipt."
        return
