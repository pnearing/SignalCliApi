#!/usr/bin/env python3
"""
File: signalAccount.py
Store account information.
"""
from typing import Optional, Any, TextIO
import os
import json
import socket
import logging

from .signalCommon import __socket_receive__, __socket_send__, __type_error__, __type_err_msg__
from .signalDevice import Device
from .signalDevices import Devices
from .signalContacts import Contacts
from .signalGroups import Groups
from .signalMessages import Messages
from .signalProfile import Profile
from .signalSticker import StickerPacks
from .signalTimestamp import Timestamp
from .signalExceptions import InvalidServerResponse, InvalidDataFile, UnsupportedVersion


class Account(object):
    """Class to store an account."""
    supportedAccountFileVersions: tuple[int, int] = (5, 6, 8)
    """Supported account detail file versions."""

    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 signal_account_path: str,
                 environment: str,
                 number: str,
                 uuid: str,
                 do_load: bool = False,
                 device: Optional[Device] = None,
                 devices: Optional[Devices] = None,
                 contacts: Optional[Contacts] = None,
                 groups: Optional[Groups] = None,
                 profile: Optional[Profile] = None,
                 ) -> None:
        """
        Initialize the Account.
        :param sync_socket: The sync socket.
        :param command_socket: The command socket.
        :param config_path: The path to the config directory.
        :param sticker_packs: The sticker packs object.
        :param signal_account_path: The filename of the account details file.
        :param environment: The environment variable from accounts.json.
        :param number: The phone number of the account.
        :param uuid: The UUID of the account.
        :param do_load: True, load the account from the account detail file, False do not load.
        :param device: Optional: The Device object for this account.
        :param devices: Optional: The Devices object for this account.
        :param contacts: Optional: The Contacts object for this account.
        :param groups: Optional: The Groups object for this account.
        :param profile: Optional: The Profile object for this account.
        :raises TypeError: If a parameter is of invalid type.
        :raises InvalidDataFile: If a file contains invalid JSON or a KeyError occurs during loading.
        """
        # Setup logging:
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Initialize.")
        # Argument checks:
        self.logger.debug("Argument checks...")
        if not isinstance(sync_socket, socket.socket):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('sync_socket', 'socket.socket', sync_socket))
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(command_socket, socket.socket):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('command_socket', 'socket.socket', command_socket))
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('config_path', 'str', config_path))
            __type_error__("config_path", "str", config_path)
        if not isinstance(sticker_packs, StickerPacks):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('sticker_packs', 'StickerPacks', sticker_packs))
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(signal_account_path, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__("signal_account_path", 'str', signal_account_path))
            __type_error__("signal_account_path", "str", signal_account_path)
        if not isinstance(environment, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('environment', 'str', environment))
        if number is not None and not isinstance(number, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('number', 'str', number))
            __type_error__("number", "str", number)
        if uuid is not None and not isinstance(uuid, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('uuid', 'Optional[str]', uuid))
            __type_error__("uuid", "str", uuid)
        if not isinstance(do_load, bool):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('do_load', 'bool', do_load))
            __type_error__("do_load", "bool", do_load)
        if device is not None and not isinstance(device, Device):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('device', 'Optional[Device]', device))
            __type_error__("device", "Optional[Device]", device)
        if devices is not None and not isinstance(devices, Devices):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('devices', 'Optional[Devices', devices))
            __type_error__("devices", "Optional[Devices]", devices)
        if contacts is not None and not isinstance(contacts, Contacts):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('contacts', 'Optional[Contacts]', contacts))
            __type_error__("contacts", "Optional[Contacts]", contacts)
        if groups is not None and not isinstance(groups, Groups):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('groups', 'Optional[Groups]', groups))
            __type_error__("groups", "Optional[Groups]", groups)
        if profile is not None and not isinstance(profile, Profile):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('profile', 'Optional[Profile]', profile))
            __type_error__("profile", "Optional[Profile]", profile)

        # Set internal Vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket for sync operations."""
        self._command_socket: socket.socket = command_socket
        """The socket for command operations."""
        self.config_path: str = config_path
        """The path to the signal-cli config directory."""
        self._sticker_packs: StickerPacks = sticker_packs
        """Known sticker packs."""
        self._account_path: str = os.path.join(config_path, 'data', signal_account_path + '.d')
        """The path to the signal-cli account data directory."""
        self._account_file_path: str = os.path.join(config_path, 'data', signal_account_path)
        """The path to the account detailed account file."""

        # Set external properties:
        self.environment: str = environment
        """The 'environment' from accounts.json."""
        self.number: str = number
        """The account phone number."""
        self.uuid: str = uuid
        """The account uuid."""

        # Set external object refs:
        self.device: Optional[Device] = device
        """The Device object."""
        self.devices: Optional[Devices] = devices
        """The account Devices object."""
        self.contacts: Optional[Contacts] = contacts
        """The account Contacts object."""
        self.groups: Optional[Groups] = groups
        """The account Groups object."""
        self.profile: Optional[Profile] = profile
        """The account Profile object."""

        # Version:
        self.version: Optional[int] = None
        """The account detail version."""
        # Version 5 info:
        self.registered: Optional[bool] = None
        """Is this account fully registered?"""
        self.username: Optional[str] = None
        """The username of the account."""
        self.service_environment: Optional[str] = None
        """The 'service environment' from the account detail file."""
        self.pni: Optional[str] = None
        """I don't know."""
        self.device_name: Optional[str] = None
        """This device name?"""
        self.device_id: Optional[int] = None
        """This device ID"""
        self.is_multi_device: Optional[bool] = None
        """Does this account have multiple devices?"""
        self.last_received_timestamp: Optional[Timestamp] = None
        """Timestamp object of the last time a message was received."""
        self.password: Optional[str] = None
        """Password?"""
        self.registration_id: Optional[int] = None
        """I don't know."""
        self.pni_registration_id: Optional[int] = None
        """I don't know."""
        self.identity_private_key: Optional[str] = None
        """I don't know."""
        self.identity_key: Optional[str] = None
        """I don't know."""
        self.pni_identity_private_key: Optional[str] = None
        """I don't know."""
        self.pni_identity_key: Optional[str] = None
        """I don't know."""
        self.registration_lock_pin: Optional[str] = None
        """The registration lock pin."""
        self.pin_master_key: Optional[str] = None
        """I don't know."""
        self.storage_key: Optional[Any] = None  # TODO: Figure out type.
        """I don't know."""
        self.storage_manifest_version: Optional[Any] = None  # TODO: Figure out type.
        """I don't know."""
        self.pre_key_id_offset: Optional[int] = None
        """I don't know."""
        self.next_signed_pre_key_id: Optional[int] = None
        """I don't know."""
        self.pni_pre_key_id_offset: Optional[int] = None
        """I don't know."""
        self.pni_next_signed_pre_key_id: Optional[int] = None
        """I don't know."""
        self.configuration_store: Optional[dict[str, bool | str]] = None
        """Signal configuration options."""
        # Version 6 info:
        self.profile_key: Optional[str] = None
        """I don't know."""
        # Version 8 info:
        self.encrypted_device_name: Optional[str] = None
        """Encrypted device name, might be device name from version 5."""
        self.aci_account_data: Optional[dict[str, int | str]] = None
        """I don't know."""
        self.pni_account_data: Optional[dict[str, int | str]] = None
        """I don't know."""

        # Do load:
        if do_load:
            self.__do_load__()
        # If the account is registered, load account data from signal:
        if self.registered:
            self.logger.info("Account is registered. Loading account data from signal.")

            # Load devices from signal:
            self.logger.debug("Loading Devices...")
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self.number, account_device=self.device_id,
                                   do_sync=True)
            # Set this device:
            self.device = self.devices.get_account_device()

            # Load contacts from signal:
            self.logger.debug("Loading Contacts...")
            self.contacts = Contacts(sync_socket=self._sync_socket, config_path=self.config_path,
                                     account_id=self.number, account_path=self._account_path, do_load=True,
                                     do_sync=True)

            # Load groups from signal:
            self.logger.debug("Loading Groups...")
            self.groups = Groups(sync_socket=self._sync_socket, config_path=self.config_path, account_id=self.number,
                                 account_contacts=self.contacts, do_sync=True)

            # Load messages from file:
            self.logger.debug("Loading messages from disk....")
            self.messages = Messages(command_socket=self._command_socket, config_path=self.config_path,
                                     account_id=self.number, account_path=self._account_path, contacts=self.contacts,
                                     groups=self.groups, devices=self.devices,
                                     this_device=self.devices.get_account_device(),
                                     sticker_packs=self._sticker_packs, do_load=True)

            # Load profile from file and merge self-contact.
            self.logger.debug("Loading Profile from disk...")
            self.profile = Profile(sync_socket=self._sync_socket, config_path=self.config_path, account_id=self.number,
                                   contact_id=self.number, account_path=self._account_path, do_load=True,
                                   is_account_profile=True)

            # Merge disk profile and self-contact profile.
            self.logger.debug("Merging account profiles...")
            self_contact = self.contacts.get_self()
            self.profile.__merge__(self_contact.profile)
        else:
            self.logger.info("Account not registered.")
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
        self.logger.info("Initialization complete.")
        return

    def __load_version_5__(self, raw_account: dict[str, Any]) -> None:
        """
        Load the version 5 properties.
        :param raw_account: The raw account dict loaded from the account detail file.
        :return: None
        :raises InvalidDataFile: On key error while loading the data.
        """
        self.logger.debug("Loading version 5 data...")
        try:
            self.number = raw_account['username']
            self.device_id = raw_account['deviceId']
            self.registered = raw_account['registered']
            self.username = raw_account['username']
            self.service_environment = raw_account['serviceEnvironment']
            self.uuid = raw_account['uuid']
            self.pni = raw_account['pni']
            self.device_name = raw_account['deviceName']
            self.is_multi_device = raw_account['isMultiDevice']
            self.last_received_timestamp = Timestamp(timestamp=raw_account['lastReceiveTimestamp'])
            self.password = raw_account['password']
            self.registration_id = raw_account['registrationId']
            self.pni_registration_id = raw_account['pniRegistrationId']
            self.identity_private_key = raw_account['identityPrivateKey']
            self.identity_key = raw_account['identityKey']
            self.pni_identity_private_key = raw_account['pniIdentityPrivateKey']
            self.pni_identity_key = raw_account['pniIdentityKey']
            self.registration_lock_pin = raw_account['registrationLockPin']
            self.pin_master_key = raw_account['pinMasterKey']
            self.storage_key = raw_account['storageKey']
            self.storage_manifest_version = raw_account['storageManifestVersion']
            self.pre_key_id_offset = raw_account['preKeyIdOffset']
            self.next_signed_pre_key_id = raw_account['nextSignedPreKeyId']
            self.pni_pre_key_id_offset = raw_account['pniPreKeyIdOffset']
            self.pni_next_signed_pre_key_id = raw_account['pniNextSignedPreKeyId']
            self.profile_key = raw_account['profileKey']
            self.configuration_store = raw_account['configurationStore']
        except KeyError as e:
            error_message: str = "KeyError while loading version 5 data: %s." % str(e.args)
            self.logger.critical("Raising InvalidDataFile(%s), File: %s" % (error_message, self._account_file_path))
            raise InvalidDataFile(error_message, e, self._account_file_path)
        self.logger.debug("Loaded.")
        return

    def __load_version_6__(self, raw_account: dict[str, Any]) -> None:
        """
        Load the version 6 account properties.
        :param raw_account: Version 6 account data.
        :return: None
        :raises InvalidDataFile: On KeyError while loading data.
        """
        self.logger.debug("Loading version 6 account data...")
        try:
            self.number = raw_account['username']
            self.username = raw_account['username']
            self.service_environment = raw_account['serviceEnvironment']
            self.uuid = raw_account['uuid']
            self.pni = raw_account['pni']
            self.device_name = raw_account['deviceName']
            self.device_id = raw_account['deviceId']
            self.is_multi_device = raw_account['isMultiDevice']
            self.last_received_timestamp = Timestamp(timestamp=raw_account['lastReceiveTimestamp'])
            self.password = raw_account['password']
            self.registration_id = raw_account['registrationId']
            self.identity_private_key = raw_account['identityPrivateKey']
            self.identity_key = raw_account['identityKey']
            self.pni_identity_private_key = raw_account['pniIdentityPrivateKey']
            self.pni_identity_key = raw_account['pniIdentityKey']
            self.registration_lock_pin = raw_account['registrationLockPin']
            self.pin_master_key = raw_account['pinMasterKey']
            self.storage_key = raw_account['storageKey']
            self.storage_manifest_version = raw_account['storageManifestVersion']
            self.pre_key_id_offset = raw_account['preKeyIdOffset']
            self.next_signed_pre_key_id = raw_account['nextSignedPreKeyId']
            self.pni_pre_key_id_offset = raw_account['pniPreKeyIdOffset']
            self.profile_key = raw_account['profileKey']
            self.registered = raw_account['registered']
            self.configuration_store = raw_account['configurationStore']
        except KeyError as e:
            error_message: str = "KeyError while loading version 6 data: %s." % str(e.args)
            self.logger.critical("Raising InvalidDataFile(%s). File: %s" % (error_message, self._account_file_path))
            raise InvalidDataFile(error_message, e, self._account_file_path)
        return

    def __load_version_8__(self, raw_account: dict[str, Any]) -> None:
        """
        Load version 8 account properties:
        :param raw_account: Raw account version 8 dict.
        :return: None
        :raises InvalidDataFile: If a KeyError occurs during the loading of data.
        """
        self.logger.debug("Loading version 8 data...")
        try:
            self.service_environment = raw_account['serviceEnvironment']
            self.registered = raw_account['registered']
            self.number = raw_account['number']
            self.username = raw_account['username']
            self.encrypted_device_name = raw_account['encryptedDeviceName']
            self.device_id = raw_account['deviceId']
            self.is_multi_device = raw_account['isMultiDevice']
            self.password = raw_account['password']
            self.aci_account_data = raw_account['aciAccountData']
            self.pni_account_data = raw_account['pniAccountData']
            self.registration_lock_pin = raw_account['registrationLockPin']
            self.pin_master_key = raw_account['pinMasterKey']
            self.storage_key = raw_account['storageKey']
            self.profile_key = raw_account['profileKey']
        except KeyError as e:
            error_message: str = "KeyError while loading version 8 data: %s." % str(e.args)
            self.logger.critical("Raising InvalidDataFile(%s). File: %s" % (error_message, self._account_file_path))
            raise InvalidDataFile(error_message, e, self._account_file_path)
        return

    def __do_load__(self) -> None:
        """
        Load the properties of the account from the account detail file.
        :return: None
        :raises RuntimeError: On error while opening file.
        :raises InvalidDataFile: On JSON Decode error.
        """
        # Load the account detail file:
        try:
            self.logger.debug("Loading detailed account data from %s." % self._account_file_path)
            file_handle: TextIO = open(self._account_file_path, 'r')  # Try to open the file for reading:
            raw_account: dict = json.loads(file_handle.read())  # Try to load the json from the file:
            file_handle.close()
        except (OSError, PermissionError, FileNotFoundError) as e:
            error_message: str = "Couldn't open '%s' for reading: %s" % (self._account_file_path, str(e.args))
            self.logger.critical(error_message)
            raise RuntimeError(error_message)
        except json.JSONDecodeError as e:
            error_message: str = "Failed to load JSON: %s" % e.msg
            self.logger.critical("Raising InvalidDataFile(%s). File: %s" % (error_message, self._account_file_path))
            raise InvalidDataFile(error_message, e, self._account_file_path)

        # Store and check version:
        self.version = raw_account['version']
        if self.version not in self.supportedAccountFileVersions:  # Currently 5, 6, and 8. I missed 7.
            error_message = "Account detail file '%s' is of version %i. Supported versions %s." \
                            % (self._account_file_path, raw_account['version'], str(self.supportedAccountFileVersions))
            self.logger.critical("Raising UnsupportedVersion(%s). File: %s" % (error_message, self._account_file_path))
            raise UnsupportedVersion(error_message, self.version, self.supportedAccountFileVersions)

        # Set the properties according to the version:
        if self.version == 5:
            self.__load_version_5__(raw_account)
        elif self.version == 6:
            self.__load_version_6__(raw_account)
        elif self.version == 8:
            self.__load_version_8__(raw_account)
        return

    ##########################
    # Methods:
    ##########################
    def verify(self, code: str, pin: Optional[str] = None) -> tuple[bool, str]:
        """
        Verify an account.
        :param code: str: The code sent via sms or voice call.
        :param pin: Optional[str]: The registered pin for this account.
        :returns: tuple[bool, str]: Boolean represents success or failure, str is an error message on failure, or
            "verification successful" on success.
        :raises InvalidServerResponse: On error decoding JSON.
        :raises CommunicationsError: On error during signal communications.
        """
        self.logger.info("Verify started.")
        # Create a verify command object:
        verify_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
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
        self.logger.debug("Sending JSON command: '%s'." % json_command_str.strip())
        __socket_send__(self._sync_socket, json_command_str)  # Raises CommunicationsError.
        response_str = __socket_receive__(self._sync_socket)  # Raises CommunicationsError.
        self.logger.debug("Got response: %s" % response_str.strip())
        # Parse response:
        try:
            response_obj: dict[str, Any] = json.loads(response_str)
        except json.JSONDecodeError as e:
            error_message: str = "Failed to decode json from server: %s." % e.msg
            raise InvalidServerResponse(error_message, e)
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "Signal error, code: %i, message: %s" % (
                response_obj['error']['code'], response_obj['error']['message'])
            self.logger.info('Verification failed.')
            self.logger.debug("Returning False: %s" % error_message)
            return False, error_message
        self.logger.info("Verification successful.")
        return True, "verification successful"
