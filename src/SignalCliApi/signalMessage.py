#!/usr/bin/env python3
"""
File: signalMessage.py
Store and handle a base message.
"""
from typing import TypeVar, Optional, Any
import socket
import logging

from .signalCommon import __type_error__, MessageTypes, RecipientTypes
from .signalContacts import Contacts
from .signalContact import Contact
from .signalDevices import Devices
from .signalDevice import Device
from .signalGroups import Groups
from .signalGroup import Group
from .signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Message")


class Message(object):
    """
    Base class for a message.
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
                 message_type: MessageTypes = MessageTypes.NOT_SET,
                 ) -> None:
        """
        Initialize a message.
        :param command_socket: socket.socket: The socket to preform command operations with
        :param account_id: str: This account ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts Contacts object.
        :param groups: Groups: This accounts Groups object.
        :param devices: Devices: This accounts Devices object.
        :param this_device: Device: The device object for this device.
        :param from_dict: Optional[dict] = None: Load from a dict provided by __to_dict__()
        :param raw_message: Optional[dict] = None: Load from a dict provided by signal.
        :param sender: Optional[Contact] = None: The sender Contact of this message.
        :param recipient: Optional[Contact | Group] = None: The recipient Contact | Group of this message.
        :param device: Optional[Device] = None: The device this message was sent from.
        :param timestamp: Optional[Timestamp] = None: The timestamp object of this message.
        :param message_type: int = TYPE_NOT_SET: The type of message this is.
        :returns: None
        """
        # Super:
        object.__init__(self)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Arg Type Checks:
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__('command_socket', 'socket', command_socket)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__('contact_id', 'str', account_id)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__('config_path', 'str', config_path)
        if not isinstance(contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "Contacts", contacts)
        if not isinstance(groups, Groups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "Groups", groups)
        if not isinstance(devices, Devices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "Device", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if raw_message is not None and not isinstance(raw_message, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_message", "dict", raw_message)
        if sender is not None and not isinstance(sender, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("sender", "Contact", sender)
        if recipient is not None and not isinstance(recipient, (Contact, Group)):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "Contact | Group", recipient)
        if device is not None and not isinstance(device, Device):
            logger.critical("Raising TypeError:")
            __type_error__("device", "Device", device)
        if timestamp is not None and not isinstance(timestamp, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "Timestamp", timestamp)
        if not isinstance(message_type, MessageTypes):
            logger.critical("Raising TypeError:")
            __type_error__("message_type", "MessageTypes(enum)", message_type)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to preform command operations on."""
        self._account_id: str = account_id
        """This accounts ID."""
        self._config_path: str = config_path
        """The full path to signal-cli config directory."""
        self._contacts: Contacts = contacts
        """This accounts Contacts object."""
        self._groups: Groups = groups
        """This accounts Groups object."""
        self._devices: Devices = devices
        """This accounts Device object."""
        self._this_device: Device = this_device
        """The Device for this device we're using."""

        # Set external properties:
        self.sender: Contact = sender
        """The sender of the message."""
        self.recipient: Contact | Group = recipient
        """The recipient of the message."""
        self.recipient_type: Optional[RecipientTypes] = None
        """The recipient type of the message, either 'contact' or 'group'."""
        self.device: Device = device
        """The device the message was sent from."""
        self.timestamp: Timestamp = timestamp
        """The timestamp object for this message."""
        self.message_type: MessageTypes = message_type
        """The message type."""
        self.is_delivered: bool = False
        """Is this message delivered?"""
        self.time_delivered: Optional[Timestamp] = None
        """Timestamp of when this message was delivered."""
        self.is_read: bool = False
        """Is this message read?"""
        self.time_read: Optional[Timestamp] = None
        """Timestamp of when this message was read."""
        self.is_viewed: bool = False
        """Is this message viewed?"""
        self.time_viewed: Optional[Timestamp] = None
        """Timestamp of when this message was viewed."""

        # Parse from dict:
        if from_dict is not None:
            logger.debug("Loading from_dict")
            self.__from_dict__(from_dict)
        # Parse from raw Message:
        elif raw_message is not None:
            logger.debug("Loading from raw_message")
            self.__from_raw_message__(raw_message)
            self.sender.seen(self.timestamp)
            self.device.seen(self.timestamp)
            self.recipient.seen(self.timestamp)  # Both Group and Contact have a seen function.

        # Set recipient type
        if self.recipient is not None:
            if isinstance(self.recipient, Contact):
                self.recipient_type = RecipientTypes.CONTACT
            elif isinstance(self.recipient, Group):
                self.recipient_type = RecipientTypes.GROUP
        return

    #######################
    # Init:
    #######################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load from a raw message dict provided by signal.
        :param raw_message: dict[str, Any]: The dict to load from
        :return: None
        """
        # Parse Sender
        added, self.sender = self._contacts.__get_or_add__(name=raw_message['sourceName'],
                                                           number=raw_message['sourceNumber'],
                                                           uuid=raw_message['sourceUuid'])
        if added:
            self._contacts.__save__()
        # Parse recipient:
        self.recipient = None
        if 'dataMessage' in raw_message.keys():
            dataMessage: dict[str, Any] = raw_message['dataMessage']
            if 'groupInfo' in dataMessage.keys():
                added, self.recipient = self._groups.__get_or_add__(group_id=dataMessage['groupInfo']['groupId'])
                self.recipient_type = RecipientTypes.GROUP
        if self.recipient is None:
            self.recipient = self._contacts.get_self()
            self.recipient_type = RecipientTypes.CONTACT
        # Parse device:
        added, self.device = self.sender.devices.__get_or_add__(device_id=raw_message['sourceDevice'])
        if added:
            self._contacts.__save__()
        # Parse Timestamp:
        self.timestamp = Timestamp(timestamp=raw_message['timestamp'])
        return

    #########################
    # Overrides:
    #########################
    def __eq__(self, other: Self) -> bool:
        """
        Calculate equality.
        :param other: Message: The other message to compare to.
        :return: bool: True the messages are the same.
        """
        if isinstance(other, Message):
            # Check sender:
            if self.sender != other.sender:
                return False
            # Check recipients:
            if self.recipient_type != other.recipient_type:
                return False
            if self.recipient != other.recipient:
                return False
            # Check Timestamp
            if self.timestamp != other.timestamp:
                return False
            # Check device:
            if self.device != other.device:
                return False
            # Check the message type:
            if self.message_type != other.message_type:
                return False
            # Check Delivered (is and time):
            if self.is_delivered != other.is_delivered:
                return False
            if self.time_delivered != other.time_delivered:
                return False
            # Check Read (is and time):
            if self.is_read != other.is_read:
                return False
            if self.time_read != other.time_read:
                return False
            # Check Viewed (is and time):
            if self.is_viewed != other.is_viewed:
                return False
            if self.time_viewed != other.time_viewed:
                return False
        return False

    ##################################
    # To / From dict:
    ##################################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to send to __from_dict__()
        """
        message_dict = {
            'sender': None,
            'recipient': None,
            'recipientType': self.recipient_type.value,
            'device': None,
            'timestamp': None,
            'messageType': self.message_type.value,
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

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any] The dict created by __to_dict__()
        :return: None
        """
        # Parse sender:
        _, self.sender = self._contacts.__get_or_add__(contact_id=from_dict['sender'])
        # Parse recipient type:
        self.recipient_type = RecipientTypes(from_dict['recipientType'])
        # Parse recipient:
        if from_dict['recipient'] is not None:
            if self.recipient_type == RecipientTypes.CONTACT:
                _, self.recipient = self._contacts.__get_or_add__(contact_id=from_dict['recipient'])
            elif self.recipient_type == RecipientTypes.GROUP:
                _, self.recipient = self._groups.__get_or_add__(group_id=from_dict['recipient'])
        # Parse device:

        _, self.device = self.sender.devices.__get_or_add__(device_id=from_dict['device'])
        self._contacts.__save__()
        # Parse timestamp:
        self.timestamp = Timestamp(from_dict=from_dict['timestamp'])
        # Parse message Type:
        self.message_type = MessageTypes(from_dict['messageType'])
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
    def mark_delivered(self, when: Optional[Timestamp] = None) -> None:
        """
        Mark a message as delivered.
        :param when: Optional[Timestamp]: The time delivered, if None, NOW is used.
        :returns: None
        :raises: TypeError: If when is not a Timestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_delivered.__name__)
        # Type check when:
        if when is not None and not isinstance(when, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'Timestamp', when)
        # If we're already delivered, do nothing:
        if self.is_delivered:
            return
        # Mark as delivered.
        self.is_delivered = True
        # Set timestamp:
        if when is None:
            self.time_delivered = Timestamp(now=True)
        else:
            self.time_delivered = when
        return

    def mark_read(self, when: Optional[Timestamp]) -> None:
        """
        Mark a message as read.
        :param when: Optional[Timestamp]: The time read, if None, NOW is used.
        :returns: None
        :raises: TypeError: If when is not a Timestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_read.__name__)
        # Type check when:
        if when is not None and not isinstance(when, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'Timestamp', when)
        # If we're already read do nothing:
        if self.is_read:
            return
        # Mark as read:
        self.is_read = True
        # Set timestamp:
        if when is None:
            self.time_read = Timestamp(now=True)
        else:
            self.time_read = when
        return

    def mark_viewed(self, when: Optional[Timestamp]) -> None:
        """
        Mark a message as viewed.
        :param when: Optional[Timestamp]: The time viewed, if None, NOW is used.
        :returns: None
        :raises: TypeError if when is not a Timestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_viewed.__name__)
        # Type check when:
        if when is not None and not isinstance(when, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'Timestamp', when)
        # If already viewed, do nothing.
        if self.is_viewed:
            return
        # Mark as viewed:
        self.is_viewed = True
        # Set timestamp:
        if when is None:
            self.time_viewed = Timestamp(now=True)
        else:
            self.time_viewed = when
        return
