#!/usr/bin/env python3

from typing import Optional
import json
import socket

from .signalCommon import __socket_receive__, __socket_send__, __type_error__
from .signalDevice import Device
from .signalTimestamp import Timestamp
DEBUG: bool = False


class Devices(object):
    """An object containing the devices list."""
    def __init__(self,
                 sync_socket: socket.socket,
                 account_id: str,
                 account_device: Optional[int] = None,
                 from_dict: Optional[dict] = None,
                 do_sync: bool = False,
                 ) -> None:
        # Argument checking:
        if not isinstance(sync_socket, socket.socket):
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(account_id, str):
            __type_error__("account_id", "str", account_id)
        if account_device is not None and not isinstance(account_device, int):
            __type_error__("account_device", "Optional[int]", account_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if not isinstance(do_sync, bool):
            __type_error__("do_sync", "bool", do_sync)
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._account_id: str = account_id
        self._account_device: int = account_device
        self._devices: list[Device] = []
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Load devices from signal:
        elif do_sync:
            self.__sync__()
        return

    ###############################
    # To / From dict:
    ###############################
    def __to_dict__(self) -> dict:
        devices_dict = {
            'devices': []
        }
        for device in self._devices:
            devices_dict['devices'].append(device.__to_dict__())
        return devices_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self._devices = []
        for device_dict in from_dict['devices']:
            device = Device(sync_socket=self._sync_socket, account_id=self._account_id,
                            account_device=self._account_device,
                            from_dict=device_dict)
            self._devices.append(device)
        return

    ##############################
    # Sync with signal:
    ##############################
    def __sync__(self) -> bool:
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
        __socket_send__(self._sync_socket, json_command)
        response_string = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_string)
        # Check for error:
        if 'error' in response_obj.keys():
            return False
        # Parse devices:
        for raw_device in response_obj['result']:
            new_device = Device(sync_socket=self._sync_socket, account_id=self._account_id,
                                account_device=self._account_device,
                                raw_device=raw_device)
            # Check for existing device:
            device_found = False
            for device in self._devices:
                if device.id == new_device.id:
                    device.__merge__(new_device)
                    device_found = True
            # Add device if not found:
            if not device_found:
                self._devices.append(new_device)
        return True

    #################################
    # Helpers:
    #################################
    def __get_or_add__(self, name: str, device_id: int) -> tuple[bool, Device]:
        for device in self._devices:
            if device.id == device_id:
                return False, device
        device = Device(sync_socket=self._sync_socket, account_id=self._account_id, account_device=self._account_device,
                        device_id=device_id, name=name, created=Timestamp(now=True))
        self._devices.append(device)
        return True, device

    ########################
    # Getters:
    ########################
    def get_account_device(self) -> Optional[Device]:
        """
        Get the device associated with the current account.
        :returns: Optional[Device]: Returns the device, or None if not found, which would happen for the devices of a
                                    contact.
        """
        for device in self._devices:
            if device.is_account_device:
                return device
        return None
