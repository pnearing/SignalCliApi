#!/usr/bin/env python3

from typing import TypeVar, Optional, Iterable
import socket
import json
import sys

from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalContacts import Contacts
from .signalContact import Contact
from .signalDevices import Devices
from .signalDevice import Device
from .signalGroups import Groups
from .signalGroup import Group
from .signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Message")
DEBUG: bool = False


class Message(object):
    """Base class for a message."""
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
    TYPE_CALL_MESSAGE: int = 10

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
                 message_type: int = TYPE_NOT_SET,
                 is_delivered: bool = False,
                 time_delivered: Optional[Timestamp] = None,
                 is_read: bool = False,
                 time_read: Optional[Timestamp] = None,
                 is_viewed: bool = False,
                 time_viewed: Optional[Timestamp] = None,
                 ) -> None:
        """
        Initialize a message.
        :param command_socket: socket.socket,
        :param account_id: str,
        :param config_path: str,
        :param contacts: Contacts,
        :param groups: Groups,
        :param devices: Devices,
        :param this_device: Device,
        :param from_dict: Optional[dict] = None,
        :param raw_message: Optional[dict] = None,
        :param sender: Optional[Contact] = None,
        :param recipient: Optional[Contact | Group] = None,
        :param device: Optional[Device] = None,
        :param timestamp: Optional[Timestamp] = None,
        :param message_type: int = TYPE_NOT_SET,
        :param is_delivered: bool = False,
        :param time_delivered: Optional[Timestamp] = None,
        :param is_read: bool = False,
        :param time_read: Optional[Timestamp] = None,
        :param is_viewed: bool = False,
        :param time_viewed: Optional[Timestamp] = None,
        :returns: None
        """
        # Arg Type Checks:
        if not isinstance(command_socket, socket.socket):
            __type_error__('command_socket', 'socket', command_socket)
        if not isinstance(account_id, str):
            __type_error__('contact_id', 'str', account_id)
        if not isinstance(config_path, str):
            __type_error__('config_path', 'str', config_path)
        if not isinstance(contacts, Contacts):
            __type_error__("contacts" "Contacts", contacts)
        if not isinstance(groups, Groups):
            __type_error__("groups", "Groups", groups)
        if not isinstance(devices, Devices):
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            __type_error__("this_device", "Device", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        if raw_message is not None and not isinstance(raw_message, dict):
            __type_error__("raw_message", "dict", raw_message)
        if sender is not None and not isinstance(sender, Contact):
            __type_error__("sender", "Contact", sender)
        if recipient is not None and not isinstance(recipient, Contact) and not isinstance(recipient, Group):
            __type_error__("recipient", "Contact | Group", recipient)
        if device is not None and not isinstance(device, Device):
            __type_error__("device", "Device", device)
        if timestamp is not None and not isinstance(timestamp, Timestamp):
            __type_error__("timestamp", "Timestamp", timestamp)
        if not isinstance(message_type, int):
            __type_error__("message_type", "int", message_type)
        if not isinstance(is_delivered, bool):
            __type_error__("is_delivered", "bool", is_delivered)
        if time_delivered is not None and not isinstance(time_delivered, Timestamp):
            __type_error__("time_delivered", "Timestamp", time_delivered)
        if not isinstance(is_read, bool):
            __type_error__("is_read", "bool", is_read)
        if time_read is not None and not isinstance(time_read, Timestamp):
            __type_error__("time_read", "Timestamp", time_read)
        if not isinstance(is_viewed, bool):
            __type_error__("is_viewed", "bool", is_viewed)
        if time_viewed is not None and not isinstance(time_viewed, Timestamp):
            __type_error__("time_viewed", "Timestamp", time_viewed)
        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        self._account_id: str = account_id
        self._config_path: str = config_path
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Devices = devices
        self._this_device: Device = this_device
        # Set external properties:
        self.sender: Contact = sender
        self.recipient: Contact | Group = recipient
        self.recipient_type: Optional[str] = None
        self.device: Device = device
        self.timestamp: Timestamp = timestamp
        self.message_type: int = message_type
        self.is_delivered: bool = is_delivered
        self.time_delivered: Optional[Timestamp] = time_delivered
        self.is_read: bool = is_read
        self.time_read: Optional[Timestamp] = time_read
        self.is_viewed: bool = is_viewed
        self.time_viewed: Optional[Timestamp] = time_viewed
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw Message:
        elif raw_message is not None:
            self.__from_raw_message__(raw_message)
            self.sender.seen(self.timestamp)
            self.device.seen(self.timestamp)
            if self.recipient_type == 'contact':
                self.recipient.seen(self.timestamp)
        # Set recipient type
        if self.recipient is not None:
            if isinstance(self.recipient, Contact):
                self.recipient_type = 'contact'
            elif isinstance(self.recipient, Group):
                self.recipient_type = 'group'
        return

    #######################
    # Init:
    #######################
    def __from_raw_message__(self, raw_message: dict) -> None:
        global DEBUG
        if DEBUG:
            print("Message.__from_raw_message__")
            print(raw_message)
        # Parse Sender
            print("DEBUG: %s" % raw_message['sourceNumber'])
        added, self.sender = self._contacts.__get_or_add__(
            name=raw_message['sourceName'],
            number=raw_message['sourceNumber'],
            uuid=raw_message['sourceUuid']
        )
        if DEBUG:
            print("DEBUG:", self.sender.number)
        if added:
            self._contacts.__save__()
        # Parse recipient:
        self.recipient = None
        if 'dataMessage' in raw_message.keys():
            dataMessage: dict[str, object] = raw_message['dataMessage']
            if 'groupInfo' in dataMessage.keys():
                added, self.recipient = self._groups.__get_or_add__("<UNKNOWN-GROUP>",
                                                                    dataMessage['groupInfo']['groupId'])
                self.recipient_type = 'group'
        if self.recipient is None:
            self.recipient = self._contacts.get_self()
            self.recipient_type = 'contact'
        # Parse device:
        added, self.device = self.sender.devices.__get_or_add__("<UNKNOWN-DEVICE>", raw_message['sourceDevice'])
        if added:
            self._contacts.__save__()
        # Parse Timestamp:
        self.timestamp = Timestamp(timestamp=raw_message['timestamp'])
        return

    #########################
    # Overrides:
    #########################
    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Message):
            # Check sender:
            if self.sender != __o.sender:
                return False
            # Check recipients:
            if self.recipient_type != __o.recipient_type:
                return False
            if self.recipient != __o.recipient:
                return False
            # Check Timestamp
            if self.timestamp != __o.timestamp:
                return False
            # Check device:
            if self.device != __o.device:
                return False
            # Check message type:
            if self.message_type != __o.message_type:
                return False
            # Check Delivered (is and time):
            if self.is_delivered != __o.is_delivered:
                return False
            if self.time_delivered != __o.time_delivered:
                return False
            # Check Read (is and time):
            if self.is_read != __o.is_read:
                return False
            if self.time_read != __o.time_read:
                return False
            # Check Viewed (is and time):
            if self.is_viewed != __o.is_viewed:
                return False
            if self.time_viewed != __o.time_viewed:
                return False
        return False

    ##################################
    # To / From dict:
    ##################################
    def __to_dict__(self) -> dict:
        message_dict = {
            'sender': None,
            'recipient': None,
            'recipientType': self.recipient_type,
            'device': None,
            'timestamp': None,
            'messageType': self.message_type,
            'isDelivered': self.is_delivered,
            'timeDelivered': None,
            'isRead': self.is_read,
            'timeRead': None,
            'isViewed': self.is_viewed,
            'timeViewed': None,
        }
        if self.sender is not None:
            message_dict['sender'] = self.sender.get_id()
        if self.recipient is not None:
            message_dict['recipient'] = self.recipient.get_id()
        if self.device is not None:
            message_dict['device'] = self.device.id
        if self.timestamp is not None:
            message_dict['timestamp'] = self.timestamp.__to_dict__()
        if self.time_delivered is not None:
            message_dict['timeDelivered'] = self.time_delivered.__to_dict__()
        if self.time_read is not None:
            message_dict['timeRead'] = self.time_read.__to_dict__()
        if self.time_viewed is not None:
            message_dict['timeViewed'] = self.time_viewed.__to_dict__()
        return message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        # Parse sender:
        added, self.sender = self._contacts.__get_or_add__(name="<UNKNOWN-CONTACT>", contact_id=from_dict['sender'])
        # Parse recipient type:
        self.recipient_type = from_dict['recipientType']
        # Parse recipient:
        if from_dict['recipient'] is not None:
            if self.recipient_type == 'contact':
                added, self.recipient = self._contacts.__get_or_add__(name="<UNKNOWN-CONTACT>",
                                                                      contact_id=from_dict['recipient'])
            elif self.recipient_type == 'group':
                added, self.recipient = self._groups.__get_or_add__(name="<UNKNOWN-GROUP>",
                                                                    group_id=from_dict['recipient'])
            else:
                raise ValueError("invalid recipient type in from_dict: %s" % self.recipient_type)
        # Parse device:

        added, self.device = self.sender.devices.__get_or_add__("<UNKNOWN-DEVICE>", from_dict['device'])
        if added:
            self._contacts.__save__()
        # Parse timestamp:
        self.timestamp = Timestamp(from_dict=from_dict['timestamp'])
        # Parse message Type:
        self.message_type = from_dict['messageType']
        # Parse Delivered: (is and time)
        self.is_delivered = from_dict['isDelivered']
        if from_dict['timeDelivered'] is not None:
            self.time_delivered = Timestamp(from_dict=from_dict['timeDelivered'])
        else:
            self.time_delivered = None
        # Parse read (is and time):
        self.is_read = from_dict['isRead']
        if from_dict['timeRead'] is not None:
            self.time_read = Timestamp(from_dict=from_dict['timeRead'])
        else:
            self.time_read = None
        # Parse viewed (is and time):
        self.is_viewed = from_dict['isViewed']
        if from_dict['timeViewed'] is not None:
            self.time_viewed = Timestamp(from_dict=from_dict['timeViewed'])
        else:
            self.time_viewed = None
        return

    ###############################
    # Methods:
    ###############################
    def mark_delivered(self, when: Timestamp) -> None:
        """
        Mark a message as delivered.
        :param when: Timestamp: The time delivered.
        :returns: None
        :raises: TypeError: If when is not a Timestamp.
        """
        if not isinstance(when, Timestamp):
            __type_error__('when', 'Timestamp', when)
        if self.is_delivered:
            return
        self.is_delivered = True
        self.time_delivered = when
        return

    def mark_read(self, when: Timestamp) -> None:
        """
        Mark a message as read.
        :param when: Timestamp: The time read.
        :returns: None
        :raises: TypeError: If when is not a Timestamp.
        """
        if not isinstance(when, Timestamp):
            __type_error__('when', 'Timestamp', when)
        if self.is_read:
            return
        self.is_read = True
        self.time_read = when
        return

    def mark_viewed(self, when: Timestamp) -> None:
        """
        Mark a message as viewed.
        :param when: Timestamp: The time viewed.
        :returns: None
        :raises: TypeError if when is not a Timestamp.
        """
        if not isinstance(when, Timestamp):
            __type_error__('when', 'Timestamp', when)
        if self.is_viewed:
            return
        self.is_viewed = True
        self.time_viewed = when
        return

