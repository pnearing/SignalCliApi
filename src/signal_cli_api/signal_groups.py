#! /usr/bin/env python3
"""
File: signal_groups.py
Contain and manage a list of groups.
"""
# pylint: disable=R0913
import logging
from typing import Optional, Iterator, Any
import socket
import json

from .signal_common import (__socket_receive_blocking__, __socket_send__, __type_error__,
                            __parse_signal_response__, __check_response_for_error__,
                            UNKNOWN_GROUP_NAME, SyncTypes)
from .signal_group import SignalGroup
from .signal_contacts import SignalContacts


class SignalGroups:
    """
    Object containing all the groups acting like a list.
    """
    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_contacts: SignalContacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 do_sync: bool = False
                 ) -> None:
        """

        :param sync_socket: socket.socket: The socket to run sync commands on.
        :param command_socket: socket.socket: The socket to run commands on.
        :param config_path: str: The path to the signal-cli config directory.
        :param account_id: str: This account ID.
        :param account_contacts: SignalContacts: The account's SignalContacts object.
        :param from_dict: dict[str, Any]: Load the groups from a dict created by __to_dict__().
        :param do_sync: bool: Sync data with signal; Defaults to False.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks:
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError")
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError")
            __type_error__("account_id", "str", account_id)
        if not isinstance(account_contacts, SignalContacts):
            logger.critical("Raising TypeError")
            __type_error__("account_contacts", "SignalContacts", account_contacts)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError")
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if not isinstance(do_sync, bool):
            logger.critical("Raising TypeError")
            __type_error__("do_sync", "bool", do_sync)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to preform sync operations on."""
        self._command_socket: socket.socket = command_socket
        """The socket to preform commands on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """This account ID."""
        self._contacts: SignalContacts = account_contacts
        """This account's SignalContacts object."""
        self._groups: list[SignalGroup] = []
        """The list of SignalGroup objects."""

        # Load from dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Load from signal
        if do_sync:
            logger.debug("Syncing with signal.")
            self.__sync__()

    ############################
    # Overrides:
    ############################
    def __iter__(self) -> Iterator[SignalGroup]:
        """
        Iterate over the groups.
        :return: Iterator[SignalGroup]: The iterator.
        """
        return iter(self._groups)

    def __len__(self) -> int:
        """
        The length of groups.
        :return: int: The number of groups.
        """
        return len(self._groups)

    ############################
    # To / From Dict:
    ############################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to pass to __from_dict__()
        """
        groups_dict: dict[str, Any] = {
            "groups": []
        }
        for group in self._groups:
            groups_dict["groups"].append(group.__to_dict__())
        return groups_dict

    def __from_dict__(self, from_dict: dict[str, Any]):
        """
        Load the properties from a JSON friendly dict.
        :param from_dict: dict[str, Any] The dict provided by __to_dict__()
        :return: None
        """
        self._groups = []
        for group_dict in from_dict['groups']:
            group = SignalGroup(sync_socket=self._sync_socket,
                                command_socket=self._command_socket,
                                config_path=self._config_path,
                                account_id=self._account_id,
                                account_contacts=self._contacts,
                                from_dict=group_dict)
            self._groups.append(group)

    ###################################
    # Sync with signal:
    ##################################
    def __sync__(self) -> None:
        """
        Sync the groups with signal.
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__sync__.__name__)
        logger.debug("Syncing with signal.")
        # Create command object and json command string:
        list_groups_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listGroups",
            "params": {
                "account": self._account_id,
            }
        }
        json_command_str = json.dumps(list_groups_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)  # Raises CommunicationsError.
        # Raises CommunicationsError:
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        # Raises InvalidServerResponse:
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        __check_response_for_error__(response_obj)  # Raises SignalError.

        # Parse results:
        group_count: int = 0
        new_group_count: int = 0
        for raw_group in response_obj['result']:
            group_count += 1
            new_group = SignalGroup(sync_socket=self._sync_socket,
                                    command_socket=self._command_socket,
                                    config_path=self._config_path,
                                    account_id=self._account_id,
                                    account_contacts=self._contacts,
                                    raw_group=raw_group)
            old_group = self.get_by_id(new_group.id)
            if old_group is None:
                new_group_count += 1
                self._groups.append(new_group)
            else:
                old_group.__update__(new_group)
        logger.debug("Got %i groups, found %i new groups.", group_count, new_group_count)

    ##############################
    # Helpers:
    ##############################
    def __parse_sync_message__(self, sync_message) -> None:  # sync_message type SignalSyncMessage
        """
        Parse a sync message.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_sync_message__.__name__)
        if sync_message.sync_type == SyncTypes.BLOCKS:  # SignalSyncMessage.TYPE_BLOCKED_SYNC
            for group_id in sync_message.blocked_groups:
                _, group = self.__get_or_add__("<UNKNOWN-GROUP>", group_id)
                group.is_blocked = True
        elif sync_message.sync_type == SyncTypes.GROUPS:
            self.__sync__()
        else:
            error_message: str = ("groups can only parse sync message of types: SyncTypes.BLOCKS "
                                  f"or SyncTypes.GROUPS not {str(sync_message.sync_type)}")
            logger.critical("Raising TypeError(%s).", error_message)
            raise TypeError(error_message)

    ##############################
    # Getters:
    ##############################
    def get_by_id(self, group_id: str) -> Optional[SignalGroup]:
        """
        Get a group by id.
        :param group_id: str: The id to search for.
        :returns: Optional[group]: The group, or None if not found.
        :raises: TypeError: If group_id is not a string.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_id.__name__)
        if not isinstance(group_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("group_id", "str", group_id)
        # Search for group:
        for group in self._groups:
            if group.id == group_id:
                return group
        return None

    def get_by_name(self, name: str) -> Optional[SignalGroup]:
        """
        Get a group given a name.
        :param name: str: The name of the group to search for.
        :returns: Optional[group]: The group, or None if not found.
        :raises: TypeError: If name is not a string.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_name.__name__)
        if not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "str", name)
        # Search for the group:
        for group in self._groups:
            if group.name == name:
                return group
        return None

    ####################################
    # Helpers:
    ###################################
    def __get_or_add__(self,
                       group_id: str,
                       name: str = UNKNOWN_GROUP_NAME
                       ) -> tuple[bool, SignalGroup]:
        """
        Get an existing group, or if not found, add it to the group list.
        :param group_id: str: The group ID.
        :param name: str: The group name; Defaults to UNKNOWN_GROUP_NAME.
        :return: tuple[bool, SignalGroup]: The first element is True if added, False if not;
            And the second element is either the existing SignalGroup object, or the newly added
            SignalGroup object.
        """
        old_group = self.get_by_id(group_id)
        if old_group is not None:
            return False, old_group
        new_group = SignalGroup(sync_socket=self._sync_socket,
                                command_socket=self._command_socket,
                                config_path=self._config_path,
                                account_id=self._account_id,
                                account_contacts=self._contacts,
                                name=name,
                                group_id=group_id)
        self._groups.append(new_group)
        return True, new_group
