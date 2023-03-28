#!/usr/bin/env python3
"""File: signalCallMessage.py"""
from typing import Optional, Any
import socket

from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message


class CallMessage(Message):
    """Class to store a call message."""

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
                 offer_id: Optional[int] = None,
                 sdp: Optional[Any] = None,
                 call_type: str = '',
                 opaque: str = '',
                 ) -> None:
        # TODO: Type check arguments:
        # Set external properties:
        self.offer_id: Optional[int] = offer_id
        self.sdp: Optional[Any] = sdp
        self.call_type: str = call_type
        self.opaque: str = opaque
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, this_device, None, Message.TYPE_CALL_MESSAGE)
        return

    ###############################
    # Init:
    ###############################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        offer_message: dict[str, object] = raw_message['callMessage']['offerMessage']

