#!/usr/bin/env python3
"""
File: signal_contacts.py
Manage the signal contacts.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915, W0511
from typing import Optional, Iterator, Any, Match
import os
import json
import socket
import logging

from .signal_common import (__type_error__, __socket_receive_blocking__, __socket_send__,
                            PHONE_NUMBER_REGEX, UUID_REGEX, NUMBER_FORMAT_STR, UUID_FORMAT_STR,
                            SELF_CONTACT_NAME, __parse_signal_response__,
                            __check_response_for_error__, UNKNOWN_CONTACT_NAME, SyncTypes)
from .signal_contact import SignalContact
from .signal_exceptions import ParameterError, InvalidDataFile


class SignalContacts:
    """Object to contain a contact list."""

    def __init__(self,
                 command_socket: socket.socket,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_path: str,
                 do_load: bool = False,
                 do_sync: bool = False,
                 ) -> None:
        """
        Initialize the contacts.
        :param command_socket: socket.socket: The socket to use for commands.
        :param sync_socket: socket.socket: The socket to use for sync operations.
        :param config_path: str: The path to the signal-cli config directory.
        :param account_id: str: The account ID, Either the number or the uuid.
        :param account_path: str: The path to the account data directory.
        :param do_load: bool: Load contacts from disk.
        :param do_sync: bool: Load contact from signal, and merge with existing contacts.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        logger.info("Initialize.")

        # Argument checks:
        logger.debug("Type checks...")
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__('command_socket', 'socket.socket', command_socket)
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if not isinstance(account_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_path", "str", account_path)
        if not isinstance(do_load, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_load", "bool", do_load)
        if not isinstance(do_sync, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_sync", "bool", do_sync)

        # Value checks:
        if not os.path.exists(config_path):
            error_message: str = f"config_path: '{config_path}', does not exist."
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        if not os.path.exists(account_path):
            error_message: str = f"account_path: '{account_path}', does not exist."
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to run commands on."""
        self._sync_socket: socket.socket = sync_socket
        """The socket to use for sync operations."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """The account ID, either number or uuid."""
        self._account_path: str = account_path
        """The full path to the account data directory."""
        self._filename: str = "contacts.json"
        """The filename to use for the contacts JSON file."""
        self._json_file_path: str = os.path.join(self._account_path, self._filename)
        """The full path to this accounts contacts JSON file."""
        self._contacts: list[SignalContact] = []
        """The main list of contacts."""

        # Load from file:
        if do_load:
            if os.path.exists(self._json_file_path):
                logger.debug("Contacts JSON file exists, loading contacts from disk.")
                self.__load__()
            else:
                warning_message: str = (f"Creating empty contacts.json file for"
                                        f"account: {self._account_id}")
                logger.warning(warning_message)
                self.__save__()

        # Sync with signal:
        if do_sync:
            logger.debug("Syncing contacts with signal.")
            self.__sync__()
            logger.debug("Saving merged contact data.")
            self.__save__()

        # Search for self-contact, and create if not found:
        logger.debug("Search for self-contact...")
        self_contact: Optional[SignalContact] = self.get_by_id(self._account_id)
        if self_contact is None:
            logger.debug("No self-contact found, adding...")
            self.add(SELF_CONTACT_NAME, self._account_id)
        else:
            logger.debug("self-contact found, ensuring name is '%s'", SELF_CONTACT_NAME)
            self_contact.set_name(SELF_CONTACT_NAME)
        self.__save__()
        logger.info("Initialization complete.")

    ##########################
    # Overrides:
    ##########################
    def __iter__(self) -> Iterator[SignalContact]:
        """
        Iterate over the contacts.
        :return: Iterator
        """
        return iter(self._contacts)

    def __len__(self) -> int:
        """
        The len of the contact list.
        :return: int: The number of contacts.
        """
        return len(self._contacts)

    def __getitem__(self, index: int | str) -> SignalContact:
        """
        Index with square brackets, returning a contact.
        :param index: int | str: The index of the contact if int, the ID of the contact if str.
        :return: SignalContact: The SignalContact object.
        :raises TypeError: If the index is not int or str.
        :raises ValueError: If the index is a string, and not a valid number or UUID format.
        :raises IndexError: If index is an integer and not a valid index.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__getitem__.__name__)
        if isinstance(index, int):
            return self._contacts[index]  # Raises IndexError
        if isinstance(index, str):
            number_match = PHONE_NUMBER_REGEX.match(index)
            uuid_match = UUID_REGEX.match(index)
            if number_match is not None:
                contact = self.get_by_number(index)
                if contact is not None:
                    return contact
                error_message: str = f"number '{index}' not found"
                logger.critical("Raising IndexError(%s).", error_message)
                raise IndexError(error_message)
            if uuid_match is not None:
                contact = self.get_by_uuid(index)
                if contact is not None:
                    return contact
                error_message: str = f"UUID '{index}' not found."
                logger.critical("Raising IndexError(%s).", error_message)
                raise IndexError(error_message)

            error_message: str = (f"index must be of format '{NUMBER_FORMAT_STR}' "
                                  f"or '{UUID_FORMAT_STR}'")
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        logger.critical("Raising TypeError:")
        __type_error__(index, "int | str", index)

    ##########################
    # To / From Dict:
    ##########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Generate a JSON friendly dict to save.
        :return: dict[str, Any]: The JSON friendly dict.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__to_dict__.__name__)
        contacts_dict: dict[str, Any] = {
            "contacts": [],
        }
        count: int = 0
        for contact in self._contacts:
            contacts_dict['contacts'].append(contact.__to_dict__())
            count += 1
        logger.debug("Stored %i contacts in the dict.", count)
        return contacts_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load contacts from a JSON friendly dict created by __to_dict_().
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)
        self._contacts = []
        count: int = 0
        for contact_dict in from_dict['contacts']:
            contact = SignalContact(command_socket=self._command_socket,
                                    sync_socket=self._sync_socket,
                                    config_path=self._config_path,
                                    account_id=self._account_id,
                                    account_path=self._account_path,
                                    from_dict=contact_dict)
            self._contacts.append(contact)
            count += 1
        logger.debug("Loaded %i contacts from the dict.", count)

    ##############################
    # Load / Save:
    ##############################
    def __save__(self) -> None:
        """
        Save the contacts a JSON file.
        :return: None
        :raises RuntimeError: On an error while opening file.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__save__.__name__)
        logger.info("Saving contacts to disk: '%s'.", self._json_file_path)
        # Create the 'contacts' object, and json string:
        contacts_obj: dict[str, Any] = self.__to_dict__()
        contacts_json: str = json.dumps(contacts_obj, indent=4)
        # Try to open the file and write the JSON:
        try:
            logger.debug("Opening file...")
            with open(self._json_file_path, 'w', encoding='utf-8') as file_handle:
                logger.debug("Writing JSON to file...")
                file_handle.write(contacts_json)
            logger.debug("File closed.")
        except (OSError, PermissionError) as e:
            error_message: str = (f"Couldn't open contacts file '{self._json_file_path}' for "
                                  f"writing: {str(e.args)}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message) from e
        logger.info("Contacts successfully saved to disk.")

    def __load__(self) -> None:
        """
        Load the contact from the JSON contacts file.
        :return: None
        :raises RuntimeError: On failure to open the file.
        :raises InvalidDataFile: On failure to load JSON from the file.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__load__.__name__)
        logger.info("Loading contacts from disk: '%s'", self._json_file_path)
        # Try and open the file for reading:
        try:
            with open(self._json_file_path, 'r', encoding='utf-8') as file_handle:
                contacts_dict: dict[str, Any] = json.loads(file_handle.read())
        except (FileNotFoundError, OSError, PermissionError) as e:
            error_message: str = (f"Couldn't open '{self._json_file_path}' for"
                                  f"reading: {str(e.args)}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message) from e
        except json.JSONDecodeError as e:
            error_message = f"Couldn't load json from file '{self._json_file_path}': {e.msg}"
            logger.critical("Raising InvalidDataFile(%s).", error_message)
            raise InvalidDataFile(error_message, e, self._json_file_path) from e
        # Load the 'contacts' object:
        self.__from_dict__(contacts_dict)
        logger.info("Contacts successfully loaded.")

    ######################
    # Sync with signal:
    ######################
    def __sync__(self) -> list[SignalContact]:
        """
        Sync contacts with signal.
        :return: list[SignalContact]: The new contacts found.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__sync__.__name__)
        logger.info("Sync contacts started.")
        # Create list contacts command object, and json command string:
        list_contacts_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listContacts",
            "params": {
                "account": self._account_id
            }
        }
        json_command_str = json.dumps(list_contacts_command_obj) + '\n'
        # Communicate with signal-cli:
        __socket_send__(self._sync_socket, json_command_str)  # Raises CommunicationError
        response_str = __socket_receive_blocking__(self._sync_socket)  # Raises CommunicationError
        response_obj = __parse_signal_response__(response_str)
        __check_response_for_error__(response_obj)  # Raises Signal Error on all signal errors.

        # Load contacts:
        new_contacts: list[SignalContact] = []
        total_count: int = 0
        new_count: int = 0
        for raw_contact in response_obj['result']:
            # Create new contact:
            new_contact = SignalContact(command_socket=self._command_socket,
                                        sync_socket=self._sync_socket,
                                        config_path=self._config_path,
                                        account_id=self._account_id,
                                        account_path=self._account_path,
                                        raw_contact=raw_contact)
            # Increment total count:
            total_count += 1
            # Check for existing contact:
            contact_found = False
            for contact in self._contacts:
                if new_contact == contact:
                    contact.__update__(new_contact)
                    contact_found = True
            # If contact not found add the new contact.
            if not contact_found:
                new_count += 1
                self._contacts.append(new_contact)
                new_contacts.append(new_contact)
        logger.info("%i contact synced %i new contacts found.", total_count, new_count)
        return new_contacts

    ##################################
    # Helpers:
    ##################################
    def __parse_sync_message__(self, sync_message) -> None:  # sync_message type = SignalSyncMessage
        """
        Parse a sync message.
        :param sync_message: SignalSyncMessage: The sync message object to check.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_sync_message__.__name__)
        if sync_message.sync_type == SyncTypes.BLOCKS:
            for contact_id in sync_message.blocked_contacts:
                _, contact = self.__get_or_add__(contact_id=contact_id)
                contact.is_blocked = True
            self.__save__()
        elif sync_message.sync_type == SyncTypes.CONTACTS:
            # new_contacts = self.__sync__()
            self.__sync__()
            self.__save__()
        else:
            error_message: str = ("SignalContacts can only parse messages of types:"
                                  "SyncTypes.BLOCKS or SyncTypes.CONTACTS.")
            logger.critical("Raising TypeError(%s).", error_message)
            raise TypeError(error_message)

    def __get_or_add__(self,
                       name: str = UNKNOWN_CONTACT_NAME,
                       number: Optional[str] = None,
                       uuid: Optional[str] = None,
                       contact_id: Optional[str] = None
                       ) -> tuple[bool, SignalContact]:
        """
        Get or add a contact.
        :param name: str: The name of the contact, defaults to UNKNOWN_CONTACT_NAME
        :param number: Optional[str]: The known phone number of the contact.
        :param uuid: Optional[str]: The known uuid of the contact.
        :param contact_id: Optional[str] The contact ID, either uuid or number formats.
        :return: tuple[bool, SignalContact]: The first element, the boolean, is if the contact
            was added to signal or not. The second element is the SignalContact object for the
            given info.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__get_or_add__.__name__)

        # Parameter checks:
        if number is None and uuid is None and contact_id is None:
            error_message: str = "Either number, uuid, or contact_id must be defined."
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        if contact_id is not None and (number is not None or uuid is not None):
            error_message: str = "Cannot define contact_id and uuid / number at the same time."
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        # Type checks:
        if not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "str", name)
        if number is not None and not isinstance(number, str):
            logger.critical("Raising TypeError:")
            __type_error__("number", "Optional[str]", number)
        if uuid is not None and not isinstance(uuid, str):
            logger.critical("Raising TypeError:")
            __type_error__("uuid", 'Optional[str]', uuid)
        if contact_id is not None and not isinstance(contact_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("contact_id", "Optional[str]", contact_id)

        # Value checks:
        if number is not None:
            number_match: Match = PHONE_NUMBER_REGEX.match(number)
            if number_match is None:
                error_message: str = f"'number' must be in format: '{NUMBER_FORMAT_STR}'"
                logger.critical("Raising ValueError(%s).", error_message)
                raise ValueError(error_message)
        if uuid is not None:
            uuid_match: Match = UUID_REGEX.match(uuid)
            if uuid_match is None:
                error_message: str = f"'uuid' must be in format: '{UUID_FORMAT_STR}'"
                logger.critical("Raising ValueError(%s).", error_message)
                raise ValueError(error_message)

        # Check the contact_id values, and set number / uuid accordingly:
        if contact_id is not None:
            number_match = PHONE_NUMBER_REGEX.match(contact_id)
            uuid_match = UUID_REGEX.match(contact_id)
            if number_match is not None:
                number = contact_id
            elif uuid_match is not None:
                uuid = contact_id
            else:
                error_message = (f"contact_id must be in format '{NUMBER_FORMAT_STR}' "
                                 f"or '{UUID_FORMAT_STR}'")
                logger.critical("Raising ValueError(%s).", error_message)
                raise ValueError(error_message)

        # Search for contact:
        found_contact: Optional[SignalContact] = None
        for contact in self._contacts:
            # Check for contact:
            if number is not None and contact.number == number:
                found_contact = contact
                break
            if uuid is not None and contact.uuid == uuid:
                found_contact = contact
                break
            if number is not None and uuid is not None and (contact.number == number or
                                                              contact.uuid == uuid):
                found_contact = contact
                break

        # If contact found:
        if found_contact is not None:
            logger.debug("Contact found.")
            # Merge contact if more info found:
            should_save: bool = False
            if found_contact.number is None and number is not None:
                found_contact.number = number
                should_save = True
            if found_contact.uuid is None and uuid is not None:
                found_contact.uuid = uuid
                should_save = True
            if found_contact.name is None or found_contact.name == UNKNOWN_CONTACT_NAME:
                if name is not None and name != UNKNOWN_CONTACT_NAME:
                    found_contact.name = name
                    should_save = True
            if should_save:
                logger.debug("contact data updated, saving.")
                self.__save__()
            return False, found_contact
        # Add contact:
        logger.debug("Adding contact.")
        # Set contact_id:
        if number is not None:
            contact_id = number
        else:
            contact_id = uuid
        # try to add to signal and return:
        added, contact, _ = self.add(name, contact_id)
        # Save the new contact:
        self.__save__()
        return added, contact

    ##################################
    # Getters:
    ##################################
    def get_by_number(self, number: str) -> Optional[SignalContact]:
        """
        Get a contact given a number.
        :param number: str: The phone number of the contact.
        :return: Optional[SignalContact]: Returns the contact, or None if not found.
        :raises: TypeError: If phone number is not a string.
        :raises: ValueError: If phone number is not in proper format.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_number.__name__)
        # Type check parameters:
        if not isinstance(number, str):
            logger.critical("Raising TypeError:")
            __type_error__("number", "str", number)
        # Value check number:
        number_match = PHONE_NUMBER_REGEX.match(number)
        if number_match is None:
            error_message = f"number must be in format '{NUMBER_FORMAT_STR}'"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        # Search for contact:
        for contact in self._contacts:
            if contact.number == number:
                return contact
        return None

    def get_by_uuid(self, uuid: str) -> Optional[SignalContact]:
        """
        Get a contact given a UUID.
        :param uuid: str: The uuid of the contact.
        :return Optional[SignalContact]: Return the contact, or None if not found.
        :raises: TypeError: If uuid is not a string.
        :raises: ValueError: If uuid is not in proper format.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_uuid.__name__)
        # Type check arguments:
        if not isinstance(uuid, str):
            logger.critical("Raising TypeError:")
            __type_error__("uuid", "str", uuid)
        uuid_match = UUID_REGEX.match(uuid)
        # Value check uuid:
        if uuid_match is None:
            error_message = f"uuid must be in format: '{UUID_FORMAT_STR}'"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        # Search for contact:
        for contact in self._contacts:
            if contact.uuid == uuid:
                return contact
        return None

    def get_by_id(self, contact_id: str) -> Optional[SignalContact]:
        """
        Get a contact given either a phone number or an uuid.
        :param contact_id: str: The id of the contact, either a phone number or an uuid.
        :return Optional[SignalContact]: Return the contact, or None if not found.
        :raises: TypeError: If the contact_id is not a string.
        :raises: ValueError: If contact_id not in phone number or uuid formats.
        """
        # setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_id.__name__)
        # Argument check:
        if not isinstance(contact_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("contact_id", "str", contact_id)
        # Match contact Values:
        number_match: Match = PHONE_NUMBER_REGEX.match(contact_id)
        uuid_match: Match = UUID_REGEX.match(contact_id)
        if number_match is not None:
            return self.get_by_number(contact_id)
        if uuid_match is not None:
            return self.get_by_uuid(contact_id)

        # Value error:
        error_message: str = (f"'contact_id' must be in format '{NUMBER_FORMAT_STR}' "
                             f"or '{UUID_FORMAT_STR}'")
        logger.critical("Raising ValueError(%s).", error_message)
        raise ValueError(error_message)

    def get_self(self) -> Optional[SignalContact]:
        """
        Return the contact for the current account.
        :return SignalContact: The 'self' contact, or None if not found.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_self.__name__)
        for contact in self._contacts:
            if contact.is_self:
                return contact
        logger.warning("'Self-Contact' not found ????'")
        return None

    def get_by_name(self, name: str) -> Optional[SignalContact]:
        """
        Get a contact given a name.
        :param name: str: The name to search for.
        :returns: Optional[SignalContact]: The contact, or None if not found.
        :raises: TypeError: If name is not a string.
        :raises: ValueError: If name is an empty string.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_name.__name__)
        # Type Check:
        if not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "str", name)
        # Value Check:
        if name == '':
            error_message = 'name cannot be an empty string.'
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        # Search for contact:
        for contact in self._contacts:
            if contact.name == name:
                return contact
        return None

    #########################
    # Methods:
    #########################
    def add(self,
            name: str,
            contact_id: str,
            expiration: Optional[int] = None
            ) -> tuple[bool, SignalContact, Optional[str]]:
        """
        Add a contact.
        :param name: str: The name to assign to the contact.
        :param contact_id: str: The id of the contact, either a phone number or an uuid.
        :param expiration: Optional[int]: The message expiration time in seconds.
        :returns: tuple(bool, SignalContact, Optional[str]): The first element, the bool indicates
            if the contact was successfully added to signal. The second element is the new
            SignalContact object, or existing SignalContact object if the contact already exists.
            The third element, the Optional string, will be None if the first element is True,
            otherwise it will be a reason the contact wasn't added to signal.
        :raises: TypeError: If a parameter is of an invalid type.
        :raises: ValueError: If the contact id not in phone number or uuid formats.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.add.__name__)

        # Type checks:
        if not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "str", name)
        elif not isinstance(contact_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("contact_id", "str", contact_id)
        elif expiration is not None and not isinstance(expiration, int):
            logger.critical("Raising TypeError:")
            __type_error__("expiration", "Optional[int]", expiration)

        # Value Checks:
        phone_number_match = PHONE_NUMBER_REGEX.match(contact_id)
        uuid_match = UUID_REGEX.match(contact_id)
        if phone_number_match is None and uuid_match is None:
            error_message = (f"'contact_id' must be in format '{NUMBER_FORMAT_STR}' "
                             f"or '{UUID_FORMAT_STR}'.")
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Check if contact already exists:
        old_contact = self.get_by_id(contact_id)
        if old_contact is not None:
            return False, old_contact, "contact exists"

        # Create add contact command object and json command string:
        add_contact_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "updateContact",
            "params": {
                "account": self._account_id,
                "name": name,
                "recipient": contact_id
            }
        }
        if expiration is not None:
            add_contact_command_obj['params']['expiration'] = expiration
        json_command_str = json.dumps(add_contact_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        error_occurred, error_code, error_message = __check_response_for_error__(response_obj,
                                                                                 [-1, ])

        # Parse Error:
        exit_message: Optional[str] = None
        if error_occurred:
            logger.debug("Non-fatal error occurred: Code: %i, Message: %s", error_code,
                         error_message)
            if error_code == -1:  # TODO: Check error. Might be linked account error.
                exit_message = error_message

        # Create a new contact object:
        new_contact: SignalContact
        if phone_number_match is not None:  # Reuse phone number match from value check.
            new_contact = SignalContact(command_socket=self._command_socket,
                                        sync_socket=self._sync_socket,
                                        config_path=self._config_path,
                                        account_id=self._account_id,
                                        account_path=self._account_path,
                                        name=name,
                                        number=contact_id )
        else:
            new_contact = SignalContact(command_socket=self._sync_socket,
                                        sync_socket=self._sync_socket,
                                        config_path=self._config_path,
                                        account_id=self._account_id,
                                        account_path=self._account_path,
                                        name=name,
                                        uuid=contact_id )

        # Store the contact:
        self._contacts.append(new_contact)
        self.__save__()

        # Return appropriately:
        if exit_message is not None:
            return False, new_contact, exit_message
        return True, new_contact, None

    def get_blocked(self, include_self: bool = True) -> list[SignalContact]:
        """
        Get a list of blocked contacts.
        :param include_self: bool: Should we include the self-contact?
        :return: list[SignalContact]: The blocked contacts, or an empty list if none found.
        """
        contact_list: list[SignalContact] = [contact for contact in self._contacts
                                             if contact.is_blocked is True]
        if include_self:
            return contact_list
        try:
            contact_list.remove(self.get_self())
        except ValueError:
            pass
        return contact_list

    def get_unblocked(self, include_self: bool = True) -> list[SignalContact]:
        """
        Get a list of unblocked contacts.
        :param include_self: bool: Should we include the self-contact?
        :return: list[SignalContact]: The unblocked contacts, or an empty list if none found.
        """
        contact_list: list[SignalContact] = [contact for contact in self._contacts
                                             if contact.is_blocked is False]
        if include_self:
            return contact_list
        contact_list.remove(self.get_self())
        return contact_list
