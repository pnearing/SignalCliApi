#!/usr/bin/env python3
"""
File: signal_message.py
Store and handle a base message.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915
from typing import TypeVar, Optional, Any
import socket
import logging

from .signal_common import __type_error__, MessageTypes, RecipientTypes
from .signal_contacts import SignalContacts
from .signal_contact import SignalContact
from .signal_devices import SignalDevices
from .signal_device import SignalDevice
from .signal_groups import SignalGroups
from .signal_group import SignalGroup
from .signal_timestamp import SignalTimestamp

Self = TypeVar("Self", bound="SignalMessage")


class SignalMessage:
    """
    Base class for a message.
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
                 message_type: MessageTypes = MessageTypes.NOT_SET,
                 ) -> None:
        """
        Initialize a message.
        :param command_socket: Socket.socket: The socket to preform command operations with
        :param account_id: str: This account ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts SignalContacts object.
        :param groups: SignalGroups: This accounts SignalGroups object.
        :param devices: SignalDevices: This accounts SignalDevices object.
        :param this_device: SignalDevice: The device object for this device.
        :param from_dict: Optional[dict] = None: Load from a dict provided by __to_dict__()
        :param raw_message: Optional[dict] = None: Load from a dict provided by signal.
        :param sender: Optional[SignalContact] = None: The sender SignalContact of this message.
        :param recipient: Optional[SignalContact | SignalGroup] = None: The recipient
        SignalContact | SignalGroup of this message.
        :param device: Optional[SignalDevice] = None: The device this message was sent from.
        :param timestamp: Optional[SignalTimestamp] = None: The timestamp object of this message.
        :param message_type: Int = TYPE_NOT_SET: The type of message this is.
        :returns: None
        """

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
        if not isinstance(contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "SignalContacts", contacts)
        if not isinstance(groups, SignalGroups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "SignalGroups", groups)
        if not isinstance(devices, SignalDevices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "SignalDevices", devices)
        if not isinstance(this_device, SignalDevice):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "SignalDevice", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if raw_message is not None and not isinstance(raw_message, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_message", "dict", raw_message)
        if sender is not None and not isinstance(sender, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("sender", "SignalContact", sender)
        if recipient is not None and not isinstance(recipient, (SignalContact, SignalGroup)):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "SignalContact | SignalGroup", recipient)
        if device is not None and not isinstance(device, SignalDevice):
            logger.critical("Raising TypeError:")
            __type_error__("device", "SignalDevice", device)
        if timestamp is not None and not isinstance(timestamp, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "SignalTimestamp", timestamp)
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
        self._contacts: SignalContacts = contacts
        """This accounts SignalContacts object."""
        self._groups: SignalGroups = groups
        """This accounts SignalGroups object."""
        self._devices: SignalDevices = devices
        """This accounts SignalDevice object."""
        self._this_device: SignalDevice = this_device
        """The SignalDevice for this device we're using."""

        # Set external properties:
        self._sender: SignalContact = sender
        """The sender of the message."""
        self._recipient: SignalContact | SignalGroup = recipient
        """The recipient of the message."""
        self._recipient_type: Optional[RecipientTypes] = None
        """The recipient type of the message, either 'contact' or 'group'."""
        self._device: SignalDevice = device
        """The device the message was sent from."""
        self._timestamp: SignalTimestamp = timestamp
        """The timestamp object for this message."""
        self._message_type: MessageTypes = message_type
        """The message type."""
        self._is_delivered: bool = False
        """Is this message delivered?"""
        self._time_delivered: Optional[SignalTimestamp] = None
        """SignalTimestamp of when this message was delivered."""
        self._is_read: bool = False
        """Is this message read?"""
        self._time_read: Optional[SignalTimestamp] = None
        """SignalTimestamp of when this message was read."""
        self._is_viewed: bool = False
        """Is this message viewed?"""
        self._time_viewed: Optional[SignalTimestamp] = None
        """SignalTimestamp of when this message was viewed."""

        # Parse from dict:
        if from_dict is not None:
            logger.debug("Loading from_dict")
            self.__from_dict__(from_dict)
        # Parse from raw Message:
        elif raw_message is not None:
            logger.debug("Loading from raw_message")
            self.__from_raw_message__(raw_message)
            self.sender.__seen__(self.timestamp)
            self.device.__seen__(self.timestamp)
            self.recipient.__seen__(self.timestamp)  # SignalGroup and SignalContact have this func.

        # Set recipient type
        if self.recipient is not None:
            if isinstance(self.recipient, SignalContact):
                self._recipient_type = RecipientTypes.CONTACT
            elif isinstance(self.recipient, SignalGroup):
                self._recipient_type = RecipientTypes.GROUP

    #######################
    # Init:
    #######################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load from a raw message dict provided by signal.
        :param raw_message: Dict[str, Any]: The dict to load from
        :return: None
        """
        # Parse Sender
        added, self._sender = self._contacts.__get_or_add__(name=raw_message['sourceName'],
                                                            number=raw_message['sourceNumber'],
                                                            uuid=raw_message['sourceUuid'])
        if added:
            self._contacts.__save__()
        # Parse recipient:
        self._recipient = None
        if 'dataMessage' in raw_message.keys():
            data_message: dict[str, Any] = raw_message['dataMessage']
            if 'groupInfo' in data_message.keys():
                added, self._recipient = self._groups.__get_or_add__(
                    group_id=data_message['groupInfo']['groupId'])
                self._recipient_type = RecipientTypes.GROUP
        if self.recipient is None:
            self._recipient = self._contacts.get_self()
            self._recipient_type = RecipientTypes.CONTACT
        # Parse device:
        added, self._device = self.sender.devices.__get_or_add__(
            device_id=raw_message['sourceDevice'])
        if added:
            self._contacts.__save__()
        # Parse Timestamp:
        self._timestamp = SignalTimestamp(timestamp=raw_message['timestamp'])

    #########################
    # Overrides:
    #########################
    def __eq__(self, other: Self) -> bool:
        """
        Calculate equality.
        :param other: SignalMessage: The other message to compare to.
        :return: bool: Return True the messages are the same.
        """
        if isinstance(other, SignalMessage):
            # Check sender:
            if self.sender != other.sender:
                return False
            # Check recipients:
            if self.recipient != other.recipient:
                return False
            # Check Timestamp
            if self.timestamp != other.timestamp:
                return False
            return True
        return False

    ##################################
    # To / From dict:
    ##################################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: Dict[str, Any]: The dict to send to __from_dict__()
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
        :param from_dict: Dict[str, Any] The dict created by __to_dict__()
        :return: None
        """
        # Parse sender:
        _, self._sender = self._contacts.__get_or_add__(contact_id=from_dict['sender'])
        # Parse recipient type:
        self._recipient_type = RecipientTypes(from_dict['recipientType'])
        # Parse recipient:
        if from_dict['recipient'] is not None:
            if self.recipient_type == RecipientTypes.CONTACT:
                _, self._recipient = self._contacts.__get_or_add__(
                    contact_id=from_dict['recipient'])
            elif self.recipient_type == RecipientTypes.GROUP:
                _, self._recipient = self._groups.__get_or_add__(group_id=from_dict['recipient'])
        # Parse device:

        _, self._device = self.sender.devices.__get_or_add__(device_id=from_dict['device'])
        self._contacts.__save__()
        # Parse timestamp:
        self._timestamp = SignalTimestamp(from_dict=from_dict['timestamp'])
        # Parse message Type:
        self._message_type = MessageTypes(from_dict['messageType'])
        # Parse Delivered: (is and time)
        self._is_delivered = from_dict['isDelivered']
        if from_dict['timeDelivered'] is not None:
            self._time_delivered = SignalTimestamp(from_dict=from_dict['timeDelivered'])
        else:
            self._time_delivered = None
        # Parse read (is and time):
        self._is_read = from_dict['isRead']
        if from_dict['timeRead'] is not None:
            self._time_read = SignalTimestamp(from_dict=from_dict['timeRead'])
        else:
            self._time_read = None
        # Parse viewed (is and time):
        self._is_viewed = from_dict['isViewed']
        if from_dict['timeViewed'] is not None:
            self._time_viewed = SignalTimestamp(from_dict=from_dict['timeViewed'])
        else:
            self._time_viewed = None

    ###############################
    # Methods:
    ###############################
    def mark_delivered(self, when: Optional[SignalTimestamp] = None) -> None:
        """
        Mark a message as delivered.
        :param when: Optional[SignalTimestamp]: The time delivered, if None, NOW is used.
        :returns: None
        :raises: TypeError: If when is not a SignalTimestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_delivered.__name__)
        # Type check when:
        if when is not None and not isinstance(when, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'SignalTimestamp', when)
        # If we're already delivered, do nothing:
        if self.is_delivered:
            return
        # Mark as delivered.
        self._is_delivered = True
        # Set timestamp:
        if when is None:
            self._time_delivered = SignalTimestamp(now=True)
        else:
            self._time_delivered = when
        return

    def mark_read(self, when: Optional[SignalTimestamp]) -> None:
        """
        Mark a message as read.
        :param when: Optional[SignalTimestamp]: The time read, if None, NOW is used.
        :returns: None
        :raises: TypeError: If when is not a SignalTimestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_read.__name__)
        # Type check when:
        if when is not None and not isinstance(when, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'SignalTimestamp', when)
        # If we're already read, do nothing:
        if self.is_read:
            return
        # Mark as read:
        self._is_read = True
        # Set timestamp:
        if when is None:
            self._time_read = SignalTimestamp(now=True)
        else:
            self._time_read = when
        return

    def mark_viewed(self, when: Optional[SignalTimestamp]) -> None:
        """
        Mark a message as viewed.
        :param when: Optional[SignalTimestamp]: The time viewed, if None, NOW is used.
        :returns: None
        :raises: TypeError if when is not a SignalTimestamp.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_viewed.__name__)
        # Type check when:
        if when is not None and not isinstance(when, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__('when', 'SignalTimestamp', when)
        # If already viewed, do nothing.
        if self.is_viewed:
            return
        # Mark as viewed:
        self._is_viewed = True
        # Set timestamp:
        if when is None:
            self._time_viewed = SignalTimestamp(now=True)
        else:
            self._time_viewed = when
        return

############################################
# Properties:
############################################
    @property
    def sender(self) -> SignalContact:
        """
        The sender of the message
        :return: SignalContact
        """
        return self._sender

    @property
    def recipient(self) -> SignalContact | SignalGroup:
        """
        The recipient of the message
        :return: SignalContact | SignalGroup
        """
        return self._recipient

    @property
    def recipient_type(self) -> Optional[RecipientTypes]:
        """
        The type of the recipient.
        :return: Optional[RecipientTypes]
        """
        return self._recipient_type

    @recipient_type.setter
    def recipient_type(self, value: RecipientTypes) -> None:
        if not isinstance(value, RecipientTypes):
            __type_error__('value', 'RecipientTypes', value)
        self._recipient_type = value

    @property
    def device(self) -> SignalDevice:
        """
        The device the message was sent from.
        :return: SignalDevice
        """
        return self._device

    @property
    def timestamp(self) -> SignalTimestamp:
        """
        The timestamp of the message.
        :return: SignalTimestamp
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: SignalTimestamp) -> None:
        if not isinstance(value, SignalTimestamp):
            __type_error__('value', 'SignalTimestamp', value)
        self._timestamp = value

    @property
    def message_type(self) -> MessageTypes:
        """
        The type of message
        :return: MessageTypes
        """
        return self._message_type

    @property
    def is_delivered(self) -> bool:
        """
        Has this message been delivered?
        :return: bool
        """
        return self._is_delivered

    @property
    def time_delivered(self) -> Optional[SignalTimestamp]:
        """
        The time this message was delivered
        :return: Optional[SignalTimestamp]
        """
        return self._time_delivered

    @property
    def is_read(self) -> bool:
        """
        Has this message been read?
        :return: bool
        """
        return self._is_read

    @property
    def time_read(self) -> Optional[SignalTimestamp]:
        """
        The time the message was read.
        :return: Optional[SignalTimestamp]
        """
        return self._time_read

    @property
    def is_viewed(self) -> bool:
        """
        Has this message been viewed?
        :return: bool
        """
        return self._is_viewed

    @property
    def time_viewed(self) -> Optional[SignalTimestamp]:
        """
        The time the message was viewed.
        :return: Optional[SignalTimestamp]
        """
        return self._time_viewed
