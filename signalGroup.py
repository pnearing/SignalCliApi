#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __socket_receive__, __socket_send__
from .signalContacts import Contacts
from .signalContact import Contact
from .signalTimestamp import Timestamp

DEBUG: bool = True
Self = TypeVar("Self", bound="Group")


class Group(object):
    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_contacts: Contacts,
                 from_dict: Optional[dict] = None,
                 raw_group: Optional[dict] = None,
                 group_id: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 is_blocked: Optional[bool] = False,
                 is_member: Optional[bool] = False,
                 expiration: Optional[int] = None,
                 link: Optional[str] = None,
                 members: Optional[list[Contact]] = [],
                 pending_members: Optional[list[Contact]] = [],
                 requesting_members: Optional[list[Contact]] = [],
                 admins: Optional[list[Contact]] = [],
                 banned: Optional[list[Contact]] = [],
                 permission_add_member: Optional[str] = None,
                 permission_edit_details: Optional[str] = None,
                 permission_send_message: Optional[str] = None,
                 last_seen: Optional[Timestamp] = None,
                 ) -> None:
        # TODO: Argument checks
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._config_path: str = config_path
        self._account_id: str = account_id
        self._contacts: Contacts = account_contacts
        self._is_valid: bool = True
        # Set external properties:
        self.id: str = group_id
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.is_blocked: bool = is_blocked
        self.is_member: bool = is_member
        self.expiration: Optional[int] = expiration
        self.link: Optional[str] = link
        self.members: list[Contact] = members
        self.pending: list[Contact] = pending_members
        self.requesting: list[Contact] = requesting_members
        self.admins: list[Contact] = admins
        self.banned: list[Contact] = banned
        self.permission_add_member: str = permission_add_member
        self.permission_edit_details: str = permission_edit_details
        self.permission_send_message: str = permission_send_message
        self.last_seen: Optional[Timestamp] = last_seen
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw_group:
        elif raw_group is not None:
            self.__from_raw_group__(raw_group)
        # Group object was created without raw_group or from_dict, see if we can get details from signal:
        else:
            if self.id is not None:
                self._is_valid = self.__sync__()
            else:
                self._is_valid = False
        return

    #################
    # Init:
    #################

    def __from_raw_group__(self, raw_group: dict) -> None:
        # print(raw_group)
        self.id = raw_group['contact_id']
        if raw_group['name'] == '':
            self.name = None
        else:
            self.name = raw_group['name']
        if raw_group['description'] == '':
            self.description = None
        else:
            self.description = raw_group['description']
        self.is_blocked = raw_group['is_blocked']
        self.is_member = raw_group['is_member']
        if raw_group['messageExpirationTime'] == 0:
            self.expiration = None
        else:
            self.expiration = raw_group['messageExpirationTime']
        self.link = raw_group['groupInviteLink']
        self.permission_add_member = raw_group['permission_add_member']
        self.permission_edit_details = raw_group['permission_edit_details']
        self.permission_send_message = raw_group['permission_send_message']
        # Parse members:
        self.members = []
        for contact_dict in raw_group['members']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.members.append(contact)
        # Parse pending:
        self.pending = []
        for contact_dict in raw_group['pending_members']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_dict in raw_group['requesting_members']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.requesting.append(contact)
        # Parse admins:
        self.admins = []
        for contact_dict in raw_group['admins']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.admins.append(contact)
        # Parse banned:
        self.banned = []
        for contact_dict in raw_group['banned']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.banned.append(contact)
        return

    ######################
    # Overrides:
    ######################
    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Group):
            if self.id == __o.id:
                return True
        return False

    ###################################
    # To / From Dict:
    ###################################
    def __to_dict__(self) -> dict:
        group_dict = {
            'contact_id': self.id,
            'name': self.name,
            'description': self.description,
            'is_blocked': self.is_blocked,
            'is_member': self.is_member,
            'expiration': self.expiration,
            'link': self.link,
            'permAddMember': self.permission_add_member,
            'permEditDetails': self.permission_edit_details,
            'permSendMessage': self.permission_send_message,
            'members': [],
            'pending': [],
            'requesting': [],
            'admins': [],
            'banned': [],
        }
        for contact in self.members:
            group_dict['members'].append(contact.get_id())
        for contact in self.pending:
            group_dict['pending'].append(contact.get_id())
        for contact in self.requesting:
            group_dict['requesting'].append(contact.get_id())
        for contact in self.admins:
            group_dict['admins'].append(contact.get_id())
        for contact in self.banned:
            group_dict['banned'].append(contact.get_id())
        return group_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self.id = from_dict['contact_id']
        self.name = from_dict['name']
        self.description = from_dict['description']
        self.is_blocked = from_dict['is_blocked']
        self.is_member = from_dict['is_member']
        self.expiration = from_dict['expiration']
        self.link = from_dict['link']
        self.permission_add_member = from_dict['permAddMember']
        self.permission_edit_details = from_dict['permEditDetails']
        self.permission_send_message = from_dict['permSendMessage']
        # Parse members:
        self.members = []
        for contact_id in from_dict['members']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=contact_id)
            self.members.append(contact)
        # Parse Pending:
        self.pending = []
        for contact_id in from_dict['pending']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=contact_id)
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_id in from_dict['requesting']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=contact_id)
            self.requesting.append(contact)
        # Parse admins:
        self.admins = []
        for contact_id in from_dict['admins']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=contact_id)
            self.admins.append(contact)
        # Parse banned:
        self.banned = []
        for contact_id in from_dict['banned']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=contact_id)
            self.banned.append(contact)
        return

    #################
    # Helpers:
    #################

    def __merge__(self, __o: Self) -> None:
        self.name = __o.name
        self.description = __o.description
        self.is_blocked = __o.is_blocked
        self.is_member = __o.is_member
        self.expiration = __o.expiration
        self.link = __o.link
        self.permission_add_member = __o.permission_add_member
        self.permission_edit_details = __o.permission_edit_details
        self.permission_send_message = __o.permission_send_message
        self.members = __o.members
        self.pending = __o.pending
        self.requesting = __o.requesting
        self.admins = __o.admins
        self.banned = __o.banned
        return

    ########################
    # Sync:
    ########################
    def __sync__(self) -> bool:
        # Create command object and json command string:
        list_group_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "listGroups",
            "params": {
                "account": self._account_id,
                "groupId": self.id,
            }
        }
        json_command_str = json.dumps(list_group_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                errorMessage = "signal error during group __sync__: code: %i message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message'])
                print(errorMessage, file=sys.stderr)
            return False
        rawGroup = response_obj['result'][0]
        self.__from_raw_group__(rawGroup)
        return True

    ########################################
    # Getters:
    ######################################
    def get_id(self) -> str:
        return self.id

    def get_display_name(self, max_len: Optional[int] = None) -> str:
        if max_len is not None and max_len <= 0:
            raise ValueError("max_len must be greater than zero")
        displayName = ''
        if self.name is not None and self.name != '' and self.name != '<UNKNOWN-GROUP>':
            displayName = self.name
        else:
            for contact in self.members:
                displayName = displayName + contact.get_display_name() + ', '
            displayName = displayName[:-2]
        if max_len is not None and len(displayName) > max_len:
            displayName = displayName[:max_len]
        return displayName
