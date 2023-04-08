#!/usr/bin/env python3
"""File: signalCallMessage.py"""
from typing import Optional, Any
import socket
from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message

DEBUG: bool = False


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
                 sdp: Optional[object] = None,
                 call_type: Optional[str] = None,
                 opaque: Optional[str] = None,
                 ) -> None:
        # Type check arguments:
        if offer_id is not None and not isinstance(offer_id, int):
            __type_error__("offer_id", "Optional[int]", offer_id)
        if sdp is not None and not isinstance(sdp, object):
            __type_error__("sdp", "Optional[object]", sdp)  # NOTE: Shouldn't get here, this is here as a placeholder
            #                                                until I know the type returned by signal.
        if call_type is not None and not isinstance(call_type, str):
            __type_error__("call_type", "Optional[str]", call_type)
        if opaque is not None and not isinstance(opaque, str):
            __type_error__("opaque", "Optional[str]", opaque)
        # Set external properties:
        self.offer_id: Optional[int] = offer_id
        self.sdp: Optional[object] = sdp
        self.call_type: Optional[str] = call_type
        self.opaque: Optional[str] = opaque
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, this_device, None, Message.TYPE_CALL_MESSAGE)
        # Mark this as delivered:
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)

        return

    ###############################
    # Init:
    ###############################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        offer_message: dict[str, object] = raw_message['callMessage']['offerMessage']
        self.offer_id = offer_message['id']
        self.sdp = offer_message['sdp']
        self.call_type = offer_message['type']
        self.opaque = offer_message['opaque']
        return

    ###############################
    # To / From dict:
    ###############################
    def __to_dict__(self) -> dict:
        call_message_dict: dict[str, object] = super().__to_dict__()
        call_message_dict['offerId'] = self.offer_id
        call_message_dict['sdp'] = self.sdp
        call_message_dict['type'] = self.call_type
        call_message_dict['opaque'] = self.opaque
        return call_message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        self.offer_id = from_dict['offerId']
        self.sdp = from_dict['sdp']
        self.call_type = from_dict['type']
        self.opaque = from_dict['opaque']
        return
