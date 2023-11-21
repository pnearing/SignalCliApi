#!/usr/bin/env python3
"""
File signalMentions.py
Store and handle a list of mentions.
"""
import logging
from typing import Optional, Iterable, Iterator, Any
import re

from .signalCommon import __type_error__, phone_number_regex, uuid_regex
from .signalContact import Contact
from .signalContacts import Contacts
from .signalMention import Mention


class Mentions(object):
    """
    Object to store the mentions in the message.
    """
    def __init__(self,
                 contacts: Contacts,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_mentions: Optional[list[dict[str, Any]]] = None,
                 mentions: Optional[Iterable[Mention]] = None,
                 ) -> None:
        """
        Initialize the Mentions.
        :param contacts: Contacts: This accounts contacts object.
        :param from_dict: Optional[dict[str, Any]]: Load from a dict provided by __to_dict__()
        :param raw_mentions: Optional[dict[str, Any]]: Load from a dict provided by signal.
        :param mentions: Optional[Iterable[Mention]]: Any mentions to load.
        """
        # Super:
        super().__init__()

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument check contacts:
        if not isinstance(contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "Contacts", contacts)
        # Argument check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, Any]", from_dict)
        # Argument check raw_mentions:
        if raw_mentions is not None:
            if not isinstance(raw_mentions, list):
                logger.critical("Raising TypeError:")
                __type_error__("raw_mentions", "Optional[list[dict[str, Any]]]", raw_mentions)
            for i, raw_mention in enumerate(raw_mentions):
                if not isinstance(raw_mention, dict):
                    logger.critical("Raising TypeError:")
                    __type_error__("raw_mention[%i]" % i, "dict[str, Any]", raw_mention)
        # Argument Check mentions:
        mentions_list: list[Mention] = []
        if mentions is not None:
            if not isinstance(mentions, Iterable):
                logger.critical("Raising TypeError:")
                __type_error__("mentions", "Optional[Iterable[Mention]]", mentions)
            for i, mention in enumerate(mentions):
                if not isinstance(mention, Mention):
                    logger.critical("Raising TypeError:")
                    __type_error__("mentions[%i]" % i, "Mention", mention)
                mentions_list.append(mention)
            if len(mentions_list) == 0:
                raise ValueError("mentions cannot be empty")

        # Set internal vars:
        self._contacts: Contacts = contacts
        """This accounts Contacts object."""
        self._mentions: list[Mention] = mentions_list
        """The list of mentions."""

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
    def __from_raw_mentions__(self, rawMentions: list[dict[str, Any]]) -> None:
        """
        Load from raw mentions.
        :param rawMentions: list[dict[str, Any]]: The raw mentions list provided by signal.
        :return: None
        """
        self._mentions = []
        for raw_mention in rawMentions:
            mention = Mention(contacts=self._contacts, raw_mention=raw_mention)
            self._mentions.append(mention)
        return

    #######################################
    # Overrides:
    #######################################
    def __iter__(self) -> Iterator[Mention]:
        """
        Iterate over the mentions.
        :return: Iterator[Mention]
        """
        return iter(self._mentions)

    def __len__(self) -> int:
        """
        Return the number of mentions.
        :return: int: The len of self._mentions.
        """
        return len(self._mentions)

    def __getitem__(self, index: int | Contact) -> Mention:
        """
        Index with square brackets.
        :param index: int | Contact: The index to look for.
        :return: Mention: The selected mention object.
        :raises IndexError: If index is an int, and is out of range, or if index is a Contact and not found.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__getitem__.__name__)
        if isinstance(index, int):
            return self._mentions[index]  # Raises IndexError
        elif isinstance(index, Contact):
            for mention in self._mentions:
                if mention.contact == index:
                    return mention
            error_message: str = "Mention with contact_id: %s not found." % index.get_id()
            logger.critical("Raising IndexError(%s)." % error_message)
            raise IndexError(error_message)
        else:
            logger.critical("Raising TypeError:")
            __type_error__("index", "int | Contact", index)

    #######################################
    # To / From Dict:
    #######################################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        mentions_dict: dict[str, Any] = {
            "mentions": [],
        }
        for mention in self._mentions:
            mentions_dict['mentions'].append(mention.__to_dict__())
        return mentions_dict

    def __from_dict__(self, fromDict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param fromDict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        self._mentions = []
        for mention_dict in fromDict['mentions']:
            self._mentions.append(Mention(contacts=self._contacts, from_dict=mention_dict))
        return

    #########################################
    # Helpers:
    #########################################
    def __parse_mentions__(self, body: Optional[str]) -> Optional[str]:
        """
        Insert mentions into the body of a message.
        :param body: str: The body of the message containing the mentions.
        :return: str: The body with mentions inserted.
        """
        # TODO: Look over this, it might not work as is.
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_mentions__.__name__)
        if body is not None and not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "Optional[str]", body)
        if body is not None:
            for mention in self._mentions:
                body_start = body[:mention.start]
                body_end = body[mention.start + mention.length:]
                body = body_start + '@' + mention.contact.get_display_name() + body_end
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
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_contact.__name__)
        if not isinstance(contact, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("contact", "Contact", contact)
        return [mention for mention in self._mentions if mention.contact == contact]

    def get_by_start_pos(self, start: int) -> list[Mention]:
        """
        Get a mention given a start position.
        :param start: int, The start position.
        :returns: list[Mention]: A list of mentions or an empty list if none found.
        :raises: TypeError: If start is not an int.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_start_pos.__name__)
        if not isinstance(start, int):
            logger.critical("Raising TypeError:")
            __type_error__("start", "int", start)
        return [mention for mention in self._mentions if mention.start == start]

    def get_by_length(self, length: int) -> list[Mention]:
        """
        Get a list of mentions that are of a certain length.
        :param length: int: The length to search for.
        :returns: List of mentions, an empty list if not found.
        :raises: TypeError if length is not an int.
        :raises: ValueError if length is < 1.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_length.__name__)
        if not isinstance(length, int):
            logger.critical("Raising TypeError:")
            __type_error__("length", "int", length)
        elif length < 1:
            error_message = "Length must be greater than zero."
            logger.critical("Raising ValueError(%s)." % error_message)
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
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.contact_mentioned.__name__)
        if not isinstance(contact, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("contact", "Contact", contact)
        if len([mention for mention in self._mentions if mention.contact == contact]) > 0:
            return True
        return False

    def get_conflicting_mention(self, mention: Mention) -> Optional[Mention]:
        """
        Get the first existing mention that conflicts with the given mention.
        :param mention: Mention: The mention to check.
        :return: Optional[Mention]: The first conflicting Mention, None if no conflict.
        :raises TypeError: if mention is not a Mention object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_conflicting_mention.__name__)
        if not isinstance(mention, Mention):
            logger.critical("Raising TypeError:")
            __type_error__('mention', 'Mention', mention)
        for pos in range(mention.start, mention.start + mention.length + 1):
            for m in self._mentions:
                if pos in range(m.start, m.start + m.length + 1):
                    return m
        return None

    def mention_conflicts(self, mention: Mention) -> bool:
        """
        Return True if an existing mention conflicts with a given mention.
        :param mention: Mention: The Mention to check.
        :return: bool: True there is a conflict, False there is no conflict.
        :raises TypeError: If mention is not a Mention object.
        """
        conflict: Optional[Mention] = self.get_conflicting_mention(mention)
        return conflict is not None

    #######################################
    # Methods:
    #######################################
    def append(self, mention: Mention) -> None:
        """
        Append a mention to the mention list.
        :param mention: Mention: The mention to append.
        :returns: None
        :raises: TypeError: If the mention is not a Mention object.
        :raises: RuntimeError: If the mention is already in the mention list, or conflicts with an existing mention.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.append.__name__)
        # Type check argument:
        if not isinstance(mention, Mention):
            logger.critical("Raising TypeError:")
            __type_error__("mention", "Mention", mention)
        # Check if mention conflicts:
        if self.mention_conflicts(mention):
            error_message: str = "mention conflicts with an existing mention"
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Append the mention:
        self._mentions.append(mention)
        return

    def create(self, contact: Contact, start: int, length: int) -> Mention:
        """
        Create and append a mention to the list.
        :param contact: Contact: The contact to mention.
        :param start: int: The start position of the mention.
        :param length: int: The length of the mention.
        :returns: Mention: The mention created.
        :raises TypeError: If contact is not a Contact object, start is not an int, or length is not an int.
        :raises RuntimeError: If the created mention conflicts with a mention in the existing mentions.
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
        #TODO: Check this out more.
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.create_from_body.__name__)
        if not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "str", body)
        regex = re.compile(
          r'(@<(\+\d+|[0-9a-fA-F]{8}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{12}|[\"\'].+[\"\']))'
        )
        match_list = regex.findall(body)
        last_find = 0
        return_value = []
        for match, contact_id, _, _ in match_list:
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
