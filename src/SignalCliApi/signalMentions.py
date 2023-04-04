#!/usr/bin/env python3
from typing import Optional, Iterable, Iterator
import re

from .signalCommon import __type_error__, phone_number_regex, uuid_regex
from .signalContact import Contact
from .signalContacts import Contacts
from .signalMention import Mention
DEBUG: bool = False


class Mentions(object):
    """Object to store the mentions in the message."""

    def __init__(self,
                 contacts: Contacts,
                 from_dict: Optional[dict[str, object]] = None,
                 raw_mentions: Optional[list[dict[str, object]]] = None,
                 mentions: Optional[Iterable[Mention]] = None,
                 ) -> None:
        # Argument check contacts:
        if not isinstance(contacts, Contacts):
            __type_error__("contacts", "Contacts", contacts)
        # Argument check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        # Argument check raw_mentions:
        if raw_mentions is not None:
            if not isinstance(raw_mentions, list):
                __type_error__("raw_mentions", "Optional[list[dict[str, object]]]", raw_mentions)
            for i, raw_mention in enumerate(raw_mentions):
                if not isinstance(raw_mention, dict):
                    __type_error__("raw_mention[%i]" % i, "dict", raw_mention)
        # Argument Check mentions:
        mentions_list: list[Mention] = []
        if mentions is not None:
            if not isinstance(mentions, Iterable):
                __type_error__("mentions", "Optional[Iterable[Mention]]", mentions)
            for i, mention in enumerate(mentions):
                if not isinstance(mention, Mention):
                    __type_error__("mentions[%i]" % i, "Mention", mention)
                mentions_list.append(mention)
            if len(mentions_list) == 0:
                raise ValueError("mentions cannot be empty")
        # Set internal vars:
        self._contacts: Contacts = contacts
        self._mentions: list[Mention] = mentions_list
        # Parse from Dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw Mentions:
        elif raw_mentions is not None:
            self.__from_raw_mentions__(raw_mentions)
        return

    ##############################
    # Init:
    ##############################
    def __from_raw_mentions__(self, rawMentions: list[dict]) -> None:
        self._mentions = []
        for raw_mention in rawMentions:
            mention = Mention(contacts=self._contacts, raw_mention=raw_mention)
            self._mentions.append(mention)
        return

    #######################################
    # Overrides:
    #######################################
    def __iter__(self) -> Iterator[Mention]:
        return iter(self._mentions)

    def __len__(self) -> int:
        return len(self._mentions)

    def __getitem__(self, index: int | Contact) -> Mention:
        if isinstance(index, int):
            return self._mentions[index]
        elif isinstance(index, Contact):
            for mention in self._mentions:
                if mention.contact == index:
                    return mention
            raise IndexError("Mention with contact_id: %s not found." % index.get_id())
        else:
            __type_error__("index", "int | Contact", index)

    #######################################
    # To / From Dict:
    #######################################
    def __to_dict__(self) -> dict[str, object]:
        mentions_dict = {
            "mentions": [],
        }
        for mention in self._mentions:
            mentions_dict['mentions'].append(mention.__to_dict__())
        return mentions_dict

    def __from_dict__(self, fromDict: dict[str, object]) -> None:
        self._mentions = []
        for mention_dict in fromDict['mentions']:
            self._mentions.append(Mention(contacts=self._contacts, from_dict=mention_dict))
        return

    #########################################
    # Helpers:
    #########################################
    def __parse_mentions__(self, body: str) -> str:
        if not isinstance(body, str):
            __type_error__("body", "str", body)
        for mention in self._mentions:
            body_start = body[:mention.start]
            body_end = body[mention.start + mention.length:]
            body = body_start + mention.contact.get_display_name() + body_end
        return body

    #######################################
    # Getters:
    #######################################
    def get_by_contact(self, contact: Contact) -> list[Mention]:
        """
        Get a list of mentions given a contact.
        :param contact: Contact: The contact to find.
        :returns: list: A list of mentions, if none found an empty list is returned.
        :raises: TypeError if contact is not a Contact.
        """
        if not isinstance(contact, Contact):
            __type_error__("contact", "Contact", contact)
        return [mention for mention in self._mentions if mention.contact == contact]

    def get_by_start_pos(self, start: int) -> Optional[Mention]:
        """
        Get a mention given a start position.
        :param start: int, The start position.
        :returns: Optional[Mention]: The mention, or None if not found.
        :raises: TypeError: If start is not an int.
        """
        if not isinstance(start, int):
            __type_error__("start", "int", start)
        for mention in self._mentions:
            if mention.start == start:
                return mention
        return None

    def get_by_length(self, length: int) -> list[Mention]:
        """
        Get a list of mentions that are of a certain length.
        :param length: int: The length to search for.
        :returns: List of mentions, an empty list if not found.
        :raises: TypeError if length is not an int.
        :raises: ValueError if length is < 1.
        """
        if not isinstance(length, int):
            __type_error__("length", "int", length)
        elif length < 1:
            error_message = "Length must be greater than zero."
            raise ValueError(error_message)
        return [mention for mention in self._mentions if mention.length == length]

    #######################################
    # Tests:
    #######################################
    def contact_mentioned(self, contact: Contact) -> bool:
        """
        Return True if a contact is mentioned.
        :param contact: Contact: The contact to search for.
        :returns: bool: True if contact is mentioned.
        :raises: TypeError if contact is not a Contact object.
        """
        if not isinstance(contact, Contact):
            __type_error__("contact", "Contact", contact)
        mentions = [mention for mention in self._mentions if mention.contact == contact]
        if len(mentions) > 0:
            return True
        return False

    #######################################
    # Methods:
    #######################################
    def append(self, mention: Mention) -> None:
        """
        Append a mention to the mention list.
        :param mention: Mention: The mention to append.
        :returns: None
        :raises: TypeError if mention is not a Mention object.
        :raises: RuntimeError is mention already in the mention list.
        """
        if not isinstance(mention, Mention):
            __type_error__("mention", "Mention", mention)
        if mention in self._mentions:
            error_message = "mention already exists."
            raise RuntimeError(error_message)
        self._mentions.append(mention)
        return

    def create(self, contact: Contact, start: int, length: int) -> Mention:
        """
        Create and append a mention to the list.
        :param contact: Contact: The contact to mention.
        :param start: int: The start position of the mention.
        :param length: int: The length of the mention.
        :returns: Mention: The mention created.
        :raises: TypeError If contact is not a Contact object, start is not an int, or length is not an int.
        """
        mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
        self.append(mention)
        return mention

    def create_from_body(self, body: str) -> list[Mention]:
        """
        Create a mention from the body of the message. Searches for the '@' sign followed by either the phone number,
            the uuid of the contact, or the contact name surrounded in either single or double quotes.
        :param body: str: The body to create the mentions from.
        :returns: list[Mention]: A list of the mentions in the body, an empty list if none found.
        :raises: TypeError: If body is not a string.
        """
        if not isinstance(body, str):
            __type_error__("body", "str", body)
        regex = re.compile(
            r'(@<(\+\d+|[0-9a-fA-F]{8}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{12}|[\"\'].+[\"\']))')
        match_list = regex.findall(body)
        last_find = 0
        return_value = []
        for match, contact_id in match_list:
            # Figure out what matched:
            match_type: Optional[str] = None
            phone_number_match = phone_number_regex.match(contact_id)
            uuid_match = uuid_regex.match(contact_id)
            if phone_number_match is not None:
                match_type = "phoneNumber"
            elif uuid_match is not None:
                match_type = "UUID"
            elif contact_id.find('@"') > -1:
                match_type = "nameDouble"
            elif contact_id.find("@'") > -1:
                match_type = "nameSingle"
            else:
                pass  # Shouldn't get here.
            # Act based on what matched:
            if match_type == "phoneNumber":
                for contact in self._contacts:
                    if contact.number == contact_id:
                        start = body.find(match, last_find)
                        length = len(match)
                        last_find = start
                        mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
                        self._mentions.append(mention)
                        return_value.append(mention)
            elif match_type == "UUID":
                for contact in self._contacts:
                    if contact.uuid == contact_id:
                        start = body.find(match, last_find)
                        length = len(match)
                        last_find = start
                        mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
                        self._mentions.append(mention)
                        return_value.append(mention)
            elif match_type == 'nameDouble' or match_type == 'nameSingle':
                contact_name: str
                name_start_pos: int
                name_end_pos: int
                if match_type == 'nameDouble':
                    name_start_pos = body.find('"', last_find)
                    last_find = name_start_pos
                    name_end_pos = body.find('"', last_find)
                else:
                    name_start_pos = body.find("'", last_find)
                    last_find = name_start_pos
                    name_end_pos = body.find("'", last_find)
                start = body.find(match, last_find)
                length = len(match)
                contact_name = body[name_start_pos+1:name_end_pos-1]
                contact = self._contacts.get_by_name(contact_name)
                if contact is not None:
                    mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
                    self._mentions.append(mention)
                    return_value.append(mention)
        return return_value
