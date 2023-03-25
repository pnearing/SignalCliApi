#!/usr/bin/env python3
from typing import Optional, Iterable, Iterator
import re

from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalMention import Mention


class Mentions(object):
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
                __type_error__("raw_mentions", "list[dict[str, object]]", raw_mentions)
            i = 0
            for rawMention in raw_mentions:
                if not isinstance(rawMention, dict):
                    __type_error__("raw_mention[%i]" % i, "dict", rawMention)
                i += 1
        # Argument Check mentions:
        mentions_list: list[Mention] = []
        if mentions is not None:
            if not isinstance(mentions, Iterable):
                __type_error__("mentions", "Optional[Iterable[Mention]]", mentions)
            i = 0
            for mention in mentions:
                if (isinstance(mention, Mention) == False):
                    __type_error__("mentions[%i]" % i, "Mention", mention)
                mentions_list.append(mention)
                i = i + 1
        if mentions is not None:
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
    def __parse_mentions__(self, body) -> str:
        for mention in self._mentions:
            body_start = body[:mention.start]
            body_end = body[mention.start + mention.length:]
            body = body_start + mention.contact.get_display_name() + body_end
        return body

    #######################################
    # Getters:
    #######################################
    def get_by_contact(self, contact: Contact) -> list[Mention]:
        return [mention for mention in self._mentions if mention.contact == contact]

    def get_by_start_pos(self, start: int) -> list[Mention]:
        return [mention for mention in self._mentions if mention.start == start]

    def get_by_length(self, length: int) -> list[Mention]:
        return [mention for mention in self._mentions if mention.length == length]

    #######################################
    # Tests:
    #######################################
    def contact_mentioned(self, contact: Contact) -> bool:
        mentions = [mention for mention in self._mentions if mention.contact == contact]
        if len(mentions) > 0:
            return True
        return False

    #######################################
    # Methods:
    #######################################
    def append(self, mention: Mention) -> None:
        if mention in self._mentions:
            errorMessage = "mention already exists."
            raise RuntimeError(errorMessage)
        self._mentions.append(mention)
        return

    def create(self, contact: Contact, start: int, length: int) -> Mention:
        mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
        self.append(mention)
        return mention

    def create_from_body(self, body: str) -> list[Mention]:
        if not isinstance(body, str):
            __type_error__("body", "str", body)
        regex = re.compile(
            r'(@<(\+\d+|[0-9a-fA-F]{8}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{12})>)')
        matchList = regex.findall(body)
        lastFind = 0
        returnValue = []
        for (match, contactId) in matchList:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)
            start = body.find(match, lastFind)
            length = len(match)
            lastFind = start
            mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
            self._mentions.append(mention)
            returnValue.append(mention)
            # print(match, " ", str(mention))
        return returnValue
