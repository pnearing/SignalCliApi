#!/usr/bin/env python3

from typing import Optional, Iterable

from .signalAttachment import Attachment
from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalGroup import Group
from .signalGroups import Groups
from .signalMention import Mention
from .signalMentions import Mentions
from .signalTimestamp import Timestamp

DEBUG: bool = False


class Quote(object):
    """Class to store a quote for a message."""
    def __init__(self,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 from_dict: Optional[dict[str, object]] = None,
                 raw_quote: Optional[dict[str, object]] = None,
                 timestamp: Optional[Timestamp] = None,
                 author: Optional[Contact] = None,
                 text: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                 conversation: Optional[Contact | Group] = None,
                 ) -> None:
        # Check config_path:
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        # Check contacts:
        if not isinstance(contacts, Contacts):
            __type_error__("contacts", "Contacts", contacts)
        # Check groups:
        if not isinstance(groups, Groups):
            __type_error__("groups", "Groups", groups)
        # Check from_dict:
        if from_dict is not None and isinstance(from_dict, dict) is None:
            __type_error__("from_dict", "dict[str, object]", from_dict)
        # Check raw_quote:
        if raw_quote is not None and not isinstance(raw_quote, dict):
            __type_error__("raw_quote", "dict[str, object]", raw_quote)
        # Check timestamp:
        if timestamp is not None and not isinstance(timestamp, Timestamp):
            __type_error__("timestamp", "Timestamp", timestamp)
        # Check author:
        if author is not None and not isinstance(author, Contact):
            __type_error__("author", "Contact", author)
        # Check text:
        if text is not None and not isinstance(text, str):
            __type_error__("text", "str", text)
        # Check attachments:
        attachment_list: list[Attachment] = []
        if attachments is not None:
            if isinstance(attachments, Attachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                i: int = 0
                for attachment in attachments:
                    if not isinstance(attachment, Attachment):
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachment_list.append(attachment)
                    i += 1
            else:
                __type_error__("attachments", "Iterable[Attachment] | Attachment")
        # Check mentions:
        mention_list: list[Mention] = []
        if mentions is not None:
            if isinstance(mentions, Mentions):
                pass
            elif isinstance(mentions, Mention):
                mention_list.append(mentions)
            elif isinstance(mentions, Iterable):
                i: int = 0
                for mention in mentions:
                    if not isinstance(mention, Mention):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mention_list.append(mention)
                    i += 1
            else:
                __type_error__("mentions", "Iterable[Mention] | Mentions | Mention", mentions)
        # Check conversation:
        if conversation is not None:
            if not isinstance(conversation, Contact) and not isinstance(conversation, Group):
                __type_error__("conversation", "Contact | Group", conversation)
        # Set internal vars:
        self._config_path: str = config_path
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        # Set external properties:
        # Set timestamp:
        self.timestamp: Timestamp = timestamp
        # Set author:
        self.author: Contact = author
        # Set text:
        self.text: str
        if text is None:
            self.text = ''
        else:
            self.text = text
        # Set attachments
        self.attachments: list[Attachment] = attachment_list
        # Set mentions:
        self.mentions: Mentions
        if isinstance(mentions, Mentions):
            self.mentions = mentions
        elif len(mention_list) == 0:
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mention_list)
        # Set conversation:
        self.conversation: Optional[Contact | Group] = conversation
        # Load from dict or raw_quote:
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw quote
        elif raw_quote is not None:
            if self.conversation is None:
                raise RuntimeError("conversation must be defined if using raw_quote")
            self.__from_raw_quote__(raw_quote)
        return

    #################
    # Init:
    #################
    def __from_raw_quote__(self, raw_quote: dict[str, object]) -> None:
        print(raw_quote)
        exit(253)
        # Load timestamp
        # TODO: Look into this:
        self.timestamp = Timestamp(timestamp=raw_quote['contact_id'])
        # Load author
        author_number: str = raw_quote['authorNumber']
        author_uuid: str = raw_quote['authorUuid']
        added, self.author = self._contacts.__get_or_add__(
            name="<UNKNOWN-CONTACT>",
            number=author_number,
            uuid=author_uuid,
        )
        # Load text
        self.text = raw_quote['text']
        # Load attachments
        self.attachments = []
        raw_attachments: list[dict[str, object]] = raw_quote['attachments']
        for raw_attachment in raw_attachments:
            self.attachments.append(Attachment(config_path=self._config_path, raw_attachment=raw_attachment))
        # Load Mentions:
        if 'mentions' in raw_quote.keys():
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=raw_quote['mentions'])
        return

    #################
    # To / From dict:
    #################
    def __to_dict__(self) -> dict[str, object]:
        quote_dict = {
            'timestamp': None,
            'author': None,
            'text': self.text,
            'attachments': [],
            'mentions': None,
            'conversation': None,
        }
        # Store timestamp
        if self.timestamp is not None:
            quote_dict['timestamp'] = self.timestamp.__to_dict__()
        # Store author:
        if self.author is not None:
            quote_dict['author'] = self.author.get_id()
        # Store attachments:
        for attachment in self.attachments:
            quote_dict['attachments'].append(attachment.__to_dict__())
        # Store mentions:
        quote_dict['mentions'] = self.mentions.__to_dict__()
        # Store conversation:
        if self.conversation is not None:
            quote_dict['conversation'] = self.conversation.get_id()
        return quote_dict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        # Set timestamp:
        self.timestamp = None
        if from_dict['timestamp'] is not None:
            timestamp_dict: dict[str, object] = from_dict['timestamp']
            self.timestamp = Timestamp(from_dict=timestamp_dict)
        # Set author
        self.author = None
        if from_dict['author'] is not None:
            added, self.author = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=from_dict['author'])
        # Set text
        self.text = from_dict['text']
        # Set attachments:
        self.attachments = []
        attachment_dicts: list[dict[str, object]] = from_dict['attachments']
        for attachment_dict in attachment_dicts:
            self.attachments.append(Attachment(config_path=self._config_path, from_dict=attachment_dict))
        # Set mentions:
        self.mentions = None
        if from_dict['mentions'] is not None:
            mentions_dict: dict[str, object] = from_dict['mentions']
            self.mentions = Mentions(contacts=self._contacts, from_dict=mentions_dict)
        # Set conversation:
        self.conversation = None
        if from_dict["conversationType"] == 'contact':
            added, self.conversation = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                     contact_id=from_dict['conversation'])
        elif from_dict["conversationType"] == 'group':
            added, self.conversation = self._groups.__get_or_add__("<UNKNOWN-GROUP>", from_dict['conversation'])
        return

    ##########################
    # Methods:
    ##########################
    def parse_mentions(self) -> str:
        """
        Parse the mentions contained in the quote.
        :returns: str: The text with the mentions inserted.
        """
        return self.mentions.__parse_mentions__(self.text)
