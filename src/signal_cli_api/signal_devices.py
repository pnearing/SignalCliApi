#!/usr/bin/env python3
"""
File: signal_devices.py
Handle a list of Devices.
"""
# pylint: disable=R0913
from typing import Optional, Any, Iterator
import json
import socket
import logging

from .signal_common import (__socket_receive_blocking__, __socket_send__, __type_error__,
                            __parse_signal_response__, __check_response_for_error__,
                            UNKNOWN_DEVICE_NAME)
from .signal_device import SignalDevice
from .signal_timestamp import SignalTimestamp
# from .signal_exceptions import SignalError


class SignalDevices:
    """An object containing the devices list."""
    def __init__(self,
                 sync_socket: socket.socket,
                 account_id: str,
                 this_device: Optional[int] = None,
                 from_dict: Optional[dict[str, Any]] = None,
                 do_sync: bool = False,
                 ) -> None:
        """
        Initialize devices:
        :param sync_socket: socket.socket: The socket to use for syncing.
        :param account_id: str, The account ID.
        :param this_device: Optional[int]: The device we're currently using.
        :param from_dict: Optional[dict[str, Any]]: Load this device from the given dict created
            by __to_dict__()
        :param do_sync: bool: Sync the device info with signal, defaults to False
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checking:
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if this_device is not None and not isinstance(this_device, int):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "Optional[int]", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if not isinstance(do_sync, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_sync", "bool", do_sync)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to preform sync operations with."""
        self._account_id: str = account_id
        """This account id."""
        self._this_device: int = this_device
        """The device we're currently using."""
        self._devices: list[SignalDevice] = []
        """The list of devices."""

        # Parse from dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)

        # Load devices from signal:
        elif do_sync:
            logger.debug("Syncing with signal.")
            self.__sync__()

    ###############################
    # Overrides:
    ###############################
    def __iter__(self) -> Iterator:
        """
        Iterate over the devices in the list.
        :return: Iterator.
        """
        return iter(self._devices)

    def __len__(self) -> int:
        """
        Get the number of devices.
        :return: int: The length of self._devices.
        """
        return len(self._devices)

    ###############################
    # To / From dict:
    ###############################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Generate a JSON friendly dict.
        :return: dict[str, Any]: The JSON friendly dict to pass to __from_dict__()
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__to_dict__.__name__)
        devices_dict: dict[str, Any] = {
            'devices': []
        }
        device_count: int = 0
        for device in self._devices:
            devices_dict['devices'].append(device.__to_dict__())
            device_count += 1
        # logger.debug("Added %i devices to dict." % device_count)
        return devices_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load SignalDevices from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)
        self._devices = []
        device_count: int = 0
        for device_dict in from_dict['devices']:
            device = SignalDevice(sync_socket=self._sync_socket, account_id=self._account_id,
                                  this_device=self._this_device, from_dict=device_dict)
            self._devices.append(device)
            device_count += 1
        logger.debug("Loaded %i devices from dict.", device_count)

    ##############################
    # Sync with signal:
    ##############################
    def __sync__(self) -> None:
        """
        Sync devices with signal.
        :return: None
        :raises CommunicationError: On error communicating with signal.
        :raises InvalidServerResponse: On JSON decode error of server response.
        :raises SignalError: On signal returning an error.
        """
        # Setup logging:
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__sync__.__name__)

        # Create list devices command Obj:
        list_devices_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listDevices",
            'params': {'account': self._account_id}
        }

        # Create json command string
        json_command = json.dumps(list_devices_command_obj) + '\n'

        # Communicate with the socket:
        __socket_send__(self._sync_socket, json_command)  # Raises CommunicationsError.
        # Raises CommunicationsError:
        response_string = __socket_receive_blocking__(self._sync_socket)
        # Raises InvalidServerResponse:
        response_obj: dict[str, Any] = __parse_signal_response__(response_string)
        __check_response_for_error__(response_obj)  # Raises Signal Error on any error

        # Parse devices response:
        for raw_device in response_obj['result']:
            new_device = SignalDevice(sync_socket=self._sync_socket, account_id=self._account_id,
                                      this_device=self._this_device,
                                      raw_device=raw_device)
            # Check for an existing device:
            device_found = False
            for device in self._devices:
                if device == new_device:
                    device.__merge__(new_device)
                    device_found = True
            # Add the device if not found:
            if not device_found:
                self._devices.append(new_device)

    #################################
    # Helpers:
    #################################
    def __get_or_add__(self,
                       device_id: int,
                       name: str = UNKNOWN_DEVICE_NAME
                       ) -> tuple[bool, SignalDevice]:
        """
        Get a device from the device list, or if not found, add it to the device list.
        :param device_id: int: The device ID.
        :param name: str: The name of the device; Defaults to UNKNOWN_DEVICE_NAME
        :return: tuple[bool, SignalDevice]: The first element is if the device was added to the
            device list; And the second element is the existing device if found, or the new device
            if not found.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__get_or_add__.__name__)
        for device in self._devices:
            if device.id == device_id:
                logger.debug("Device found.")
                return False, device
        device = SignalDevice(sync_socket=self._sync_socket,
                              account_id=self._account_id,
                              this_device=self._this_device,
                              device_id=device_id,
                              name=name,
                              created=SignalTimestamp(now=True))
        self._devices.append(device)
        logger.debug("Device created and added.")
        return True, device

    ########################
    # Getters:
    ########################
    def get_this_device(self) -> Optional[SignalDevice]:
        """
        Get the device associated with the current account.
        :returns: Optional[SignalDevice]: Returns the device, or None if not found, which would
            happen for the devices of a contact.
        """
        for device in self._devices:
            if device.is_this_device:
                return device
        return None
