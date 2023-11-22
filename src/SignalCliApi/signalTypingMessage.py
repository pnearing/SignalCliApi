#!/usr/bin/env python3
"""
File: signalTypingMessage.py
Store and handle a typing message.
"""
import logging
from typing import Optional, Any
import socket

from .signalCommon import RecipientTypes, MessageTypes, TypingStates, __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalTimestamp import Timestamp


class TypingMessage(Message):
    """Class to store a typing message."""
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
                 action: TypingStates = TypingStates.NOT_SET,
                 time_changed: Optional[Timestamp] = None
                 ) -> None:
        """
        Initialize a Typing Message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The Device object that represents the device we're on.
        :param from_dict: Optional[dict[str, Any]]: The dict created to __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: A dict provided by Signal.
        :param sender: Optional[Contact]: The sender of this message.
        :param recipient: Optional[Contact | Group]: The recipient of the message.
        :param device: Optional[Device]: The device that generated this message.
        :param timestamp: Optional[Timestamp]: The timestamp of this message.
        :param action: TypingStates: The typing state, either started or stopped.
        :param time_changed: Optional[Timestamp]: The time the typing state changed.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type check parameters:
        if not isinstance(action, TypingStates):
            logger.critical("Raising TypeError:")
            __type_error__('action', 'TypingStates', action)

        if time_changed is not None and not isinstance(time_changed, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__('time_changed', 'Optional[Timestamp]', time_changed)

        # Set external properties:
        # The typing action:
        self.action: TypingStates = action
        """The action being preformed. Either STARTED or STOPPED."""
        # The time the typing action changed.
        self.time_changed: Optional[Timestamp] = time_changed
        """The Timestamp of the action change."""

        # Run super:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, MessageTypes.TYPING)

        # update body:
        self.__update_body__()

        # Mark as delivered, read, and viewed.
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)
            self.mark_read(self.timestamp)
            self.mark_viewed(self.timestamp)
        return

    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by Signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        super().__from_raw_message__(raw_message)
        typing_dict: dict[str, Any] = raw_message['typingMessage']
        self.action = typing_dict['action']
        self.time_changed = Timestamp(timestamp=typing_dict['timestamp'])
        return

    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict for this typing message.
        :return: dict[str, Any]: A dict to provide to __from_dict__().
        """
        typing_message: dict[str, Any] = super().__to_dict__()
        typing_message['action'] = self.action.value
        if self.time_changed is not None:
            typing_message['timeChanged'] = self.time_changed.__to_dict__()
        else:
            typing_message['timeChanged'] = None
        return typing_message

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load fom a JSON friendly dict.
        :param from_dict: dict[str, Any]: A dict provided by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        self.action = TypingStates(from_dict['action'])
        self.time_changed = None
        if from_dict['timeChanged'] is not None:
            self.time_changed = Timestamp(from_dict=from_dict['timeChanged'])
        return

    def __get_action_string__(self) -> str:
        """
        Return the a string for the action.
        :return: str: The action string.
        """
        if self.action == TypingStates.STARTED:
            return 'started'
        elif self.action == TypingStates.STOPPED:
            return 'stopped'
        else:
            return 'not set'

    def __update_body__(self) -> None:
        """
        Update the body based on the current action.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__update_body__.__name__)
        if self.sender is not None and self.action is not None and self.time_changed is not None:
            if self.recipient is not None and self.recipient_type is not None:
                if self.recipient_type == RecipientTypes.CONTACT:
                    self.body = "At %s, %s %s typing." % (
                        self.time_changed.get_display_time(), self.sender.get_display_name(),
                        self.__get_action_string__())
                elif self.recipient_type == RecipientTypes.GROUP:
                    self.body = "At %s, %s %s typing in group %s." % (
                        self.time_changed.get_display_time(), self.sender.get_display_name(),
                        self.__get_action_string__(), self.recipient.get_display_name())
                else:
                    error_message: str = "invalid recipient_type: %s" % str(self.recipient_type)
                    logger.critical("Raising ValueError(%s)." % error_message)
                    raise ValueError(error_message)
        else:
            self.body = "Invalid typing message."
        return

