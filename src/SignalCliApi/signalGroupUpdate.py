#!/usr/bin/env python3
from typing import Optional
import socket

from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalTimestamp import Timestamp
DEBUG: bool = False


class GroupUpdate(Message):
    """Class for a group update message."""
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
                 is_delivered: bool = False,
                 time_delivered: Optional[Timestamp] = None,
                 is_read: bool = False,
                 time_read: Optional[Timestamp] = None,
                 is_viewed: bool = False,
                 time_viewed: Optional[Timestamp] = None
                 ) -> None:
        # No argument checks required. Body is created.
        # Set external properties:
        self.body: str = ''
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_GROUP_UPDATE_MESSAGE,
                         is_delivered, time_delivered, is_read, time_read, is_viewed, time_viewed)
        self.__updateBody__()
        return

    def __updateBody__(self) -> None:
        if self.sender is not None and self.recipient is not None:
            self.body = "At %s, %s updated the group %s." % (
                self.timestamp.get_display_time(),
                self.sender.get_display_name(),
                self.recipient.get_display_name()
            )
        else:
            self.body = "Invalid group update."
        return