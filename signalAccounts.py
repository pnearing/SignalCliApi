#!/usr/bin/env python3

from typing import Optional, Iterator
import os
import json
import socket

from .signalCommon import phone_number_regex, uuid_regex
from .signalAccount import Account
from .signalSticker import StickerPacks

DEBUG: bool = False
ACCOUNTS: list[Account] = []


class Accounts(object):
    supported_accounts_version: int = 2

    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 do_load: bool = False,
                 ) -> None:
        # TODO: Argument checks:
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
            count = count + 1
            account = Account(sync_socket=self._sync_socket, command_socket=self._command_socket,
                              config_path=self._config_path,
                              sticker_packs=self._sticker_packs, signal_account_path=raw_account['path'], do_load=True)
            ACCOUNTS.append(account)
        return

    def __sync__(self) -> list[Account]:
        global ACCOUNTS
        new_account = None
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
                # newAccounts.append(newAccount)
        return new_account

    ##############################
    # Overrides:
    ##############################
    def __iter__(self) -> Iterator:
        global ACCOUNTS
        return iter(ACCOUNTS)

    ##############################
    # Getters:
    ##############################
    def get_unregistered(self) -> list[Account]:
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered is False]

    def get_by_number(self, number: str) -> Optional[Account]:
        global ACCOUNTS
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message = "number must be in format: +nnnnnnnn..."
            raise ValueError(error_message)
        for account in ACCOUNTS:
            if account.number == number:
                return account
        return None
