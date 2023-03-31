#!/usr/bin/env python3

from typing import Optional, Iterator
import os
import json
import socket

from .signalCommon import phone_number_regex, uuid_regex, __type_error__
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

    def __load_accounts_file__(self) -> dict:
        # Try to open the accounts file:
        try:
            file_handle = open(self._accounts_file_path, 'r')
        except Exception as err:
            error_message = "FATAL: Failed to open '%s' for reading: %s" % (self._accounts_file_path, str(err.args))
            raise RuntimeError(error_message)
        # Try to load the json from the file:
        try:
            response_obj: dict = json.loads(file_handle.read())
        except json.JSONDecodeError as err:
            error_message = "FATAL: Failed to load json from file '%s': %s" % (self._accounts_file_path, err.msg)
            raise RuntimeError(error_message)
        file_handle.close()
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
                              signal_account_path=raw_account['path'], do_load=True)
            ACCOUNTS.append(account)
        return

    def __sync__(self) -> list[Account]:
        global ACCOUNTS
        new_account: Optional[Account] = None
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
                new_account = Account(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                      config_path=self._config_path, sticker_packs=self._sticker_packs,
                                      signal_account_path=raw_account['path'], do_load=True)
                ACCOUNTS.append(new_account)
                new_accounts.append(new_account)
        return new_accounts

    ##############################
    # Overrides:
    ##############################
    def __iter__(self) -> Iterator:
        global ACCOUNTS
        return iter(ACCOUNTS)

    ##############################
    # Getters:
    ##############################
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
        # noinspection SpellCheckingInspection
        """
                Get an account by phone number.
                :param number: str: The phone number in format +nnnnnnnnn...
                :returns: Optional[Account]: The account found or None if not found.
                :raises: TypeError: If number not a string.
                :raises: ValueError: If number not in proper format.
                """
        global ACCOUNTS
        if not isinstance(number, str):
            __type_error__("number", "str", number)
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message = "number must be in format: +nnnnnnnn..."
            raise ValueError(error_message)
        for account in ACCOUNTS:
            if account.number == number:
                return account
        return None
