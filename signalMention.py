#!/usr/bin/env python3

from typing import TypeVar, Optional, Any
from .signalContacts import Contacts
from .signalContact import Contact

Self = TypeVar("Self", bound="Mention")


class Mention(object):
    def __init__(self,
                 contacts: Contacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_mention: Optional[dict[str, Any]] = None,
                 contact: Optional[Contact] = None,
                 start: Optional[int] = None,
                 length: Optional[int] = None,
                 ) -> None:
        # TODO: Argument checks:
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
            "contact_id": self.contact.get_id(),
            "start": self.start,
            "length": self.length,
        }
        return mention_dict

    def __from_dict__(self, from_dict: dict) -> None:
        added, self.contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=from_dict['contact_id'])
        self.start = from_dict['start']
        self.length = from_dict['length']
        return
