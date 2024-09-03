#!/usr/bin/env python3
"""
File: signal_group_update.py
Store and handle a group update message.
"""
# pylint: disable=R0913
from typing import Optional
import socket

from .signal_common import MessageTypes
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_groups import SignalGroups
from .signal_message import SignalMessage


class SignalGroupUpdate(SignalMessage):
    """
    Class for a group update message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 this_device: SignalDevice,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 ) -> None:
        # No argument checks required. Body is created.
        # Set external properties:
        self.body: str = ''
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, None, None, None,
                         None, MessageTypes.GROUP_UPDATE)
        # Generate the body.
        self.__update_body__()

    def __update_body__(self) -> None:
        """
        Update the body of the message to reflect the change that was made.
        :return: None
        """
        if self.sender is not None and self.recipient is not None:
            self.body = (f"At {self.timestamp.get_display_time()}, "
                         f"{self.sender.get_display_name()} "
                         f"updated the group {self.recipient.get_display_name()}.")
        else:
            self.body = "Invalid group update."
