#!/usr/bin/env python3
"""
File: signal_receipt.py
Store and handle a signal receipt message.
"""
# pylint: disable=R0913
import logging
from typing import Optional, Any
import socket

from .signal_common import MessageTypes, ReceiptTypes
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_message import SignalMessage
from .signal_timestamp import SignalTimestamp


class SignalReceipt(SignalMessage):
    """
    Class to store a receipt.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 this_device: SignalDevice,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 sender: Optional[SignalContact] = None,
                 recipient: Optional[SignalContact | SignalGroup] = None,
                 device: Optional[SignalDevice] = None,
                 timestamp: Optional[SignalTimestamp] = None,
                 ) -> None:
        """
        Initialize a SignalReceipt.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object for the device we're using.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__()
        :param raw_message: Optional[dict[str, Any]]: The dict provided by signal.
        :param sender: Optional[SignalContact]: The sender of the receipt.
        :param recipient: Optional[SignalContact | SignalGroup]: The recipient of the receipt.
        :param device: Optional[SignalDevice]: The device this receipt was generated from.
        :param timestamp: Optional[SignalTimestamp]: The timestamp of the receipt.
        """
        # Set internal properties:
        self._is_parsed: bool = False
        """Has this receipt been parsed yet?"""

        # Set external properties:
        # Set when:
        self.when: Optional[SignalTimestamp] = None
        """When this was read / viewed / delivered."""
        # Set receipt Type:
        self.receipt_type: ReceiptTypes = ReceiptTypes.NOT_SET
        """The type of receipt."""
        # Set target timestamps:
        self.timestamps: list[SignalTimestamp] = []
        """The timestamps this applies to."""
        # Set body:
        self.body: str = ''
        """The body of the message."""
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, sender, recipient, device, timestamp,
                         MessageTypes.RECEIPT)

        # Mark this receipt as read, viewed and delivered:
        if self.timestamp is not None:
            super().mark_delivered(self.timestamp)
            super().mark_read(self.timestamp)
            super().mark_viewed(self.timestamp)
        # Update the body:
        self.__update_body__()

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
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__from_raw_message__.__name__)
        super().__from_raw_message__(raw_message)
        receipt_message: dict[str, Any] = raw_message['receiptMessage']
        # Load when:
        self.when = SignalTimestamp(timestamp=receipt_message['when'])
        # Load receipt type:
        if receipt_message['isDelivery']:
            self.receipt_type = ReceiptTypes.DELIVER
        elif receipt_message['isRead']:
            self.receipt_type = ReceiptTypes.READ
        elif receipt_message['isViewed']:
            self.receipt_type = ReceiptTypes.VIEWED
        else:

            error_message: str = f"Unknown receipt type... receiptMessage={str(receipt_message)}"
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)
        # Load target timestamps:
        self.timestamps = []
        for target_timestamp in receipt_message['timestamps']:
            self.timestamps.append(SignalTimestamp(timestamp=target_timestamp))

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
            self.when = SignalTimestamp(from_dict=from_dict['when'])
        # Load receipt Type:
        self.receipt_type = ReceiptTypes(from_dict['receiptType'])
        # Load target timestamps:
        self.timestamps = []
        for timestamp_dict in from_dict['timestamps']:
            self.timestamps.append(SignalTimestamp(from_dict=timestamp_dict))

    #########################
    # Helpers:
    #########################
    def __update_body__(self) -> None:
        """
        Update the body of the message.
        :return: None
        """
        timestamp_strs: list[str] = [timestamp.get_display_time() for timestamp in self.timestamps]
        timestamps_str: str = ', '.join(timestamp_strs)
        if self.receipt_type == ReceiptTypes.DELIVER:
            self.body = (f"The messages: {timestamps_str} have been delivered "
                         f"to: {self.sender.get_display_name()}'s "
                         f"device: {self.device.get_display_name()}")
        elif self.receipt_type == ReceiptTypes.READ:
            self.body = (f"The messages: {timestamps_str} have been read "
                         f"by: {self.sender.get_display_name()} on "
                         f"device: {self.device.get_display_name()}")
        elif self.receipt_type == ReceiptTypes.VIEWED:
            self.body = (f"The messages: {timestamps_str} have been viewed "
                         f"by: {self.sender.get_display_name()} on "
                         f"device: {self.device.get_display_name()}")
        else:
            self.body = "Invalid receipt."
