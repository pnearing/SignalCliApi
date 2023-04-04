#!/usr/bin/env python3
"""File: signalGroup.py"""
from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __socket_receive__, __socket_send__, __type_error__
from .signalContacts import Contacts
from .signalContact import Contact
from .signalTimestamp import Timestamp

DEBUG: bool = False
Self = TypeVar("Self", bound="Group")


class Group(object):
    """An object containing a single group."""
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
        # Argument checks
        if not isinstance(sync_socket, socket.socket):
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            __type_error__("account_id", "str", account_id)
        if not isinstance(account_contacts, Contacts):
            __type_error__("account_contacts", "Contacts", account_contacts)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if raw_group is not None and not isinstance(raw_group, dict):
            __type_error__("raw_group", "Optional[dict]", raw_group)
        if group_id is not None and not isinstance(group_id, str):
            __type_error__("group_id", "Optional[str]", group_id)
        if name is not None and not isinstance(name, str):
            __type_error__("name", "Optional[str]", name)
        if description is not None and not isinstance(description, str):
            __type_error__("description", "Optional[str]", description)
        if is_blocked is not None and not isinstance(is_blocked, bool):
            __type_error__("is_blocked", "Optional[bool]", is_blocked)
        if is_member is not None and not isinstance(is_member, bool):
            __type_error__("is_member", "Optional[bool]", is_member)
        if expiration is not None and not isinstance(expiration, int):
            __type_error__("expiration", "Optional[int]", expiration)
        if link is not None and not isinstance(link, str):
            __type_error__("link", "Optional[str]", link)
        if members is not None and not isinstance(members, list):
            __type_error__("members", "Optional[list[Contact]]", members)
        elif members is not None:
            for i, member in enumerate(members):
                if not isinstance(member, Contact):
                    __type_error__("members[%i]" % i, "Contact", member)
        if pending_members is not None and not isinstance(pending_members, list):
            __type_error__("pending_members", "Optional[list[Contact]]", pending_members)
        elif pending_members is not None:
            for i, member in enumerate(pending_members):
                if not isinstance(member, Contact):
                    __type_error__("pending_members[%i]" % i, "Contact", member)
        if requesting_members is not None and not isinstance(requesting_members, list):
            __type_error__("requesting_members", "Optional[list[Contact]]", requesting_members)
        elif requesting_members is not None:
            for i, member in enumerate(requesting_members):
                if not isinstance(member, Contact):
                    __type_error__("requesting_members[%i]" % i, "Contact", member)
        if admins is not None and not isinstance(admins, list):
            __type_error__("admins", "Optional[list[str]]", admins)
        elif admins is not None:
            for i, admin in enumerate(admins):
                if not isinstance(admin, Contact):
                    __type_error__("admins[%i]" % i, "Contact", admin)
        if banned is not None and not isinstance(banned, list):
            __type_error__("banned", "Optional[list[Contact]]", banned)
        elif banned is not None:
            for i, contact in enumerate(banned):
                if not isinstance(contact, Contact):
                    __type_error__("banned[%i]", "Contact", contact)
        if permission_add_member is not None and not isinstance(permission_add_member, str):
            __type_error__("permission_add_member", "Optional[str]", permission_add_member)
        if permission_edit_details is not None and not isinstance(permission_edit_details, str):
            __type_error__("permission_edit_details", "Optional[str]", permission_edit_details)
        if permission_send_message is not None and not isinstance(permission_send_message, str):
            __type_error__("permission_send_message", "Optional[str]", permission_send_message)
        if last_seen is not None and not isinstance(last_seen, Timestamp):
            __type_error__("last_seen", "Optional[Timestamp]", last_seen)
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
        # print("DEBUG in __from_raw_group__")
        # exit(254)
        # print("DEBUG: in __from_raw_group__ after exit.")
        self.id = raw_group['id']
        self.name: Optional[str] = None
        if raw_group['name'] == '':
            self.name = None
        else:
            self.name = raw_group['name']
        if raw_group['description'] == '':
            self.description = None
        else:
            self.description = raw_group['description']
        self.is_blocked = raw_group['isBlocked']
        self.is_member = raw_group['isMember']
        if raw_group['messageExpirationTime'] == 0:
            self.expiration = None
        else:
            self.expiration = raw_group['messageExpirationTime']
        self.link = raw_group['groupInviteLink']
        self.permission_add_member = raw_group['permissionAddMember']
        self.permission_edit_details = raw_group['permissionEditDetails']
        self.permission_send_message = raw_group['permissionSendMessage']
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
        for contact_dict in raw_group['pendingMembers']:
            added, contact = self._contacts.__get_or_add__(
                "<UNKNOWN-CONTACT>",
                number=contact_dict['number'],
                uuid=contact_dict['uuid']
            )
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_dict in raw_group['requestingMembers']:
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
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'isBlocked': self.is_blocked,
            'isMember': self.is_member,
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
        self.id = from_dict['id']
        self.name = from_dict['name']
        self.description = from_dict['description']
        self.is_blocked = from_dict['isBlocked']
        self.is_member = from_dict['isMember']
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
            "id": 0,
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
        """
        Return the group id.
        :returns: str: The group id.
        """
        return self.id

    def get_display_name(self, max_len: Optional[int] = None) -> str:
        """
        Get the display name, optionally truncating it to a number of characters.
        :param max_len: Optional[int]: The number of characters to return.
        :returns str: The display name.
        :raises: TypeError: If max_len is not an int.
        :raises: ValueError: if max_len is less than 1.
        """
        if max_len is not None and not isinstance(max_len, int):
            __type_error__("max_len", "Optional[int]", max_len)
        elif max_len is not None and max_len <= 0:
            raise ValueError("max_len must be greater than zero")
        display_name = ''
        if self.name is not None and self.name != '' and self.name != '<UNKNOWN-GROUP>':
            display_name = self.name
        else:
            for contact in self.members:
                display_name = display_name + contact.get_display_name() + ', '
            display_name = display_name[:-2]
        if max_len is not None and len(display_name) > max_len:
            display_name = display_name[:max_len]
        return display_name
