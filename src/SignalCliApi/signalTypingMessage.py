#!/usr/bin/env python3

from typing import Optional, Iterable
import sys
import socket

from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMention import Mention
from .signalMessage import Message
from .signalReaction import Reaction
from .signalSticker import Sticker
from .signalTimestamp import Timestamp
DEBUG: bool = False


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
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 action: Optional[str] = None,
                 time_changed: Optional[Timestamp] = None,
                 ) -> None:
        # Arg Checks:
        # Check action
        if action is not None:
            if not isinstance(action, str):
                __type_error__("action", 'str', action)
            action = action.upper()
            if action != 'STARTED' and action != 'STOPPED':
                raise ValueError("action must be either STARTED or STOPPED")
        # Check time changed:
        if time_changed is not None and not isinstance(time_changed, Timestamp):
            __type_error__("time_changed", "Timestamp", time_changed)
        # Set external properties:
        self.action: str = action
        self.time_changed: Timestamp = time_changed
        self.body: str = ''
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_TYPING_MESSAGE)
        # update body:
        self.__update_body__()
        return

    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        typing_dict: dict[str, object] = raw_message['typingMessage']
        self.action = typing_dict['action']
        self.time_changed = Timestamp(timestamp=typing_dict['timestamp'])
        return

    def __to_dict__(self) -> dict:
        typing_message = super().__to_dict__()
        typing_message['action'] = self.action
        if self.time_changed is not None:
            typing_message['time_changed'] = self.time_changed.__to_dict__()
        else:
            typing_message['time_changed'] = None
        return typing_message

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        self.action = from_dict['action']
        if from_dict['time_changed'] is not None:
            self.time_changed = Timestamp(from_dict=from_dict['time_changed'])
        else:
            self.time_changed = None
        return

    def __update_body__(self) -> None:
        if self.sender is not None and self.action is not None and self.time_changed is not None:
            if self.recipient is not None and self.recipient_type is not None:
                if self.recipient_type == 'contact':
                    self.body = "At %s, %s %s typing." % (
                        self.time_changed.get_display_time(), self.sender.get_display_name(),
                        self.action.lower())
                elif self.recipient_type == 'group':
                    self.body = "At %s, %s %s typing in group %s." % (
                        self.time_changed.get_display_time(), self.sender.get_display_name(),
                        self.action.lower(), self.recipient.get_display_name())
                else:
                    raise ValueError("invalid recipient_type: %s" % self.recipient_type)
        else:
            self.body = "Invalid typing message."
