#!/usr/bin/env python3
"""
File: signalGroup.py
Manage and maintain a single group.
"""
import logging
from typing import TypeVar, Optional, Any
import socket
import json

from .signalCommon import __socket_receive__, __socket_send__, __type_error__, __parse_signal_response__, \
    __check_response_for_error__, UNKNOWN_GROUP_NAME
from .signalContacts import Contacts
from .signalContact import Contact
from .signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Group")


class Group(object):
    """An object containing a single group."""
    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_contacts: Contacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_group: Optional[dict[str, Any]] = None,
                 group_id: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 is_blocked: bool = False,
                 is_member: bool = False,
                 expiration: Optional[int] = None,
                 link: Optional[str] = None,
                 members: list[Contact] = [],
                 pending_members: list[Contact] = [],
                 requesting_members: list[Contact] = [],
                 admins: list[Contact] = [],
                 banned: list[Contact] = [],
                 permission_add_member: Optional[str] = None,
                 permission_edit_details: Optional[str] = None,
                 permission_send_message: Optional[str] = None,
                 last_seen: Optional[Timestamp] = None,
                 ) -> None:
        """
        Initialize a Group.
        :param sync_socket: socket.socket: The socket to run sync commands on.
        :param config_path: str: The path to the signal-cli config directory.
        :param account_id: str: This account ID.
        :param account_contacts: The account's Contacts object.
        :param from_dict: dict[str, Any]: Load from a dict provided by __to_dict__()
        :param raw_group: dict[str, Any]: Load from a dict provided by signal.
        :param group_id: Optional[str]: The group ID.
        :param name: Optional[str]: The group name.
        :param description: Optional[str]: The group description.
        :param is_blocked: bool: If this group is blocked.
        :param is_member: bool: If this account is a member of the group.
        :param expiration: Optional[int]: The expiration time of the group.
        :param link: Optional[str]: The join link of the group.
        :param members: list[Contact]: Existing members.
        :param pending_members: list[Contact]: Pending members.
        :param requesting_members: list[Contact] Requesting members.
        :param admins: list[Contact]: Admin members.
        :param banned: list[Contact]: Banned members.
        :param permission_add_member: Optional[str]: Add member permissions.
        :param permission_edit_details: Optional[str]: Edit details permissions.
        :param permission_send_message: Optional[str]: Permission to send messages.
        :param last_seen: Optional[Timestamp]: The time this group was last seen.
        """
        # Super:
        object.__init__(self)

        # Set up logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__('command_socket', 'socket.socket', command_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if not isinstance(account_contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("account_contacts", "Contacts", account_contacts)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if raw_group is not None and not isinstance(raw_group, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_group", "Optional[dict]", raw_group)
        if group_id is not None and not isinstance(group_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("group_id", "Optional[str]", group_id)
        if name is not None and not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "Optional[str]", name)
        if description is not None and not isinstance(description, str):
            logger.critical("Raising TypeError:")
            __type_error__("description", "Optional[str]", description)
        if is_blocked is not None and not isinstance(is_blocked, bool):
            logger.critical("Raising TypeError:")
            __type_error__("is_blocked", "Optional[bool]", is_blocked)
        if is_member is not None and not isinstance(is_member, bool):
            logger.critical("Raising TypeError:")
            __type_error__("is_member", "Optional[bool]", is_member)
        if expiration is not None and not isinstance(expiration, int):
            logger.critical("Raising TypeError:")
            __type_error__("expiration", "Optional[int]", expiration)
        if link is not None and not isinstance(link, str):
            logger.critical("Raising TypeError:")
            __type_error__("link", "Optional[str]", link)
        if members is not None and not isinstance(members, list):
            logger.critical("Raising TypeError:")
            __type_error__("members", "Optional[list[Contact]]", members)
        elif members is not None:
            for i, member in enumerate(members):
                if not isinstance(member, Contact):
                    logger.critical("Raising TypeError:")
                    __type_error__("members[%i]" % i, "Contact", member)
        if pending_members is not None and not isinstance(pending_members, list):
            logger.critical("Raising TypeError:")
            __type_error__("pending_members", "Optional[list[Contact]]", pending_members)
        elif pending_members is not None:
            for i, member in enumerate(pending_members):
                if not isinstance(member, Contact):
                    logger.critical("Raising TypeError:")
                    __type_error__("pending_members[%i]" % i, "Contact", member)
        if requesting_members is not None and not isinstance(requesting_members, list):
            logger.critical("Raising TypeError:")
            __type_error__("requesting_members", "Optional[list[Contact]]", requesting_members)
        elif requesting_members is not None:
            for i, member in enumerate(requesting_members):
                if not isinstance(member, Contact):
                    logger.critical("Raising TypeError:")
                    __type_error__("requesting_members[%i]" % i, "Contact", member)
        if admins is not None and not isinstance(admins, list):
            logger.critical("Raising TypeError:")
            __type_error__("admins", "Optional[list[str]]", admins)
        elif admins is not None:
            for i, admin in enumerate(admins):
                if not isinstance(admin, Contact):
                    logger.critical("Raising TypeError:")
                    __type_error__("admins[%i]" % i, "Contact", admin)
        if banned is not None and not isinstance(banned, list):
            logger.critical("Raising TypeError:")
            __type_error__("banned", "Optional[list[Contact]]", banned)
        elif banned is not None:
            for i, contact in enumerate(banned):
                if not isinstance(contact, Contact):
                    logger.critical("Raising TypeError:")
                    __type_error__("banned[%i]", "Contact", contact)
        if permission_add_member is not None and not isinstance(permission_add_member, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_add_member", "Optional[str]", permission_add_member)
        if permission_edit_details is not None and not isinstance(permission_edit_details, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_edit_details", "Optional[str]", permission_edit_details)
        if permission_send_message is not None and not isinstance(permission_send_message, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_send_message", "Optional[str]", permission_send_message)
        if last_seen is not None and not isinstance(last_seen, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__("last_seen", "Optional[Timestamp]", last_seen)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to run sync operations on."""
        self._command_socket: socket.socket = command_socket
        """The socket to run command operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """This account ID."""
        self._contacts: Contacts = account_contacts
        """This account's Contacts object."""
        self._is_valid: bool = True
        """Is this group valid?"""

        # Set external properties:
        self.id: str = group_id
        """The group ID."""
        self.name: Optional[str] = name
        """The name of the group."""
        self.description: Optional[str] = description
        """The description of the group."""
        self.is_blocked: bool = is_blocked
        """Is this group blocked?"""
        self.is_member: bool = is_member
        """Is this account a member of the group?"""
        self.expiration: Optional[int] = expiration
        """The expiration time of this group in seconds."""
        self.link: Optional[str] = link
        """The join link of this group."""
        self.members: list[Contact] = members
        """The current members of this group."""
        self.pending: list[Contact] = pending_members
        """The pending members of this group."""
        self.requesting: list[Contact] = requesting_members
        """The requesting members of the group."""
        self.admins: list[Contact] = admins
        """The admins of the group."""
        self.banned: list[Contact] = banned
        """The banned members of the group."""
        self.permission_add_member: str = permission_add_member
        """The permissions to add a member."""
        self.permission_edit_details: str = permission_edit_details
        """The permission to edit group details."""
        self.permission_send_message: str = permission_send_message
        """The permissions to send a message to the group."""
        self.last_seen: Optional[Timestamp] = last_seen
        """The date / time this was last seen."""

        # Parse from_dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Parse raw_group:
        elif raw_group is not None:
            logger.debug("Loading from raw group.")
            self.__from_raw_group__(raw_group)
        # Group object was created without raw_group or from_dict, see if we can get details from signal:
        else:
            if self.id is not None:
                self.__sync__()
                self._is_valid = True
            else:
                self._is_valid = False
        return

    #################
    # Init:
    #################

    def __from_raw_group__(self, raw_group: dict[str, Any]) -> None:
        """
        Load a group from raw group dict provided by signal.
        :param raw_group:  dict[str, Any]: The dict to load from.
        :return: None
        """
        self.id = raw_group['id']
        self.name: Optional[str] = None
        if raw_group['name'] == '' or raw_group['name'] is None:
            self.name = None
        else:
            self.name = raw_group['name']
        if raw_group['description'] == '' or raw_group['description'] is None:
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
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'], uuid=contact_dict['uuid'])
            self.members.append(contact)
        # Parse pending:
        self.pending = []
        for contact_dict in raw_group['pendingMembers']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'], uuid=contact_dict['uuid'])
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_dict in raw_group['requestingMembers']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'], uuid=contact_dict['uuid'])
            self.requesting.append(contact)
        # Parse admins:
        self.admins = []
        for contact_dict in raw_group['admins']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'], uuid=contact_dict['uuid'])
            self.admins.append(contact)
        # Parse banned:
        self.banned = []
        for contact_dict in raw_group['banned']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'], uuid=contact_dict['uuid'])
            self.banned.append(contact)
        return

    ######################
    # Overrides:
    ######################
    def __eq__(self, other: Self) -> bool:
        """
        Generate equality.
        :param other: Group: The group to compare to.
        :return: bool: True the groups are equal, False they are not.
        :raises TypeError: If other is not a Group object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__eq__.__name__)
        if isinstance(other, Group):
            if self.id == other.id:
                return True
        error_message: str = "Can only compare equality to another Group object."
        logger.critical("Raising TypeError(%s)." % error_message)
        raise TypeError(error_message)

    ###################################
    # To / From Dict:
    ###################################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to pass to __from_dict__().
        """
        group_dict: dict[str, Any] = {
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

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
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
            _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            self.members.append(contact)
        # Parse Pending:
        self.pending = []
        for contact_id in from_dict['pending']:
            _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_id in from_dict['requesting']:
            _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            self.requesting.append(contact)
        # Parse admins:
        self.admins = []
        for contact_id in from_dict['admins']:
            _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            self.admins.append(contact)
        # Parse banned:
        self.banned = []
        for contact_id in from_dict['banned']:
            _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            self.banned.append(contact)
        return

    #################
    # Helpers:
    #################
    def __update__(self, other: Self) -> None:
        """
        Overwrite properties with an update from signal.
        :param other: Group: The most recent copy of the group.
        :return: None
        """
        self.name = other.name
        self.description = other.description
        self.is_blocked = other.is_blocked
        self.is_member = other.is_member
        self.expiration = other.expiration
        self.link = other.link
        self.permission_add_member = other.permission_add_member
        self.permission_edit_details = other.permission_edit_details
        self.permission_send_message = other.permission_send_message
        self.members = other.members
        self.pending = other.pending
        self.requesting = other.requesting
        self.admins = other.admins
        self.banned = other.banned
        if self.last_seen is not None and other.last_seen is not None:
            if other.last_seen > self.last_seen:
                self.last_seen = other.last_seen
        return

    ########################
    # Sync:
    ########################
    def __sync__(self) -> None:
        """
        Sync this group with signal.
        :return: None
        """
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
        __socket_send__(self._sync_socket, json_command_str)  # Raises CommunicationError.
        response_str = __socket_receive__(self._sync_socket)  # Raises CommunicationsError.
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)  # Raises InvalidServerResponse.
        __check_response_for_error__(response_obj)  # Raises SignalError on all signal errors.

        # Get the result and update:
        raw_group: dict[str, Any] = response_obj['result'][0]
        self.__from_raw_group__(raw_group)
        return

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
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_display_name.__name__)

        # Type and value check max_len:
        if max_len is not None and not isinstance(max_len, int):
            logger.critical("Raising TypeError:")
            __type_error__("max_len", "Optional[int]", max_len)
        elif max_len is not None and max_len <= 0:
            error_message: str = "'max_len' must be greater than zero"
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)
        display_name = ''
        if self.name is not None and self.name != '' and self.name != UNKNOWN_GROUP_NAME:
            display_name = self.name
        else:
            for contact in self.members:
                display_name = display_name + contact.get_display_name() + ', '
            display_name = display_name[:-2]
        if max_len is not None and len(display_name) > max_len:
            display_name = display_name[:max_len - 3]
            display_name += '...'
        return display_name

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
