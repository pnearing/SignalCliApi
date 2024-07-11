#!/usr/bin/env python3
"""
File: signalAccounts.py
Maintain and manage a list of accounts.
"""
from typing import Optional, Iterator, TextIO
import os
import json
import socket
import logging

from .signalCommon import phone_number_regex, uuid_regex, __type_error__, UUID_FORMAT_STR, __type_err_msg__, \
    NUMBER_FORMAT_STR
from .signalAccount import SignalAccount
from .signalSticker import SignalStickerPacks


ACCOUNTS: list[SignalAccount] = []
"""The main accounts list."""


# noinspection SpellCheckingInspection
class SignalAccounts(object):
    """
    Class to store the known accounts.
    """
    supported_accounts_versions: tuple[int] = (2,)
    """Supported accounts.json versions."""

    def __init__(self,
                 sync_socket: socket.socket,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: SignalStickerPacks,
                 do_load: bool = False,
                 ) -> None:
        """
        Initialize the accounts:
        :param sync_socket: socket.socket: The socket to run sync operations on.
        :param command_socket: socket.socket: The socket to run commands on.
        :param config_path: str: The path to the signal-cli direcotry.
        :param sticker_packs: SignalStickerPacks: The loaded SignalStickerPacks object.
        :param do_load: bool: Load from disk right away; Defaults to False.
        """
        # Super:
        object.__init__(self)

        # Setup logging:
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialize")
        # Argument checks:
        self.logger.debug("Type checks.")
        if not isinstance(sync_socket, socket.socket):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('sync_socket', 'socket.socket', sync_socket))
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(command_socket, socket.socket):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('command_socket', 'socket.socket', command_socket))
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('config_path', 'str', config_path))
            __type_error__("config_path", "str", config_path)
        if not isinstance(do_load, bool):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('do_load', 'bool', do_load))
            __type_error__("do_load", "bool", do_load)
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The sync socket to use."""
        self._command_socket: socket.socket = command_socket
        """The command socket to use."""
        self._config_path: str = config_path
        """The path to the signal-cli config directory."""
        self._sticker_packs: SignalStickerPacks = sticker_packs
        """The known sticker packs."""
        self._accounts_file_path: str = os.path.join(config_path, 'data', 'accounts.json')
        """The full path to the accounts.json file."""
        if do_load:
            self.__do_load__()
        return

    def __load_accounts_file__(self) -> dict[str, int | list[dict[str, str]]]:
        """
        Load the json data from the accounts.json file and return the resulting dict.
        :return: dict[str, int | list[dict[str, str]]]: The returned data.
        :raises RuntimeError: On failure to open file or json decode error.
        """
        # Load the accounts.json file:
        try:
            self.logger.info("Loading accounts.json...")
            file_handle: TextIO = open(self._accounts_file_path, 'r')  # Try to open the accounts.json file.
            response_obj: dict[str, int | list[dict[str, str]]] = json.loads(file_handle.read())  # Load the json.
            file_handle.close()  # Close the file.
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = "Failed to open '%s' for reading: %s" % (self._accounts_file_path, str(e.args))
            self.logger.critical(error_message)
            raise RuntimeError(error_message)
        except json.JSONDecodeError as e:
            error_message = "Failed to load JSON from '%s': %s" % (self._accounts_file_path, e.msg)
            self.logger.critical(error_message)
            raise RuntimeError(error_message)

        # Store account.json version and check to see if supported:
        self.version: int = response_obj['version']
        self.logger.debug("Version check accounts.json file: '%i' in '%s'."
                          % (self.version, str(self.supported_accounts_versions)))
        if self.version not in self.supported_accounts_versions:
            error_message = "Version %i is not supported. Currently supported versions: '%s'." % (
                response_obj['version'], str(self.supported_accounts_versions))
            self.logger.critical(error_message)
            raise RuntimeError(error_message)
        return response_obj

    def __do_load__(self) -> None:
        """
        Load the accounts from the accounts.json file.
        :return: None
        """
        self.logger.info("Loading accounts...")
        # Load accounts file:
        accounts_dict = self.__load_accounts_file__()
        # Parse the file and create the accounts:
        global ACCOUNTS
        ACCOUNTS = []
        count: int = 0
        for raw_account in accounts_dict['accounts']:
            count += 1
            account = SignalAccount(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                    config_path=self._config_path, sticker_packs=self._sticker_packs,
                                    signal_account_path=raw_account['path'], environment=raw_account['environment'],
                                    number=raw_account['number'], uuid=raw_account['uuid'], do_load=True
                                    )
            self.logger.info("Loaded account: '%s'" % account.number)
            ACCOUNTS.append(account)
        self.logger.info("Loaded %i accounts." % count)
        return

    def __sync__(self) -> list[SignalAccount]:
        """
        Reread the accounts.json and load any new accounts.
        :return: list[SignalAccount]: The list of new accounts, an empty list if none found.
        """
        global ACCOUNTS
        self.logger.info("Accounts sync started...")
        new_accounts: list[SignalAccount] = []
        # Load accounts file:
        accounts_dict: dict = self.__load_accounts_file__()
        # Parse the accounts file looking for a new account.
        for raw_account in accounts_dict['accounts']:
            account_found = False
            for account in ACCOUNTS:
                if account.number == raw_account['number']:
                    account_found = True
            if not account_found:
                new_account: SignalAccount = SignalAccount(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                                           config_path=self._config_path, sticker_packs=self._sticker_packs,
                                                           signal_account_path=raw_account['path'],
                                                           environment=raw_account['environment'], number=raw_account['number'],
                                                           uuid=raw_account['uuid'], do_load=True
                                                           )
                self.logger.info("New account found: '%s'" % new_account.number)
                ACCOUNTS.append(new_account)
                new_accounts.append(new_account)
        self.logger.info("Found %i new accounts." % len(new_accounts))
        return new_accounts

    ##############################
    # Overrides:
    ##############################
    def __iter__(self) -> Iterator[SignalAccount]:
        """
        Return an iterator over the accounts.
        :return: Iterator[SignalAccount]: The iterator.
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

    def __getitem__(self, item: int | str) -> SignalAccount:
        """
        Index accounts by int or str.
        :param item: int | str: If int: index as a list; If str: index by phone number.
        :return: SignalAccount: The selected account.
        :raises IndexError: If selected by int, and index out of range.
        :raises KeyError: If selected by str, and phone number doesn't exist.
        :raises TypeError: If item is not an int or str.
        :raises ValueError: If iteme is a str and is not in proper phone number format.
        """
        global ACCOUNTS
        self.logger.debug("__getitem__ started.")
        if isinstance(item, int):
            try:
                return ACCOUNTS[item]  # Raises IndexError if index out of range.
            except IndexError as e:
                self.logger.error("IndexError: %s" % str(e.args))
                raise e
        elif isinstance(item, str):
            try:
                account = self.get_by_number(item)  # Raises ValueError if the number is not in proper format.
            except ValueError as e:
                self.logger.error("ValueError: %s" % str(e.args))
                raise e
            if account is None:
                error_message: str = "Key '%s' not found." % item
                self.logger.error("KeyError: %s" % error_message)
                raise KeyError(error_message)
            return account
        self.logger.error("TypeError:")
        self.logger.error(__type_err_msg__('item', 'int | str', item))
        __type_error__('item', 'int | str', item)

    ##############################
    # Getters:
    ##############################
    @staticmethod
    def get_registered() -> list[SignalAccount]:
        """
        Get accounts that are both known and registered.
        :return: list[SignalAccount]: The registerd accounts, or an empty list if none found.
        """
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered is True]

    @staticmethod
    def get_unregistered() -> list[SignalAccount]:
        """
        Get accounts that are unregistered, but known.
        :returns: list[SignalAccount]: The unregistered accounts, or an empty list if none found.
        """
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered is False]

    def get_by_number(self, number: str) -> Optional[SignalAccount]:
        """
        Get an account by phone number.
        :param number: str: The phone number in format +nnnnnnnnn...
        :returns: Optional[SignalAccount]: The account found or None if not found.
        :raises: TypeError: If number is not a string.
        :raises: ValueError: If number not in proper format.
        """
        global ACCOUNTS
        self.logger.debug("get_by_number started.")
        # Type check:
        if not isinstance(number, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('number', 'str', number))
            __type_error__("number", "str", number)
        # Value check:
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message = "number: '%s', must be in format: %s" % (number, NUMBER_FORMAT_STR)
            self.logger.critical("ValueError: %s" % error_message)
            raise ValueError(error_message)
        # Search for the account:
        for account in ACCOUNTS:
            if account.number == number:
                self.logger.debug("Account number '%s' found." % number)
                return account
        self.logger.debug("Account number '%s' NOT found." % number)
        return None

    def get_by_uuid(self, uuid: str) -> Optional[SignalAccount]:
        """
        Get an account by UUID.
        :param uuid: str: the UUID to search for.
        :return: Optional[SignalAccount]
        :raises TypeError: if the uuid is not a string.
        :raises ValueError: if the uuid is not in the correct format.
        """
        global ACCOUNTS
        self.logger.debug("get_by_uuid started.")
        # Type check:
        if not isinstance(uuid, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('uuid', 'str', uuid))
            __type_error__('uuid', 'str', uuid)
        # Value check:
        uuid_match = uuid_regex.match(uuid)
        if uuid_match is None:
            error_message = "UUID: '%s',  must be in format: %s" % (uuid, UUID_FORMAT_STR)
            self.logger.critical("ValueError: %s" % error_message)
            raise ValueError(error_message)
        # Search for the account:
        for account in ACCOUNTS:
            if account.uuid == uuid:
                self.logger.debug("Account uuid '%s' found." % uuid)
                return account
        self.logger.debug("Account uuid '%s' NOT found." % uuid)
        return None

    def get_by_username(self, username: str) -> Optional[SignalAccount]:
        """
        Get an account by username.
        :param username: str: The username to search for.
        :return: Optional[SignalAccount]: The SignalAccount object or None if not found.
        :raises TypeError: If username is not a string.
        """
        global ACCOUNTS
        self.logger.debug("get_by_username started.")
        # Type check:
        if not isinstance(username, str):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('username', 'str', username))
            __type_error__('username', 'str', username)
        # Search for the account:
        for account in ACCOUNTS:
            if account.username == username:
                self.logger.debug("Account username '%s' found." % username)
                return account
        self.logger.debug("Account username '%s' NOT found.")
        return None

    ##########################
    # Properties:
    ##########################
    @property
    def num_accounts(self) -> int:
        """
        The total number of accounts.
        :return: int: The total number of accounts.
        """
        return self.__len__()

    @property
    def num_registered(self) -> int:
        """
        The number of registered accounts.
        :return: int: The number of registered accounts.
        """
        return len(self.get_registered())

    @property
    def num_unregistered(self) -> int:
        """
        The nubmer of unregistered accounts.
        :return: int: The number of unregistered accounts.
        """
        return len(self.get_unregistered())