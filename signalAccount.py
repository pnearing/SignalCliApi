#!/usr/bin/env python3

from typing import Optional
import os
import json
import sys
import socket

from .signalCommon import __socket_receive__, __socket_send__
from .signalDevice import Device
from .signalDevices import Devices
from .signalContacts import Contacts
from .signalGroups import Groups
from .signalMessages import Messages
from .signalProfile import Profile
from .signalSticker import StickerPacks

DEBUG: bool = False


class Account(object):
    supportedAccountFileVersion: int = 6

    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 signal_account_path: str = None,
                 do_load: bool = False,
                 number: Optional[str] = None,
                 uuid: Optional[str] = None,
                 device_id: Optional[int] = None,
                 device: Optional[Device] = None,
                 registered: bool = False,
                 config: Optional[dict] = None,
                 devices: Optional[Devices] = None,
                 contacts: Optional[Contacts] = None,
                 groups: Optional[Groups] = None,
                 profile: Optional[Profile] = None,
                 ) -> None:
        # TODO: Argument checks:
        # Set internal Vars:
        self._sync_socket: socket.socket = sync_socket
        self._command_socket: socket.socket = command_socket
        self.config_path: str = config_path
        self._sticker_packs: StickerPacks = sticker_packs
        self._account_path: str = os.path.join(config_path, 'data', signal_account_path + '.d')
        self._account_file_path: str = os.path.join(config_path, 'data', signal_account_path)
        # Set external properties:
        self.number: str = number
        self.uuid: str = uuid
        self.device_id: int = device_id
        self.device: Device = device
        self.registered: bool = registered
        self.config: Optional[dict] = config
        self.devices: Optional[Devices] = devices
        self.contacts: Optional[Contacts] = contacts
        self.groups: Optional[Groups] = groups
        self.profile: Optional[Profile] = profile
        # Do load:
        if do_load:
            self.__do_load__()
        # If the account is registered load account data from signal:
        if self.registered:
            # Load devices from signal:
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self.number, account_device=self.device_id,
                                   do_sync=True)
            # Set this device:
            self.device = self.devices.get_account_device()
            # Load contacts from signal:
            self.contacts = Contacts(sync_socket=self._sync_socket, config_path=self.config_path, account_id=self.number,
                                     account_path=self._account_path, do_load=True, do_sync=True)
            # Load groups from signal:
            self.groups = Groups(sync_socket=self._sync_socket, config_path=self.config_path, account_id=self.number,
                                 account_contacts=self.contacts, do_sync=True)
            # Load messages from file:
            self.messages = Messages(command_socket=self._command_socket, config_path=self.config_path,
                                     account_id=self.number, account_path=self._account_path, contacts=self.contacts,
                                     groups=self.groups, devices=self.devices,
                                     this_device=self.devices.get_account_device(),
                                     sticker_packs=self._sticker_packs, do_load=True)
            # Load profile from file and merge self contact.
            self.profile = Profile(sync_socket=self._sync_socket, config_path=self.config_path, account_id=self.number,
                                   contact_id=self.number, account_path=self._account_path, do_load=True,
                                   is_account_profile=True)
            self_contact = self.contacts.get_self()
            self.profile.__merge__(self_contact.profile)
        else:
            # Set devices to None:
            self.devices = None
            # Set this device to None:
            self.device = None
            # Set contacts to None:
            self.contacts = None
            # Set groups to None
            self.groups = None
            # Set messages to None
            self.messages = None
            # Set profile to None
            self.profile = None
        return

    def __do_load__(self) -> None:
        # Try to open the file for reading:
        try:
            file_handle = open(self._account_file_path, 'r')
        except Exception as e:
            error_message = "FATAL: Couldn't open '%s' for reading: %s" % (self._account_file_path, str(e.args))
            raise RuntimeError(error_message)
        # Try to load the json from the file:
        try:
            raw_account: dict = json.loads(file_handle.read())
        except json.JSONDecodeError as e:
            error_message = "FATAL: Failed to load json from '%s': %s" % (self._account_file_path, e.msg)
            raise RuntimeError(error_message)
        # Version check account file:
        if (raw_account['version'] > 6):
            error_message = "WARNING: Account detail file %s is of a different supported version. This may cause things to break."
            print(error_message, file=sys.stderr, flush=True)
        # Set the properties from the account json:
        self.number = raw_account['username']
        self.uuid = raw_account['uuid']
        self.device_id = raw_account['device_id']
        self.registered = raw_account['registered']
        self.config = raw_account['configurationStore']
        return

    ##########################
    # Methods:
    ##########################
    def verify(self, code: str, pin: str | None = None) -> tuple[bool, str]:
        # Create verify command object:
        verify_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "verify",
            "params": {
                "account": self.number,
                "verificationCode": code,
            }
        }
        if pin is not None:
            verify_command_obj['params']['pin'] = pin
        json_command_str = json.dumps(verify_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "ERROR: Signal error, code: %i, message: %s" % (
                response_obj['error']['code'], response_obj['error']['message'])
            if DEBUG:
                print(error_message, file=sys.stderr)
            return False, error_message
        print(response_obj)

        return True, "verification successful"
