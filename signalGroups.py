#! /usr/bin/env python3

from typing import Optional, Iterator
import socket
import json

from .signalCommon import __socket_receive__, __socket_send__
from .signalGroup import Group
from .signalContacts import Contacts

# from signalSyncMessage import SyncMessage

DEBUG: bool = True


class Groups(object):
    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_contacts: Contacts,
                 from_dict: Optional[dict] = None,
                 do_sync: bool = False
                 ) -> None:
        # TODO: Arg checks:
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._config_path: str = config_path
        self._account_id: str = account_id
        self._contacts: Contacts = account_contacts
        self._groups: list[Group] = []
        # Load from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Load from signal
        if do_sync:
            self.__sync__()
        return

    ############################
    # Overrides:
    ############################
    def __iter__(self) -> Iterator[Group]:
        return iter(self._groups)

    ############################
    # To / From Dict:
    ############################
    def __to_dict__(self) -> dict[str, object]:
        groups_dict = {
            "groups": []
        }
        for group in self._groups:
            groups_dict["groups"].append(group.__to_dict__())
        return groups_dict

    def __from_dict__(self, from_dict: dict):
        self._groups = []
        for groupDict in from_dict['groups']:
            group = Group(sync_socket=self._sync_socket, config_path=self._config_path, account_id=self._account_id,
                          account_contacts=self._contacts, from_dict=groupDict)
            self._groups.append(group)
        return

    ###################################
    # Sync with signal:
    ##################################
    def __sync__(self) -> bool:
        # Create command object and json command string:
        list_groups_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "listGroups",
            "params": {
                "account": self._account_id,
            }
        }
        json_command_str = json.dumps(list_groups_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_string = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_string)
        # print(responseObj)
        # Check for error:
        if 'error' in response_obj.keys():
            return False
        # Parse result:
        group_added = False
        for raw_group in response_obj['result']:
            new_group = Group(sync_socket=self._sync_socket, config_path=self._config_path, account_id=self._account_id,
                              account_contacts=self._contacts, raw_group=raw_group)
            old_group = self.get_by_id(new_group.id)
            if old_group is None:
                self._groups.append(new_group)
                group_added = True
            else:
                old_group.__merge__(new_group)

        return group_added

    ##############################
    # Helpers:
    ##############################
    def __parse_sync_message__(self, sync_message) -> None:  # sync_message type SyncMessage
        if sync_message.sync_type == 5:  # SyncMessage.TYPE_BLOCKED_SYNC
            for group_id in sync_message.blocked_groups:
                added, group = self.__get_or_add__("<UNKNOWN-GROUP>", group_id)
                group.is_blocked = True
        else:
            errorMessage = "groups can only parse sync message of type: SyncMessage.TYPE_BLOCKED_SYNC."
            raise TypeError(errorMessage)

    ##############################
    # Getters:
    ##############################
    def get_by_id(self, group_id: str) -> Optional[Group]:
        for group in self._groups:
            if group.id == group_id:
                return group
        return None

    def get_by_name(self, name: str) -> Optional[Group]:
        for group in self._groups:
            if group.name == name:
                return group
        return None

    ####################################
    # Helpers:
    ###################################
    def __get_or_add__(self, name: str, group_id: str) -> tuple[bool, Group]:
        # self.__sync__()
        old_group = self.get_by_id(group_id)
        if old_group is not None:
            return False, old_group
        new_group = Group(sync_socket=self._sync_socket, config_path=self._config_path, account_id=self._account_id,
                          account_contacts=self._contacts, name=name, group_id=group_id)
        self._groups.append(new_group)
        return True, new_group
