#!/usr/bin/env python3
"""
File: signalContact.py
Store and manage a single contact.
"""
import logging
from typing import TypeVar, Optional, Any
import socket
import json

from .signalCommon import __type_error__, __socket_receive__, __socket_send__, __parse_signal_response__, \
    __check_response_for_error__, UNKNOWN_CONTACT_NAME, SELF_CONTACT_NAME, TypingStates
from .signalProfile import Profile
from .signalTimestamp import Timestamp
from .signalDevices import Devices

Self = TypeVar("Self", bound="Contact")


class Contact(object):
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
                 expiration: Optional[int] = None,
                 color: Optional[str] = None,
                 ) -> None:
        """
        Initialize a Contact.
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
        :param expiration: Optional[int]: The expiration of this contact in seconds.
        :param color: Optional[str]: The colour of this contact.
        """
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
            __type_error__('raw_contact', 'Optional[dict[str, Any]]', raw_contact)
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
        if expiration is not None and not isinstance(expiration, int):
            logger.critical("Raising TypeError:")
            __type_error__('expiration', 'Optional[int]', expiration)
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
        self.profile: Optional[Profile] = None
        """The profile of the contact."""
        self.devices: Optional[Devices] = None
        """The contacts device list."""
        self.is_blocked: bool = is_blocked
        """Is this contact blocked?"""
        self.expiration: Optional[int] = expiration
        """Expiration in seconds."""
        self.is_typing: bool = False
        """Is this contact typing?"""
        self.last_typing_change: Optional[Timestamp] = None
        """The Timestamp of the last typing change."""
        self.last_seen: Optional[Timestamp] = None
        """The last time this contact was seen."""
        self.color: Optional[str] = color
        """The colour of the contact."""
        self.is_self: bool = False
        """Is this the self-contact?"""

        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw contact:
        elif raw_contact is not None:
            self.__from_raw_contact__(raw_contact)

        # Mark as self:
        if self.number == self._account_id:
            self.is_self = True
            self.name = SELF_CONTACT_NAME

        # Catch unknown contact:
        if self.name == UNKNOWN_CONTACT_NAME:
            if self.profile is not None:
                self.set_name(self.profile.name)
                self.name = self.profile.name  # Force the name for this session if setting it failed.

        # If 'devices' isn't created yet, create empty devices:
        if self.devices is None:
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self.get_id())

        return

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
            self.expiration = raw_contact['messageExpirationTime']
        self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path,
                               account_id=self._account_id, contact_id=self.get_id(), raw_profile=raw_contact['profile']
                               )
        if self.name is None and self.profile.name != '':
            self.set_name(self.profile.name)
        return

    ##########################
    # Overrides:
    ##########################
    def __eq__(self, other: Self) -> bool:
        """
        Determine equality.
        :param other: The other object.
        :return: bool: the equality result.
        """
        logger: logging.Logger = logging.getLogger('__name__' + '.' + self.__eq__.__name__)
        if isinstance(other, Contact):
            number_match: bool = False
            uuid_match: bool = False
            if self.number is not None and other.number is not None:
                number_match = self.number == other.number
            if self.uuid is not None and other.uuid is not None:
                uuid_match = self.uuid == other.uuid
            if self.uuid is None or other.uuid is None:
                return number_match
            elif self.number is None or other.number is None:
                return uuid_match
            else:
                return number_match and uuid_match
        error_message: str = "can only check against another Contact object."
        logger.critical("Raising TypeError(%s)." % error_message)
        raise TypeError(error_message)

    def __str__(self) -> str:
        """
        String representation of this contact.
        :return: str
        """
        return_val: str = "%s(%s)" % (self.name, self.get_id())
        return return_val

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
            'expiration': self.expiration,
            'isTyping': False,
            'lastTypingChange': None,
            'lastSeen': None,
            'color': self.color,
        }
        if self.profile is not None:
            contact_dict['profile'] = self.profile.__to_dict__()
        if self.devices is not None:
            contact_dict['devices'] = self.devices.__to_dict__()
        if self.last_typing_change is not None:
            contact_dict['lastTypingChange'] = self.last_typing_change.__to_dict__()
        if self.last_seen is not None:
            contact_dict['lastSeen'] = self.last_seen.__to_dict__()
        return contact_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: Load from a dict provided by __to_dict__().
        :return: None
        """
        # Load basic properties:
        self.name = from_dict['name']
        self.number = from_dict['number']
        self.uuid = from_dict['uuid']
        self.is_blocked = from_dict['isBlocked']
        self.is_typing = from_dict['isTyping']
        self.expiration = from_dict['expiration']
        self.color = from_dict['color']

        # Load Profile:
        self.profile = None
        if from_dict['profile'] is not None:
            if self.number == self._account_id:
                self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path,
                                       account_id=self._account_id,
                                       contact_id=self.get_id(), from_dict=from_dict['profile'])
            else:
                self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path,
                                       account_id=self._account_id,
                                       contact_id=self.get_id(), from_dict=from_dict['profile'])
        # Load Devices:
        self.devices = None
        if from_dict['devices'] is not None:
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self._account_id,
                                   from_dict=from_dict['devices'])

        # Load last typing change:
        self.last_typing_change = None
        if from_dict['lastTypingChange'] is not None:
            self.last_typing_change = Timestamp(from_dict=from_dict['lastTypingChange'])

        # Load last seen:
        self.last_seen = None
        if from_dict['lastSeen'] is not None:
            self.last_seen = Timestamp(from_dict=from_dict['lastSeen'])
        return

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

    def get_display_name(self) -> str:
        """
        Get a display version of the contact name.
        :returns: str: The display name.
        """
        if self.is_self:
            if self.profile is not None and self.profile.name != '':
                return self.profile.name
            else:
                return self.name
        if self.name is not None and self.name != '' and self.name != UNKNOWN_CONTACT_NAME:
            return self.name
        elif self.profile is not None and self.profile.name != '':
            return self.profile.name
        else:
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
        response_str = __socket_receive__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        error_occurred, error_code, error_message = __check_response_for_error__(response_obj, [-1])

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
        :param other: Contact: The other contact to update from.
        :return: None
        """
        self.name = other.name
        self.is_blocked = other.is_blocked
        self.expiration = other.expiration
        if self.profile is not None and other.profile is not None:
            self.profile.__update__(other.profile)
        elif self.profile is None and other.profile is not None:
            self.profile = other.profile
        return

    def __parse_typing_message__(self, message) -> None:
        """
        Parse a typing message.
        :param message: TypingMessage: The message to parse.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_typing_message__.__name__)
        if message.action == TypingStates.STARTED:
            self.is_typing = True
        elif message.action == TypingStates.STOPPED:
            self.is_typing = False
        else:
            error_message: str = "invalid TypingMessage, can't parse typing action: %s" % str(message.action)
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        self.last_typing_change = message.time_changed
        self.seen(message.time_changed)
        return

    ############################
    # Methods:
    ############################
    def seen(self, time_seen: Timestamp) -> None:
        """
        Update the last time this contact has been seen.
        :param time_seen: Timestamp: The time this contact was seen at.
        :raises: TypeError: If time_seen is not a Timestamp object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.seen.__name__)
        if not isinstance(time_seen, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__('time_seen', 'Timestamp', time_seen)
        if self.last_seen is not None:
            if time_seen > self.last_seen:
                self.last_seen = time_seen
        else:
            self.last_seen = time_seen
        return
