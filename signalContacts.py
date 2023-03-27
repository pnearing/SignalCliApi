#!/usr/bin/env python3

from typing import Optional, Iterator
import sys
import os
import json
import socket

from .signalCommon import __type_error__, __socket_receive__, __socket_send__, phone_number_regex, uuid_regex, \
    NUMBER_FORMAT_STR, UUID_FORMAT_STR
from .signalContact import Contact

# from signalSyncMessage import SyncMessage

DEBUG: bool = False


class Contacts(object):
    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 account_path: str,
                 do_load: bool = False,
                 do_sync: bool = False,
                 ) -> None:
        # TODO: Argument checks:
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._config_path: str = config_path
        self._account_id: str = account_id
        self._account_path: str = account_path
        self._contacts: list[Contact] = []
        # Load from file:
        if do_load:
            try:
                self.__load__()
            except RuntimeError:
                if DEBUG:
                    errorMessage = "Creating empty contacts.json file for account: %s" % self._account_id
                    print(errorMessage, file=sys.stderr)
                self.__save__()
        # Sync with signal:
        if do_sync:
            self.__sync__()
            self.__save__()
        # Search for self contact, and create if not found:
        self_contact = self.get_by_number(self._account_id)
        if self_contact is None:
            self.add("Note-To-Self", self._account_id)
            self.__save__()
        else:
            self_contact.set_name("Note-To-Self")
            self.__save__()
        return

    ##########################
    # Overrides:
    ##########################
    def __iter__(self) -> Iterator[Contact]:
        return iter(self._contacts)

    def __len__(self) -> int:
        return len(self._contacts)

    def __getitem__(self, index: int | str) -> Contact:
        if isinstance(index, int):
            return self._contacts[index]
        elif isinstance(index, str):
            number_match = phone_number_regex.match(index)
            uuid_match = uuid_regex.match(index)
            if number_match is not None:
                for contact in self._contacts:
                    if contact.number == index:
                        return contact
            elif uuid_match is not None:
                for contact in self._contacts:
                    if contact.uuid == index:
                        return contact
            else:
                error_message = "index must be of format '%s' or '%s'" % (NUMBER_FORMAT_STR, UUID_FORMAT_STR)
                raise ValueError(error_message)
            error_message = "index not found: %s" % index
            raise IndexError(error_message)
        else:
            __type_error__(index, "int | str", index)

    ##########################
    # To / From Dict:
    ##########################
    def __to_dict__(self) -> dict:
        contacts_dict = {
            "contacts": [],
        }
        for contact in self._contacts:
            contacts_dict['contacts'].append(contact.__to_dict__())
        return contacts_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self._contacts = []
        for contact_dict in from_dict['contacts']:
            contact = Contact(sync_socket=self._sync_socket, config_path=self._config_path, account_id=self._account_id,
                              account_path=self._account_path, from_dict=contact_dict)
            self._contacts.append(contact)
        return

    ##############################
    # Load / Save:
    ##############################
    def __save__(self) -> None:
        # Create the contacts object, and json string:
        contacts_obj = self.__to_dict__()
        contacts_json = json.dumps(contacts_obj, indent=4)
        # Build the file Path:
        file_name = "contacts-" + self._account_id + '.json'
        file_path = os.path.join(self._account_path, file_name)
        # Try to open the file:
        try:
            file_handle = open(file_path, 'w')
        except Exception as e:
            error_message = "FATAL: Couldn't open contacts file '%s' for writing: %s" % (file_path, str(e.args))
            raise RuntimeError(error_message)
        # Write the json to the file and close it.
        file_handle.write(contacts_json)
        file_handle.close()
        return

    def __load__(self) -> None:
        # Build the file Path:
        file_name = 'contacts-' + self._account_id + '.json'
        file_path = os.path.join(self._account_path, file_name)
        # Try and open the file for reading:
        try:
            file_handle = open(file_path, 'r')
        except Exception as e:
            error_message = "FATAL: Couldn't open '%s' for reading: %s" % (file_path, str(e.args))
            raise RuntimeError(error_message)
        # Try and load the json from the file:
        try:
            contacts_dict: dict = json.loads(file_handle.read())
        except json.JSONDecodeError as e:
            error_message = "FATAL: Couldn't load json from file '%s': %s" % (file_path, e.msg)
            raise RuntimeError(error_message)
        # Load the contacts object:
        self.__from_dict__(contacts_dict)
        return

    ######################
    # Sync with signal:
    ######################
    def __sync__(self) -> list[Contact]:
        # Create list contacts command object, and json command string:
        list_contacts_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "listContacts",
            "params": {
                "account": self._account_id
            }
        }
        json_command_str = json.dumps(list_contacts_command_obj) + '\n'
        # Communicate with signal-cli:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                errorMessage = "ERROR: Signal reported error during contacts sync, code: %i, message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message'])
                print(errorMessage, file=sys.stderr)
                return
        # Load contacts:
        new_contacts = []
        for raw_contact in response_obj['result']:
            # Create new contact:
            new_contact = Contact(sync_socket=self._sync_socket, config_path=self._config_path,
                                  account_id=self._account_id,
                                  account_path=self._account_path, raw_contact=raw_contact)
            # Check for existing contact:
            contact_found = False
            for contact in self._contacts:
                if contact.get_id() == new_contact.get_id():
                    contact.__merge__(new_contact)
                    contact_found = True
            # If contact not found add the new contact.
            if not contact_found:
                self._contacts.append(new_contact)
                new_contacts.append(new_contact)
        return new_contacts

    ##################################
    # Helpers:
    ##################################
    def __parse_sync_message__(self, sync_message) -> None:  # sync_message type = SyncMessage
        if sync_message.sync_type == 5:  # SyncMessage.TYPE_BLOCKED_SYNC
            for contact_id in sync_message.blocked_contacts:
                added, contact = self.__get_or_add__("<UNKNOWN-CONTACT>", contact_id)
                contact.is_blocked = True
            self.__save__()
        else:
            error_message = "Contacts can only parse messages of type: SyncMessage.TYPE_BLOCKED_SYNC."
            raise TypeError(error_message)
        return

    def __get_or_add__(self,
                       name: str,
                       number: Optional[str] = None,
                       uuid: Optional[str] = None,
                       contact_id: Optional[str] = None
                       ) -> tuple[bool, Contact]:
        # Argument check
        if number is None and uuid is None and contact_id is None:
            RuntimeError("Either number or uuid, or contact_id must be defined.")
        # Check contact_id type:
        if contact_id is not None:
            numberMatch = phone_number_regex.match(contact_id)
            uuidMatch = uuid_regex.match(contact_id)
            if numberMatch is None and uuidMatch is None:
                errorMessage = "contact_id must be in format '%s' or '%s'" % (NUMBER_FORMAT_STR, UUID_FORMAT_STR)
                raise ValueError(errorMessage)
            elif numberMatch is not None:
                number = contact_id
                uuid = None
            elif uuidMatch is not None:
                number = None
                uuid = contact_id
        # Search for contact:
        contact = None
        for contact in self._contacts:
            if contact.number == number or contact.uuid == uuid:
                contact = contact
                # Merge contact if more info found:
                if contact.number is None and number is not None:
                    contact.number = number
                    self.__save__()
                if contact.uuid is None and uuid is not None:
                    contact.uuid = uuid
                    self.__save__()
        # If contact found:
        if contact is not None:
            return False, contact
        # Set contact_id:
        if number is not None:
            contact_id = number
        else:
            contact_id = uuid
        # add to signal:
        (addedToSignal, contact) = self.add(name, contact_id)
        return True, contact

    ##################################
    # Getters:
    ##################################
    def get_by_number(self, number: str) -> Optional[Contact]:
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message = "number must be in format '+nnnnnnnn...'"
            raise ValueError(error_message)
        for contact in self._contacts:
            if contact.number == number:
                return contact
        return None

    def get_by_uuid(self, uuid: str) -> Optional[Contact]:
        uuid_match = uuid_regex.match(uuid)
        if uuid_match is None:
            errorMessage = "uuid must be in format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'"
            raise ValueError(errorMessage)
        for contact in self._contacts:
            if contact.uuid == uuid:
                return contact
        return None

    def get_by_id(self, contact_id: str) -> Optional[Contact]:
        number_match = phone_number_regex.match(contact_id)
        uuidMatch = uuid_regex.match(contact_id)
        if number_match is not None:
            return self.get_by_number(contact_id)
        elif uuidMatch is not None:
            return self.get_by_uuid(contact_id)
        else:
            errorMessage = "contact_id must be in format '+nnnnnnnnn...' or 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'"
            raise ValueError(errorMessage)

    def get_self(self) -> Contact:
        for contact in self._contacts:
            if contact.is_self:
                return contact
        raise RuntimeError("FATAL: Couldn't find self contact, should never get here.")

    #########################
    # Methods:
    #########################
    def add(self, name: str, contact_id: str, expiration: Optional[int] = None) -> tuple[bool, Contact]:
        # TODO: Argument checks:
        old_contact = self.get_by_id(contact_id)
        if old_contact is not None:
            return False, old_contact
        # Create add contact command object and json command string:
        add_contact_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
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
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "signal error. Code: %i, Message: %s" % (
                    response_obj['error']['code'], response_obj['error']['message'])
                print(error_message, file=sys.stderr)
            number_match = phone_number_regex.match(contact_id)
            uuid_match = uuid_regex.match(contact_id)
            if number_match is not None:
                new_contact = Contact(sync_socket=self._sync_socket, config_path=self._config_path,
                                      account_id=self._account_id,
                                      account_path=self._account_path, name=name, number=contact_id)
            elif uuid_match is not None:
                new_contact = Contact(sync_socket=self._sync_socket, config_path=self._config_path,
                                      account_id=self._account_id,
                                      account_path=self._account_path, name=name, uuid=contact_id)
            else:
                error_message = "contact_id must be in format '+nnnnnn...' or 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                raise ValueError(error_message)
            self._contacts.append(new_contact)
            return False, new_contact
        # Parse result:
        self.__sync__()
        self.__save__()
        new_contact = self.get_by_id(contact_id)
        return True, new_contact
