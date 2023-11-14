#!/usr/bin/env python3

from typing import Optional, Iterator, TextIO
import os
import json
import socket

from .signalCommon import phone_number_regex, uuid_regex, __type_error__, UUID_FORMAT_STR
from .signalAccount import Account
from .signalSticker import StickerPacks

DEBUG: bool = False
ACCOUNTS: list[Account] = []


# noinspection SpellCheckingInspection
class Accounts(object):
    """Class to store the known accounts."""
    supported_accounts_version: int = 2

    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 do_load: bool = False,
                 ) -> None:
        # Argument checks:
        if not isinstance(sync_socket, socket.socket):
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(command_socket, socket.socket):
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        if not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._command_socket: socket.socket = command_socket
        self._config_path: str = config_path
        self._sticker_packs: StickerPacks = sticker_packs
        self._accounts_file_path: str = os.path.join(config_path, 'data', 'accounts.json')
        if do_load:
            self.__do_load__()
        return

    def __load_accounts_file__(self) -> dict[str, int | list[dict[str, str]]]:
        # Load the accounts.json file:
        try:
            file_handle: TextIO = open(self._accounts_file_path, 'r')  # Try to open the accounts.json file.
            response_obj: dict[str, int | list[dict[str, str]]] = json.loads(file_handle.read())  # Load the json.
            file_handle.close()  # Close the file.
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = "FATAL: Failed to open '%s' for reading: %s" % (self._accounts_file_path, str(e.args))
            raise RuntimeError(error_message)
        except json.JSONDecodeError as e:
            error_message = "FATAL: Failed to load json from file '%s': %s" % (self._accounts_file_path, e.msg)
            raise RuntimeError(error_message)

        # Version check accounts file:
        if response_obj['version'] != self.supported_accounts_version:
            error_message = "FATAL: Version %i is not supported. Currently only version %i is supported." % (
                response_obj['version'], self.supported_accounts_version)
            raise RuntimeError(error_message)
        return response_obj

    def __do_load__(self) -> None:
        # Load accounts file:
        accounts_dict = self.__load_accounts_file__()
        # Parse the file and create the accounts:
        global ACCOUNTS
        ACCOUNTS = []
        count = 0
        for raw_account in accounts_dict['accounts']:
            count += 1
            account = Account(sync_socket=self._sync_socket, command_socket=self._command_socket,
                              config_path=self._config_path, sticker_packs=self._sticker_packs,
                              signal_account_path=raw_account['path'], environment=raw_account['environment'],
                              number=raw_account['number'], uuid=raw_account['uuid'], do_load=True
                              )
            ACCOUNTS.append(account)
        return

    def __sync__(self) -> list[Account]:
        global ACCOUNTS
        new_accounts: list[Account] = []
        # Load accounts file:
        accounts_dict: dict = self.__load_accounts_file__()
        # Parse the accounts file looking for a new account.
        for raw_account in accounts_dict['accounts']:
            account_found = False
            for account in ACCOUNTS:
                if account.number == raw_account['number']:
                    account_found = True
            if not account_found:
                new_account: Account = Account(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                               config_path=self._config_path, sticker_packs=self._sticker_packs,
                                               signal_account_path=raw_account['path'],
                                               environment=raw_account['environment'], number=raw_account['number'],
                                               uuid=raw_account['uuid'], do_load=True
                                               )
                ACCOUNTS.append(new_account)
                new_accounts.append(new_account)
        return new_accounts

    ##############################
    # Overrides:
    ##############################
    def __iter__(self) -> Iterator:
        """
        Return an iterator over the accounts.
        :return: Iterator: The iterator.
        """
        global ACCOUNTS
        return iter(ACCOUNTS)

    def __len__(self) -> int:
        """
        Return the length or number of accounts.
        :return: int: The len of ACCOUNTS.
        """
        global ACCOUNTS
        return len(ACCOUNTS)

    def __getitem__(self, item: int | str) -> Account:
        """
        Index accounts by int or str.
        :param item: int | str: If int: index as a list; If str: index by phone number.
        :return: Account: The selected account.
        :raises IndexError: If selected by int, and index out of range.
        :raises KeyError: If selected by str, and phone number doesn't exist.
        :raises TypeError: If item is not an int or str.
        :raises ValueError: If iteme is a str and is not in proper phone number format.
        """
        global ACCOUNTS
        if isinstance(item, int):
            return ACCOUNTS[item]  # Raises IndexError if index out of range.
        elif isinstance(item, str):
            account = self.get_by_number(item)  # Raises ValueError if the number is not in proper format.
            if account is None:
                raise KeyError("Key '%s' not found." % item)
            return account
        __type_error__('item', 'int | str', item)

    ##############################
    # Getters:
    ##############################
    @staticmethod
    def get_registered() -> list[Account]:
        """
        Get accounts that are both known and registered.
        :return: list[Account]: The registerd accounts, or an empty list if none found.
        """
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered is True]

    @staticmethod
    def get_unregistered() -> list[Account]:
        """
        Get accounts that are unregistered, but known.
        :returns: list[Account]: The unregistered accounts, or an empty list if none found.
        """
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered is False]

    @staticmethod
    def get_by_number(number: str) -> Optional[Account]:
        """
        Get an account by phone number.
        :param number: str: The phone number in format +nnnnnnnnn...
        :returns: Optional[Account]: The account found or None if not found.
        :raises: TypeError: If number is not a string.
        :raises: ValueError: If number not in proper format.
        """
        global ACCOUNTS
        # Type check:
        if not isinstance(number, str):
            __type_error__("number", "str", number)
        # Value check:
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message = "number must be in format: +nnnnnnnn..."
            raise ValueError(error_message)
       # Search for account:
        for account in ACCOUNTS:
            if account.number == number:
                return account
        return None

    @staticmethod
    def get_by_uuid(uuid: str) -> Optional[Account]:
        """
        Get an account by UUID.
        :param uuid: str: the UUID to search for.
        :return: Optional[Account]
        :raises TypeError: if the uuid is not a string.
        :raises ValueError: if the uuid is not in the correct format.
        """
        global ACCOUNTS
        # Type check:
        if not isinstance(uuid, str):
            __type_error__('uuid', 'str', uuid)
        # Value check:
        uuid_match = uuid_regex.match(uuid)
        if uuid_match is None:
            error_message = "UUID must be in format: %s" % UUID_FORMAT_STR
            raise ValueError(error_message)
        # Search for the account:
        for account in ACCOUNTS:
            if account.uuid == uuid:
                return account
        return None

    @staticmethod
    def get_by_username(username: str) -> Optional[Account]:
        """
        Get an account by username.
        :param username: str: The username to search for.
        :return: Optional[Account]: The Account object or None if not found.
        :raises TypeError: If username is not a string.
        """
        global ACCOUNTS
        # Type check:
        if not isinstance(username, str):
            __type_error__('username', 'str', username)
        # Search for the account:
        for account in ACCOUNTS:
            if account.username == username:
                return account
        return None
