#!/usr/bin/env python3
"""
File: signal_call_message.py
"""
# pylint: disable=R0913, W0511
import logging
from typing import Optional, Any
import socket
from .signal_common import MessageTypes #, __type_error__
# from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
# from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_message import SignalMessage


class SignalCallMessage(SignalMessage):
    """
    Class to store a call message.
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
                 ) -> None:
        """
        Initialize a call message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This account's ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts SignalContacts object.
        :param groups: SignalGroups: This accounts SignalGroups object.
        :param devices: SignalDevices: This accounts SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object for the device we're using.
        :param from_dict: dict[str, Any]: Load properties from a dict created by __to_dict__()
        :param raw_message:  dict[str, Any]: Load properties from a dict provided by signal.
        """
        # Setup logging:
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Set external properties:
        self.offer_id: Optional[int] = None
        self.sdp: Optional[Any] = None
        self.call_type: Optional[str] = None
        self.opaque: Optional[str] = None

        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, None, None, None, None,
                         MessageTypes.CALL)

        # Mark this as delivered:
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)

    ###############################
    # Init:
    ###############################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict created by signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        logger = logging.Logger = logging.getLogger(__name__ + '.' +
                                                    self.__from_raw_message__.__name__)
        super().__from_raw_message__(raw_message)
        logger.debug(raw_message)
        # TODO: THIS HAS CHANGED:

        # offer_message: dict[str, object] = raw_message['callMessage']['offerMessage']
        # self.offer_id = offer_message['id']
        # self.sdp = offer_message['sdp']
        # self.call_type = offer_message['type']
        # self.opaque = offer_message['opaque']


    ###############################
    # To / From dict:
    ###############################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Generate a JSON friendly dict for this message.
        :return: dict[str, Any]: The dict to provide to __from_dict__()
        """
        call_message_dict: dict[str, Any] = super().__to_dict__()
        call_message_dict['offerId'] = self.offer_id
        call_message_dict['sdp'] = self.sdp
        call_message_dict['type'] = self.call_type
        call_message_dict['opaque'] = self.opaque
        return call_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict to load from.
        :return: None
        """
        super().__from_dict__(from_dict)
        self.offer_id = from_dict['offerId']
        self.sdp = from_dict['sdp']
        self.call_type = from_dict['type']
        self.opaque = from_dict['opaque']
