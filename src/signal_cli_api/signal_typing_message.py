#!/usr/bin/env python3
"""
File: signal_typing_message.py
Store and handle a typing message.
"""
# pylint: disable=R0913, R0914
import logging
from typing import Optional, Any
import socket

from .signal_common import RecipientTypes, MessageTypes, TypingStates, __type_error__
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_groups import SignalGroups
from .signal_message import SignalMessage
from .signal_recipient import SignalRecipient
from .signal_timestamp import SignalTimestamp


class SignalTypingMessage(SignalMessage):
    """Class to store a typing message."""
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
                 recipient: Optional[SignalRecipient] = None,
                 device: Optional[SignalDevice] = None,
                 timestamp: Optional[SignalTimestamp] = None,
                 action: TypingStates = TypingStates.NOT_SET,
                 time_changed: Optional[SignalTimestamp] = None,
                 ) -> None:
        """
        Initialize a Typing Message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object that represents the device
            we're on.
        :param from_dict: Optional[dict[str, Any]]: The dict created to __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: A dict provided by Signal.
        :param sender: Optional[SignalContact]: The sender of this message.
        :param recipient: Optional[SignalContact | SignalGroup]: The recipient of the message.
        :param device: Optional[SignalDevice]: The device that generated this message.
        :param timestamp: Optional[SignalTimestamp]: The timestamp of this message.
        :param action: TypingStates: The typing state, either started or stopped.
        :param time_changed: Optional[SignalTimestamp]: The time the typing state changed.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type check parameters:
        if not isinstance(action, TypingStates):
            logger.critical("Raising TypeError:")
            __type_error__('action', 'TypingStates', action)

        if time_changed is not None and not isinstance(time_changed, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__('time_changed', 'Optional[SignalTimestamp]', time_changed)

        # Set external properties:
        # The typing action:
        self._action: TypingStates = action
        """The action being preformed. Either STARTED or STOPPED."""
        # The time the typing action changed.
        self.time_changed: Optional[SignalTimestamp] = time_changed
        """The SignalTimestamp of the action change."""

        # Run super:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, sender, recipient, device, timestamp,
                         MessageTypes.TYPING)

        # update body:
        self.__update_body__()

        # Mark as delivered, read, and viewed.
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)
            self.mark_read(self.timestamp)
            self.mark_viewed(self.timestamp)

    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by Signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        super().__from_raw_message__(raw_message)
        typing_dict: dict[str, Any] = raw_message['typingMessage']
        if typing_dict['action'] == 'STARTED':
            self.action = TypingStates.STARTED
        elif typing_dict['action'] == 'STOPPED':
            self.action = TypingStates.STOPPED
        else:
            self.action = TypingStates.NOT_SET
        self.time_changed = SignalTimestamp(timestamp=typing_dict['timestamp'])
        if 'groupId' in typing_dict.keys():
            group = self._groups.get_by_id(typing_dict['groupId'])
            if group is not None:
                self._recipient = group

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
            self.time_changed = SignalTimestamp(from_dict=from_dict['timeChanged'])

    def __get_action_string__(self) -> str:
        """
        Return a string for the action.
        :return: str: The action string.
        """
        if self.action == TypingStates.STARTED:
            return 'started'
        if self.action == TypingStates.STOPPED:
            return 'stopped'
        return 'not set'

    def __update_body__(self) -> None:
        """
        Update the body based on the current action.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__update_body__.__name__)
        if self.sender is not None and self.action is not None and self.time_changed is not None:
            if self.recipient is not None and self.recipient_type is not None:
                if self.recipient_type == RecipientTypes.CONTACT:
                    self.body = (f"At {self.time_changed.get_display_time()}, "
                                 f"{self.sender.get_display_name()} {self.__get_action_string__()} "
                                 f"typing.")
                elif self.recipient_type == RecipientTypes.GROUP:
                    self.body = (f"At {self.time_changed.get_display_time()}, "
                                 f"{self.sender.get_display_name()} "
                                 f"{self.__get_action_string__()} typing in "
                                 f"group {self.recipient.get_display_name()}.")
                else:
                    error_message: str = f"invalid recipient_type: {self.recipient_type}"
                    logger.critical("Raising ValueError(%s).", error_message)
                    raise ValueError(error_message)
        else:
            self.body = "Invalid typing message."

#################################################
# Properties:
#################################################
    @property
    def action(self) -> TypingStates:
        """
        Get the action this typing message represents.
        :return: TypingStates: The typing state.
        """
        return self._action

    @action.setter
    def action(self, value: TypingStates | int) -> None:
        """
        Set the action this typing message represents.
        :param value: TypingStates | int: The value to set it to.
        :return: None
        :raises ValueError: If value out of range.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.action.Setter')
        if not isinstance(value, (TypingStates, int)):
            logger.critical("Raising TypeError:")
            __type_error__('value', 'TypingStates | int', value)
        self._action = TypingStates(value)
