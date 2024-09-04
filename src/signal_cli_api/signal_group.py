#!/usr/bin/env python3
"""
File: signal_group.py
Manage and maintain a single group.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915, C0206
import logging
from datetime import timedelta
from typing import TypeVar, Optional, Any
import socket
import json

# from . import SignalTypingMessage
from .signal_common import (__socket_receive_blocking__, __socket_send__, __type_error__,
                            __parse_signal_response__, __check_response_for_error__,
                            UNKNOWN_GROUP_NAME, RecipientTypes, TypingStates)
from .signal_contacts import SignalContacts
from .signal_contact import SignalContact
from .signal_recipient import SignalRecipient
from .signal_timestamp import SignalTimestamp

Self = TypeVar("Self", bound="SignalGroup")


class SignalGroup(SignalRecipient):
    """An object containing a single group."""
    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_contacts: SignalContacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_group: Optional[dict[str, Any]] = None,
                 group_id: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 is_blocked: bool = False,
                 is_member: bool = False,
                 expiration: Optional[int | timedelta] = None,
                 link: Optional[str] = None,
                 members: list[SignalContact] = None,
                 pending_members: list[SignalContact] = None,
                 requesting_members: list[SignalContact] = None,
                 admins: list[SignalContact] = None,
                 banned: list[SignalContact] = None,
                 permission_add_member: Optional[str] = None,
                 permission_edit_details: Optional[str] = None,
                 permission_send_message: Optional[str] = None,
                 last_seen: Optional[SignalTimestamp] = None,
                 ) -> None:
        """
        Initialize a SignalGroup.
        :param sync_socket: socket.socket: The socket to run sync commands on.
        :param config_path: str: The path to the signal-cli config directory.
        :param account_id: str: This account ID.
        :param account_contacts: The account's SignalContacts object.
        :param from_dict: dict[str, Any]: Load from a dict provided by __to_dict__()
        :param raw_group: dict[str, Any]: Load from a dict provided by signal.
        :param group_id: Optional[str]: The group ID.
        :param name: Optional[str]: The group name.
        :param description: Optional[str]: The group description.
        :param is_blocked: bool: If this group is blocked.
        :param is_member: bool: If this account is a member of the group.
        :param expiration: Optional[int | timedelta]: The expiration time of the group.
        :param link: Optional[str]: The join link of the group.
        :param members: list[SignalContact]: Existing members.
        :param pending_members: list[SignalContact]: Pending members.
        :param requesting_members: list[SignalContact] Requesting members.
        :param admins: list[SignalContact]: Admin members.
        :param banned: list[SignalContact]: Banned members.
        :param permission_add_member: Optional[str]: Add member permissions.
        :param permission_edit_details: Optional[str]: Edit details permissions.
        :param permission_send_message: Optional[str]: Permission to send messages.
        :param last_seen: Optional[SignalTimestamp]: The time this group was last seen.
        """
        # Super:
        super().__init__(recipient_type=RecipientTypes.GROUP)

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
        if not isinstance(account_contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("account_contacts", "SignalContacts", account_contacts)
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
        if expiration is not None and not isinstance(expiration, (int, timedelta)):
            logger.critical("Raising TypeError:")
            __type_error__("expiration", "Optional[int | timedelta]", expiration)
        if link is not None and not isinstance(link, str):
            logger.critical("Raising TypeError:")
            __type_error__("link", "Optional[str]", link)
        if members is not None and not isinstance(members, list):
            logger.critical("Raising TypeError:")
            __type_error__("members", "Optional[list[SignalContact]]", members)
        elif members is not None:
            for i, member in enumerate(members):
                if not isinstance(member, SignalContact):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"members[{i}]", "SignalContact", member)
        if pending_members is not None and not isinstance(pending_members, list):
            logger.critical("Raising TypeError:")
            __type_error__("pending_members", "Optional[list[SignalContact]]", pending_members)
        elif pending_members is not None:
            for i, member in enumerate(pending_members):
                if not isinstance(member, SignalContact):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"pending_members[{i}]", "SignalContact", member)
        if requesting_members is not None and not isinstance(requesting_members, list):
            logger.critical("Raising TypeError:")
            __type_error__("requesting_members", "Optional[list[SignalContact]]",
                           requesting_members)
        elif requesting_members is not None:
            for i, member in enumerate(requesting_members):
                if not isinstance(member, SignalContact):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"requesting_members[{i}]", "SignalContact", member)
        if admins is not None and not isinstance(admins, list):
            logger.critical("Raising TypeError:")
            __type_error__("admins", "Optional[list[str]]", admins)
        elif admins is not None:
            for i, admin in enumerate(admins):
                if not isinstance(admin, SignalContact):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"admins[{i}]", "SignalContact", admin)
        if banned is not None and not isinstance(banned, list):
            logger.critical("Raising TypeError:")
            __type_error__("banned", "Optional[list[SignalContact]]", banned)
        elif banned is not None:
            for i, contact in enumerate(banned):
                if not isinstance(contact, SignalContact):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"banned[{i}]", "SignalContact", contact)
        if permission_add_member is not None and not isinstance(permission_add_member, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_add_member", "Optional[str]", permission_add_member)
        if permission_edit_details is not None and not isinstance(permission_edit_details, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_edit_details", "Optional[str]", permission_edit_details)
        if permission_send_message is not None and not isinstance(permission_send_message, str):
            logger.critical("Raising TypeError:")
            __type_error__("permission_send_message", "Optional[str]", permission_send_message)
        if last_seen is not None and not isinstance(last_seen, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("last_seen", "Optional[SignalTimestamp]", last_seen)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to run sync operations on."""
        self._command_socket: socket.socket = command_socket
        """The socket to run command operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """This account ID."""
        self._contacts: SignalContacts = account_contacts
        """This account's SignalContacts object."""
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
        self.expiration: Optional[int] = None
        """The expiration time as a timedelta."""
        if expiration is not None:
            if isinstance(expiration, int):
                self.expiration = timedelta(seconds=expiration)
            else:  # Expiration is a timedelta:
                self.expiration = expiration
        self.link: Optional[str] = link
        """The join link of this group."""
        self.members: list[SignalContact] = []
        """The current members of this group."""
        if members is not None:
            self.members = members
        self.pending: list[SignalContact] = []
        """The pending members of this group."""
        if pending_members is not None:
            self.pending = pending_members
        self.requesting: list[SignalContact] = []
        """The requesting members of the group."""
        if requesting_members is not None:
            self.requesting = requesting_members
        self.admins: list[SignalContact] = []
        """The admins of the group."""
        if admins is not None:
            self.admins = admins
        self.banned: list[SignalContact] = []
        """The banned members of the group."""
        if banned is not None:
            self.banned = banned
        self.permission_add_member: str = permission_add_member
        """The permissions to add a member."""
        self.permission_edit_details: str = permission_edit_details
        """The permission to edit group details."""
        self.permission_send_message: str = permission_send_message
        """The permissions to send a message to the group."""
        self.last_seen: Optional[SignalTimestamp] = last_seen
        """The date / time this was last seen."""
        self.typing_members: list[SignalContact] = []
        """List of contact typing in this group."""

        # Parse from_dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Parse raw_group:
        elif raw_group is not None:
            logger.debug("Loading from raw group.")
            self.__from_raw_group__(raw_group)
        # SignalGroup object was created without raw_group or from_dict, see if we can get
        # details from signal:
        else:
            if self.id is not None:
                self.__sync__()
                self._is_valid = True
            else:
                self._is_valid = False

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
            self.expiration = timedelta(seconds=raw_group['messageExpirationTime'])
        self.link = raw_group['groupInviteLink']
        self.permission_add_member = raw_group['permissionAddMember']
        self.permission_edit_details = raw_group['permissionEditDetails']
        self.permission_send_message = raw_group['permissionSendMessage']
        # Parse members:
        self.members = []
        for contact_dict in raw_group['members']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'],
                                                       uuid=contact_dict['uuid'])
            self.members.append(contact)
        # Parse pending:
        self.pending = []
        for contact_dict in raw_group['pendingMembers']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'],
                                                       uuid=contact_dict['uuid'])
            self.pending.append(contact)
        # Parse requesting:
        self.requesting = []
        for contact_dict in raw_group['requestingMembers']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'],
                                                       uuid=contact_dict['uuid'])
            self.requesting.append(contact)
        # Parse admins:
        self.admins = []
        for contact_dict in raw_group['admins']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'],
                                                       uuid=contact_dict['uuid'])
            self.admins.append(contact)
        # Parse banned:
        self.banned = []
        for contact_dict in raw_group['banned']:
            _, contact = self._contacts.__get_or_add__(number=contact_dict['number'],
                                                       uuid=contact_dict['uuid'])
            self.banned.append(contact)

    ######################
    # Overrides:
    ######################
    def __eq__(self, other: Self) -> bool:
        """
        Generate equality.
        :param other: SignalGroup: The group to compare to.
        :return: bool: True the groups are equal, False they are not.
        :raises TypeError: If other is not a SignalGroup object.
        """
        if super().__eq__(other):
            self.__update__(other)
            return True
        if isinstance(other, SignalGroup):
            if self.id == other.id:
                self.__update__(other)
            return True
        return False

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
            'expiration': None,
            'link': self.link,
            'permAddMember': self.permission_add_member,
            'permEditDetails': self.permission_edit_details,
            'permSendMessage': self.permission_send_message,
            'members': [],
            'pending': [],
            'requesting': [],
            'admins': [],
            'banned': [],
            'lastSeen': None,
        }
        if self.expiration is not None:
            group_dict['expiration'] = self.expiration.total_seconds()
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
        if self.last_seen is not None:
            group_dict['lastSeen'] = self.last_seen.__to_dict__()
        # Add the parent keys
        recipient_dict = super().__to_dict__()
        for key in recipient_dict:
            group_dict[key] = recipient_dict[key]
        return group_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        self.id = from_dict['id']
        self.name = from_dict['name']
        self.description = from_dict['description']
        self.is_blocked = from_dict['isBlocked']
        self.is_member = from_dict['isMember']
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])
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
        # Parse last seen:
        self.last_seen = None
        if from_dict['lastSeen'] is not None:
            self.last_seen = SignalTimestamp(from_dict=from_dict['lastSeen'])

    #################
    # Helpers:
    #################
    def __update__(self, other: Self) -> None:
        """
        Overwrite properties with an update from signal.
        :param other: SignalGroup: The most recent copy of the group.
        :return: None
        """
        super().__update__(other)
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
            self.last_seen = max(self.last_seen, other.last_seen)
        elif self.last_seen is None and other.last_seen is not None:
            self.last_seen = other.last_seen

    def __parse_typing_message__(self, message) -> None:  # Message type: SignalTypingMessage
        """
        Parse a typing message for the group.
        :param message: SignalTypingMessage: The message to parse.
        :return: None
        """
        if message.action == TypingStates.STARTED:
            if message.sender not in self.typing_members:
                self.typing_members.append(message.sender)
        elif message.action == TypingStates.STOPPED:
            if message.sender in self.typing_members:
                self.typing_members.remove(message.sender)

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
        response_str = __socket_receive_blocking__(self._sync_socket)  # Raises CommunicationsError.
        # Raises InvalidServerResponse:
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        __check_response_for_error__(response_obj)  # Raises SignalError on all signal errors.

        # Get the result and update:
        raw_group: dict[str, Any] = response_obj['result'][0]
        self.__from_raw_group__(raw_group)

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
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        display_name = ''
        if self.name is not None and self.name != '' and self.name != UNKNOWN_GROUP_NAME:
            # logger.debug("Group.name: %s" % self.name)
            display_name = self.name
        else:
            for contact in self.members:
                display_name = display_name + contact.get_display_name() + ', '
            display_name = display_name[:-2]
            # logger.debug("Built name: %s" % display_name)
        if max_len is not None and len(display_name) > max_len:
            display_name = display_name[:max_len - 3]
            display_name += '...'
        return display_name

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

####################################################
# Properties:
####################################################
    @property
    def is_typing(self) -> bool:
        """
        Is anybody typing in the group?
        :return: bool
        """
        return len(self.typing_members) > 0
