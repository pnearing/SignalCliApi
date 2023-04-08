#!/usr/bin/env python3
"""Signal Mention"""
from typing import TypeVar, Optional, Any
from .signalContacts import Contacts
from .signalContact import Contact
from .signalCommon import __type_error__
DEBUG: bool = False
Self = TypeVar("Self", bound="Mention")


class Mention(object):
    """Object for a mention."""
    def __init__(self,
                 contacts: Contacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_mention: Optional[dict[str, Any]] = None,
                 contact: Optional[Contact] = None,
                 start: Optional[int] = None,
                 length: Optional[int] = None,
                 ) -> None:
        # Argument checks:
        if not isinstance(contacts, Contacts):
            __type_error__("contacts", "Contacts", contacts)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if raw_mention is not None and not isinstance(raw_mention, dict):
            __type_error__("raw_mention", "Optional[dict]", raw_mention)
        if contact is not None and not isinstance(contact, Contact):
            __type_error__("contact", "Optional[Contact]", contact)
        if start is not None and not isinstance(start, int):
            __type_error__("start", "Optional[int]", start)
        if length is not None and not isinstance(length, int):
            __type_error__("length", "Optional[int]", length)
        # Set internal properties:
        self._contacts: Contacts = contacts
        # Set external properties:
        self.contact: Contact = contact
        self.start: int = start
        self.length: int = length
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw Mention:
        elif raw_mention is not None:
            self.__from_raw_mention__(raw_mention)
        return

    ########################
    # Init:
    ########################
    def __from_raw_mention__(self, raw_mention: dict) -> None:
        print(raw_mention)
        added, self.contact = self._contacts.__get_or_add__(
            name=raw_mention['name'],
            number=raw_mention['number'],
            uuid=raw_mention['uuid']
        )

        self.start = raw_mention['start']
        self.length = raw_mention['length']
        return

    ######################
    # Overrides:
    ######################
    def __str__(self) -> str:
        return "%i:%i:%s" % (self.start, self.length, self.contact.get_id())

    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Mention):
            if self.start != __o.start:
                return False
            elif self.length != __o.length:
                return False
            elif self.contact != __o.contact:
                return False
            else:
                return True
        return False

    ######################
    # To / From Dict:
    ######################
    def __to_dict__(self) -> dict[str, object]:
        mention_dict = {
            "contactId": self.contact.get_id(),
            "start": self.start,
            "length": self.length,
        }
        return mention_dict

    def __from_dict__(self, from_dict: dict) -> None:
        added, self.contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=from_dict['contactId'])
        self.start = from_dict['start']
        self.length = from_dict['length']
        return
