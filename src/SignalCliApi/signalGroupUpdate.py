#!/usr/bin/env python3
"""
File: signalGroupUpdate.py
Store and handle a group update message.
"""
from typing import Optional
import socket

from .signalCommon import MessageTypes
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroups import Groups
from .signalMessage import Message


class GroupUpdate(Message):
    """
    Class for a group update message.
    """
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
                 ) -> None:
        # No argument checks required. Body is created.
        # Set external properties:
        self.body: str = ''
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, None, None, None, None, MessageTypes.GROUP_UPDATE)
        # Generate the body.
        self.__updateBody__()
        return

    def __updateBody__(self) -> None:
        """
        Update the body of the message to reflect the change that was made.
        :return: None
        """
        if self.sender is not None and self.recipient is not None:
            self.body = "At %s, %s updated the group %s." % (self.timestamp.get_display_time(),
                                                             self.sender.get_display_name(),
                                                             self.recipient.get_display_name()
                                                             )
        else:
            self.body = "Invalid group update."
        return
