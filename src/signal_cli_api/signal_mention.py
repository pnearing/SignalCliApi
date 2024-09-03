#!/usr/bin/env python3
"""
File: signal_mention.py
Class to store and handle a mention.
"""
# pylint: disable=R0913
import logging
from typing import TypeVar, Optional, Any
from .signal_contacts import SignalContacts
from .signal_contact import SignalContact
from .signal_common import __type_error__

Self = TypeVar("Self", bound="SignalMention")


class SignalMention:
    """
    Object for a mention.
    """

    def __init__(self,
                 contacts: SignalContacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_mention: Optional[dict[str, Any]] = None,
                 contact: Optional[SignalContact] = None,
                 start: Optional[int] = None,
                 length: Optional[int] = None,
                 ) -> None:
        """
        Initialize a new mention.
        :param contacts: SignalContacts, The accounts contacts object.
        :param from_dict: Optional[dict[str, Any]]: Load from a dict provided by __to_dict__()
        :param raw_mention: Optional[dict[str, Any]]: Load from a dict provided by signal.
        :param contact: Optional[SignalContact]: The contact this mention refers to.
        :param start: Optional[int]: Where in the body the mention starts.
        :param length: Optional[int]: How long the mention is.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "SignalContacts", contacts)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if raw_mention is not None and not isinstance(raw_mention, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_mention", "Optional[dict]", raw_mention)
        if contact is not None and not isinstance(contact, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("contact", "Optional[SignalContact]", contact)
        if start is not None and not isinstance(start, int):
            logger.critical("Raising TypeError:")
            __type_error__("start", "Optional[int]", start)
        if length is not None and not isinstance(length, int):
            logger.critical("Raising TypeError:")
            __type_error__("length", "Optional[int]", length)

        # Set internal properties:
        self._contacts: SignalContacts = contacts
        """This accounts SignalContact object."""

        # Set external properties:
        self.contact: SignalContact = contact
        """The contact this mention refers to."""
        self.start: int = start
        """The start position in the body where this mention starts."""
        self.length: int = length
        """The length of the mention."""

        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw Mention:
        elif raw_mention is not None:
            self.__from_raw_mention__(raw_mention)

    ########################
    # Init:
    ########################
    def __from_raw_mention__(self, raw_mention: dict[str, Any]) -> None:
        """
        Load properties from raw mention provided by signal.
        :param raw_mention: dict[str, Any]: The dict to load from.
        :return: None
        """
        _, self.contact = self._contacts.__get_or_add__(name=raw_mention['name'],
                                                        number=raw_mention['number'],
                                                        uuid=raw_mention['uuid'])
        self._contacts.__save__()
        self.start = raw_mention['start']
        self.length = raw_mention['length']

    ######################
    # Overrides:
    ######################
    def __str__(self) -> str:
        """
        String representation of the mention.
        :return:
        """
        return f"{self.start}:{self.length}:{self.contact.get_id()}"

    def __eq__(self, other: Self) -> bool:
        """
        Calculate equality.
        :param other: SignalMention: The mention to compare with.
        :return: bool
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__eq__.__name__)
        if isinstance(other, SignalMention):
            if self.start != other.start:
                return False
            if self.length != other.length:
                return False
            if self.contact != other.contact:
                return False
            return True
        return False

    ######################
    # To / From Dict:
    ######################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a jSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        mention_dict = {
            "contactId": self.contact.get_id(),
            "start": self.start,
            "length": self.length,
        }
        return mention_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        _, self.contact = self._contacts.__get_or_add__(contact_id=from_dict['contactId'])
        self._contacts.__save__()
        self.start = from_dict['start']
        self.length = from_dict['length']
