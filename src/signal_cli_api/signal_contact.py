#!/usr/bin/env python3
"""
File: signal_contact.py
Store and manage a single contact.
"""
# pylint: disable=R0902, R0912, R0913, R0915, C0206
import logging
from datetime import timedelta
from typing import TypeVar, Optional, Any
import socket
import json

from .signal_common import (__type_error__, __socket_receive_blocking__, __socket_send__,
                            __parse_signal_response__, __check_response_for_error__,
                            UNKNOWN_CONTACT_NAME, SELF_CONTACT_NAME, TypingStates, RecipientTypes)
from .signal_profile import SignalProfile
from .signal_recipient import SignalRecipient
from .signal_timestamp import SignalTimestamp
from .signal_devices import SignalDevices

Self = TypeVar("Self", bound="SignalContact")


class SignalContact(SignalRecipient):
    """Class to store a contact."""

    def __init__(self,
                 command_socket: socket.socket,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_path: str,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_contact: Optional[dict[str, Any]] = None,
                 name: Optional[str] = None,
                 number: Optional[str] = None,
                 uuid: Optional[str] = None,
                 is_blocked: bool = False,
                 expiration: Optional[int | timedelta] = None,
                 color: Optional[str] = None,
                 ) -> None:
        """
        Initialize a SignalContact.
        :param command_socket: socket.socket: The socket to run commands with.
        :param sync_socket: socket.socket: The socket to run sync operations with.
        :param config_path: str: The full path to the signal-cli config directory.
        :param account_id: str: This account's ID.
        :param account_path: str: The path to this accounts data directory.
        :param from_dict: Optional[dict[str, Any]]: Load from a dict created by __to_dict__()
        :param raw_contact: Optional[dict[str, Any]]: Load from a dict provided by signal.
        :param name: Optional[str]: The name of this contact.
        :param number: Optional[str]: The phone number of this contact.
        :param uuid: Optional[str]: The UUID of the contact.
        :param is_blocked: bool: If this contact should be blocked.
        :param expiration: Optional[int | timedelta]: The expiration of this contact in seconds.
        :param color: Optional[str]: The colour of this contact.
        """
        # Super:
        super().__init__(recipient_type=RecipientTypes.CONTACT)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks:
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__('command_socket', 'socket.socket', command_socket)
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__('sync_socket', 'socket.socket', sync_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__('config_path', 'str', config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__('account_id', 'str', account_id)
        if not isinstance(account_path, str):
            logger.critical("Raising TypeError:")
            __type_error__('account_path', 'str', account_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__('from_dict', 'Optional[dict[str, Any]]', from_dict)
        if raw_contact is not None and not isinstance(raw_contact, dict):
            logger.critical("Raising TypeError:")
            __type_error__('raw_contact', 'Optional[dict[str, Any]]',
                           raw_contact)
        if name is not None and not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__('name', 'Optional[str]', name)
        if number is not None and not isinstance(number, str):
            logger.critical("Raising TypeError:")
            __type_error__('number', 'Optional[str]', number)
        if uuid is not None and not isinstance(uuid, str):
            logger.critical("Raising TypeError:")
            __type_error__('uuid', 'Optional[str]', uuid)
        if not isinstance(is_blocked, bool):
            logger.critical("Raising TypeError:")
            __type_error__('is_blocked', 'bool', is_blocked)
        if expiration is not None and not isinstance(expiration, (int, timedelta)):
            logger.critical("Raising TypeError:")
            __type_error__('expiration', 'Optional[int | timedelta]',
                           expiration)
        if color is not None and not isinstance(color, str):
            logger.critical("Raising TypeError:")
            __type_error__('color', 'Optional[str]', color)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to run commands on."""
        self._sync_socket: socket.socket = sync_socket
        """The socket to run sync operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_path: str = account_path
        """The full path to the account data directory."""
        self._account_id: str = account_id
        """This account's ID."""

        # Set external properties:
        self.name: Optional[str] = name
        """The name of the contact."""
        self.number: Optional[str] = number
        """The phone number of the contact."""
        self.uuid: Optional[str] = uuid
        """The UUID of the contact."""
        self.profile: Optional[SignalProfile] = None
        """The profile of the contact."""
        self.devices: Optional[SignalDevices] = None
        """The contacts device list."""
        self.is_blocked: bool = is_blocked
        """Is this contact blocked?"""
        self.expiration: Optional[timedelta] = None
        """Expiration timedelta."""
        if expiration is not None:
            if isinstance(expiration, int):
                self.expiration = timedelta(seconds=expiration)
            else:
                self.expiration = expiration
        self.is_typing: bool = False
        """Is this contact typing?"""
        self.last_typing_change: Optional[SignalTimestamp] = None
        """The SignalTimestamp of the last typing change."""
        self.last_seen: Optional[SignalTimestamp] = None
        """The last time this contact was seen."""
        self.color: Optional[str] = color
        """The colour of the contact."""
        self.is_self: bool = False
        """Is this the self-contact?"""
        self.user_obj: Optional[Any] = None
        """An object set by the user to store with the contact."""

        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw contact:
        elif raw_contact is not None:
            self.__from_raw_contact__(raw_contact)

        # Mark as self:
        if self.number == self._account_id:
            self.is_self = True

        # Catch unknown contact:
        if self.name == UNKNOWN_CONTACT_NAME:
            if self.profile is not None:
                self.set_name(self.profile.name)
                # Force the name for this session if setting it failed:
                self.name = self.profile.name

        # If 'devices' isn't created yet, create empty devices:
        if self.devices is None:
            self.devices = SignalDevices(sync_socket=self._sync_socket, account_id=self.get_id())

        # Validate that this is a valid contact:
        if self.number is None and self.uuid is None:
            raise RuntimeError("Invalid contact created, has no number and no uuid.")

    ##################
    # Init:
    ##################
    def __from_raw_contact__(self, raw_contact: dict[str, Any]) -> None:
        """
        Load properties from a raw contact dict.
        :param raw_contact: dict[str, Any]: The dict provided by signal.
        :return: None
        """
        if raw_contact['name'] == '':
            self.name = None
        else:
            self.name = raw_contact['name']
        self.number = raw_contact['number']
        self.uuid = raw_contact['uuid']
        self.is_blocked = raw_contact['isBlocked']
        self.color = raw_contact['color']
        if raw_contact['messageExpirationTime'] == 0:
            self.expiration = None
        else:
            self.expiration = timedelta(seconds=raw_contact['messageExpirationTime'])
        self.profile = SignalProfile(sync_socket=self._sync_socket, config_path=self._config_path,
                                     account_id=self._account_id, contact_id=self.get_id(),
                                     raw_profile=raw_contact['profile']
                                     )
        if self.name is None and self.profile.name != '':
            self.set_name(self.profile.name)
            self.name = self.profile.name

    ##########################
    # Overrides:
    ##########################
    def __eq__(self, other: Self) -> bool:
        """
        Determine equality.
        :param other: The other object.
        :return: bool: the equality result.
        """
        if super().__eq__(other):
            self.__update__(other)
            return True
        if isinstance(other, SignalContact):
            if self.uuid == other.uuid or self.number == other.number:
                self.__update__(other)
                return True
        return False

    def __str__(self) -> str:
        """
        String representation of this contact.
        :return: str
        """
        return f"{self.name}({self.get_id()})"

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__()
        """
        contact_dict: dict[str, Any] = {
            'name': self.name,
            'number': self.number,
            'uuid': self.uuid,
            'profile': None,
            'devices': None,
            'isBlocked': self.is_blocked,
            'expiration': None,
            'isTyping': False,
            'lastTypingChange': None,
            'lastSeen': None,
            'color': self.color,
            'userObj': self.user_obj,
        }
        if self.profile is not None:
            contact_dict['profile'] = self.profile.__to_dict__()
        if self.devices is not None:
            contact_dict['devices'] = self.devices.__to_dict__()
        if self.expiration is not None:
            contact_dict['expiration'] = self.expiration.total_seconds()
        if self.last_typing_change is not None:
            contact_dict['lastTypingChange'] = self.last_typing_change.__to_dict__()
        if self.last_seen is not None:
            contact_dict['lastSeen'] = self.last_seen.__to_dict__()

        # Add recipient data:
        recipient_dict = super().__to_dict__()
        for key in recipient_dict:
            contact_dict[key] = recipient_dict[key]

        return contact_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: Load from a dict provided by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        # Load basic properties:
        self.name = from_dict['name']
        self.number = from_dict['number']
        self.uuid = from_dict['uuid']
        self.is_blocked = from_dict['isBlocked']
        self.is_typing = from_dict['isTyping']
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.color = from_dict['color']
        self.user_obj = from_dict['userObj']
        # Load Profile:
        self.profile = None
        if from_dict['profile'] is not None:
            if self.number == self._account_id:
                self.profile = SignalProfile(sync_socket=self._sync_socket,
                                             config_path=self._config_path,
                                             account_id=self._account_id,
                                             contact_id=self.get_id(),
                                             from_dict=from_dict['profile'])
            else:
                self.profile = SignalProfile(sync_socket=self._sync_socket,
                                             config_path=self._config_path,
                                             account_id=self._account_id,
                                             contact_id=self.get_id(),
                                             from_dict=from_dict['profile'])
        # Load Devices:
        self.devices = None
        if from_dict['devices'] is not None:
            self.devices = SignalDevices(sync_socket=self._sync_socket, account_id=self._account_id,
                                         from_dict=from_dict['devices'])

        # Load last typing change:
        self.last_typing_change = None
        if from_dict['lastTypingChange'] is not None:
            self.last_typing_change = SignalTimestamp(from_dict=from_dict['lastTypingChange'])

        # Load last seen:
        self.last_seen = None
        if from_dict['lastSeen'] is not None:
            self.last_seen = SignalTimestamp(from_dict=from_dict['lastSeen'])

    ########################
    # Getters:
    ########################
    def get_id(self) -> str:
        """
        Get the id, preferring the phone number, otherwise the uuid of the contact.
        :returns: str: The number or uuid.
        """
        if self.number is not None:
            return self.number
        return self.uuid

    def get_display_name(self, proper_self: bool = True) -> str:
        """
        Get a display version of the contact name.
        :param proper_self: bool: If this is the self contact, return the proper name,
            otherwise return 'note-to-self'.
        :returns: str: The display name.
        """
        if not proper_self and self.is_self:
            return SELF_CONTACT_NAME
        if self.name is not None and self.name != '' and self.name != UNKNOWN_CONTACT_NAME and \
                self.name != 'Note-To-Self':
            return self.name
        if self.profile is not None and self.profile.name != '':
            return self.profile.name
        if self.number is not None:
            return self.number
        return UNKNOWN_CONTACT_NAME

    ###########################
    # Setters:
    ##########################
    def set_name(self, name: str) -> bool:
        """
        Set the name of the contact.
        :param name: str: The name to assign to the contact.
        :raises: TypeError if name not a string.
        """
        # Type check name:
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        # If name hasn't changed return false:
        if self.name == name:
            return False
        # create command object and json command string:
        set_name_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "updateContact",
            "params": {
                "account": self._account_id,
                "recipient": self.get_id(),
                "name": name,
            }
        }
        json_command_str = json.dumps(set_name_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        error_occurred, error_code, _ = __check_response_for_error__(response_obj, [-1])

        if error_occurred:
            if error_code == -1:  # Can't update on linked accounts.
                return False

        # All is good set name.
        self.name = name
        return True

    #########################
    # Helpers:
    #########################
    def __update__(self, other: Self) -> None:
        """
        Update a contact given another contact assumed to be more recent.
        :param other: SignalContact: The other contact to update from.
        :return: None
        """
        super().__update__(other)
        self.name = other.name
        self.is_blocked = other.is_blocked
        self.expiration = other.expiration
        if self.profile is not None and other.profile is not None:
            self.profile.__update__(other.profile)
        elif self.profile is None and other.profile is not None:
            self.profile = other.profile

    def __parse_typing_message__(self, message) -> None:
        """
        Parse a typing message.
        :param message: SignalTypingMessage: The message to parse.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_typing_message__.__name__)
        if message.action == TypingStates.STARTED:
            self.is_typing = True
        elif message.action == TypingStates.STOPPED:
            self.is_typing = False
        else:
            error_message: str = (f"invalid SignalTypingMessage, can't parse typing"
                                  f"action: {str(message.action)}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)
        self.last_typing_change = message.time_changed
        self.__seen__(message.time_changed)

    ############################
    # Methods:
    ############################
    def __seen__(self, time_seen: SignalTimestamp) -> None:
        """
        Update the last time this contact has been seen.
        :param time_seen: SignalTimestamp: The time this contact was seen at.
        :raises: TypeError: If time_seen is not a SignalTimestamp object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__seen__.__name__)
        if not isinstance(time_seen, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__('time_seen', 'SignalTimestamp', time_seen)
        if self.last_seen is not None:
            self.last_seen = max(time_seen, self.last_seen)
        else:
            self.last_seen = time_seen
