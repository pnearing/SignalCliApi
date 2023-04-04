#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalProfile import Profile
from .signalTimestamp import Timestamp
from .signalDevices import Devices

Self = TypeVar("Self", bound="Contact")

DEBUG: bool = False


class Contact(object):
    """Class to store a contact."""
    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_path: str,
                 from_dict: Optional[dict] = None,
                 raw_contact: Optional[dict] = None,
                 name: Optional[str] = None,
                 number: Optional[str] = None,
                 uuid: Optional[str] = None,
                 profile: Optional[Profile] = None,
                 devices: Optional[Devices] = None,
                 is_blocked: Optional[bool] = None,
                 expiration: Optional[int] = None,
                 is_typing: Optional[bool] = None,
                 last_typing_change: Optional[Timestamp] = None,
                 last_seen: Optional[Timestamp] = None,
                 color: Optional[str] = None,
                 ) -> None:
        # TODO: Argument checks:
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._config_path: str = config_path
        self._account_path: str = account_path
        self._account_id: str = account_id
        # Set external properties:
        self.name: Optional[str] = name
        self.number: Optional[str] = number
        self.uuid: Optional[str] = uuid
        self.profile: Optional[Profile] = profile
        self.devices: Devices = devices
        self.is_blocked: bool = is_blocked
        self.expiration: Optional[int] = expiration
        self.is_typing: Optional[bool] = is_typing
        self.last_typing_change: Optional[Timestamp] = last_typing_change
        self.last_seen: Optional[Timestamp] = last_seen
        self.color: Optional[str] = color
        self.is_self: bool = False
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        elif raw_contact is not None:
            self.__from_raw_contact__(raw_contact)
        # Mark as self:
        if self.number == self._account_id:
            self.is_self = True
            self.name = "Note-To-Self"
        # Catch unknown contact:
        if self.name == "<UNKNOWN-CONTACT>":
            if self.profile is not None:
                self.set_name(self.profile.name)
                self.name = self.profile.name  # Force the name for this session if setting failed.
        # If devices isn't yet set create empty devices:
        if self.devices is None:
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self.uuid)

        return

    ##################
    # Init:
    ##################
    def __from_raw_contact__(self, raw_contact: dict) -> None:
        # print(raw_contact)
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
        self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path, account_id=self._account_id,
                               contact_id=self.get_id(), raw_profile=raw_contact['profile'])
        if self.name is None and self.profile.name != '':
            self.set_name(self.profile.name)
        return

    ##########################
    # Overrides:
    ##########################
    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Contact):
            number_match: bool = False
            uuid_match: bool = False
            if self.number is not None and __o.number is not None:
                number_match = self.number == __o.number
            if self.uuid is not None and __o.uuid is not None:
                uuid_match = self.uuid == __o.uuid
            if self.uuid is None or __o.uuid is None:
                return number_match
            elif self.number is None or __o.number is None:
                return uuid_match
            else:
                return number_match and uuid_match
        return False

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict:
        contact_dict = {
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

    def __from_dict__(self, from_dict: dict) -> None:
        self.name = from_dict['name']
        self.number = from_dict['number']
        self.uuid = from_dict['uuid']
        self.is_blocked = from_dict['isBlocked']
        self.is_typing = from_dict['isTyping']
        self.expiration = from_dict['expiration']
        self.color = from_dict['color']
        # Load Profile:
        if from_dict['profile'] is not None:
            if self.number == self._account_id:
                self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path,
                                       account_id=self._account_id,
                                       contact_id=self.get_id(), from_dict=from_dict['profile'])
            else:
                self.profile = Profile(sync_socket=self._sync_socket, config_path=self._config_path,
                                       account_id=self._account_id,
                                       contact_id=self.get_id(), from_dict=from_dict['profile'])
        else:
            self.profile = None
        # Load Devices:
        if from_dict['devices'] is not None:
            self.devices = Devices(sync_socket=self._sync_socket, account_id=self._account_id,
                                   from_dict=from_dict['devices'])
        else:
            self.devices = None
        # Load last typing change:
        if from_dict['lastTypingChange'] is not None:
            self.last_typing_change = Timestamp(from_dict=from_dict['lastTypingChange'])
        else:
            self.last_typing_change = None
        # Load last seen:
        if from_dict['lastSeen'] is not None:
            self.last_seen = Timestamp(from_dict=from_dict['lastSeen'])
        else:
            self.last_seen = None
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
        if self.name is not None and self.name != '' and self.name != "<UNKNOWN-CONTACT>":
            return self.name
        elif self.profile is not None and self.profile.name != '':
            return self.profile.name
        else:
            return "<UNKNOWN-CONTACT>"

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
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                errorMessage = "Signal error while setting name: code %i, message: %s" % (response_obj['error']['code'],
                                                                                          response_obj['error'][
                                                                                              'message'])
                print(errorMessage, file=sys.stderr)
            return False
        # All is good set name.
        self.name = name
        return True

    #########################
    # Helpers:
    #########################
    def __merge__(self, __o: Self) -> None:
        self.name = __o.name
        self.is_blocked = __o.is_blocked
        self.expiration = __o.expiration
        if self.profile is not None and __o.profile is not None:
            self.profile.__merge__(__o.profile)
        elif self.profile is None and __o.profile is not None:
            self.profile = __o.profile
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
        if not isinstance(time_seen, Timestamp):
            __type_error__('time_seen', 'Timestamp', time_seen)
        if self.last_seen is not None:
            if self.last_seen < time_seen:
                self.last_seen = time_seen
        else:
            self.last_seen = time_seen
        return
