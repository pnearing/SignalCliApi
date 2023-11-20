#!/usr/bin/env python3
"""
File: signalQuote.py
Store and manage a signal quote.
"""
import logging
from typing import Optional, Iterable, Any

from .signalAttachment import Attachment
from .signalCommon import __type_error__, ConversationTypes
from .signalContact import Contact
from .signalContacts import Contacts
from .signalGroup import Group
from .signalGroups import Groups
from .signalMention import Mention
from .signalMentions import Mentions
from .signalTimestamp import Timestamp
from .signalExceptions import ParameterError


class Quote(object):
    """
    Class to store a quote for a message.
    """
    def __init__(self,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_quote: Optional[dict[str, Any]] = None,
                 timestamp: Optional[Timestamp] = None,
                 author: Optional[Contact] = None,
                 text: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                 conversation: Optional[Contact | Group] = None,
                 ) -> None:
        """
        Initialize a quote.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__().
        :param raw_quote: Optional[dict[str, Any]]: The dict provided by signal.
        :param timestamp: Optional[Timestamp]: The timestamp.# TODO: Figure out a better description.
        :param author: Optional[Contact]: The author of the quote.
        :param text: Optional[str]: The text of the quote.
        :param attachments: Optional[Iterable[Attachment] | Attachment]: Any attachments of the quote.
        :param mentions: Optional[Iterable[Mention] | Mention]: Any mentions in the quote.
        :param conversation: Optional[Contact | Group]: The conversation this quote is in.
        """
        # Super:
        super().__init__()

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Check config_path:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        # Check contacts:
        if not isinstance(contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "Contacts", contacts)
        # Check groups:
        if not isinstance(groups, Groups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "Groups", groups)
        # Check from_dict:
        if from_dict is not None and isinstance(from_dict, dict) is None:
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, object]", from_dict)
        # Check raw_quote:
        if raw_quote is not None and not isinstance(raw_quote, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_quote", "dict[str, object]", raw_quote)
        # Check timestamp:
        if timestamp is not None and not isinstance(timestamp, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "Timestamp", timestamp)
        # Check author:
        if author is not None and not isinstance(author, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("author", "Contact", author)
        # Check text:
        if text is not None and not isinstance(text, str):
            logger.critical("Raising TypeError:")
            __type_error__("text", "str", text)
        # Check attachments:
        attachment_list: list[Attachment] = []
        if attachments is not None:
            if isinstance(attachments, Attachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, Attachment):
                        logger.critical("Raising TypeError:")
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachment_list.append(attachment)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments", "Iterable[Attachment] | Attachment", attachments)
        # Check mentions:
        mention_list: list[Mention] = []
        if mentions is not None:
            if isinstance(mentions, Mentions):
                pass
            elif isinstance(mentions, Mention):
                mention_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, Mention):
                        logger.critical("Raising TypeError:")
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mention_list.append(mention)
            else:
                __type_error__("mentions", "Iterable[Mention] | Mentions | Mention", mentions)
        # Check conversation:
        if conversation is not None:
            if not isinstance(conversation, Contact) and not isinstance(conversation, Group):
                logger.critical("Raising TypeError:")
                __type_error__("conversation", "Contact | Group", conversation)

        # Parameter check:
        if self.conversation is None and raw_quote is None:
            error_message: str = "'conversation' must be defined if using 'raw_quote'"
            logger.critical("Raising ParameterError(%s)." % error_message)
            raise ParameterError(error_message)

        # Set internal vars:
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._contacts: Contacts = contacts
        """This accounts' Contacts object."""
        self._groups: Groups = groups
        """This accounts' Groups object."""

        # Set external properties:
        self.timestamp: Timestamp = timestamp
        """The timestamp of this quote?"""
        self.author: Contact = author
        """The author of the quoted message."""
        self.text: str
        """The body of the quoted message."""
        if text is None:
            self.text = ''
        else:
            self.text = text
        self.attachments: list[Attachment] = attachment_list
        """Any attachments of the quoted message."""
        self.mentions: Mentions
        """Any mentions in the quoted message."""
        if isinstance(mentions, Mentions):
            self.mentions = mentions
        elif len(mention_list) == 0:
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mention_list)
        self.conversation: Optional[Contact | Group] = conversation
        """The conversation Contact or Group the quoted message is in."""
        self.conversation_type: Optional[ConversationTypes] = None
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw quote
        elif raw_quote is not None:
            self.__from_raw_quote__(raw_quote)
        # Set conversation type based on conversation value.
        if self.conversation is not None:
            if isinstance(self.conversation, Contact):
                self.conversation_type = ConversationTypes.CONTACT
            else:
                self.conversation_type = ConversationTypes.GROUP
        return

    #################
    # Init:
    #################
    def __from_raw_quote__(self, raw_quote: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_quote: dict[str, Any]: The dict to load from.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_raw_quote__.__name__)
        logger.debug("'raw_quote': %s" % str(raw_quote))
        # Load timestamp
        # TODO: Look into this:
        self.timestamp = Timestamp(timestamp=raw_quote['timestamp'])
        # Load author
        author_number: str = raw_quote['authorNumber']
        author_uuid: str = raw_quote['authorUuid']
        added, self.author = self._contacts.__get_or_add__(number=author_number, uuid=author_uuid,)
        # Load text
        self.text = raw_quote['text']
        # Load attachments
        self.attachments = []
        raw_attachments: list[dict[str, Any]] = raw_quote['attachments']
        for raw_attachment in raw_attachments:
            self.attachments.append(Attachment(config_path=self._config_path, raw_attachment=raw_attachment))
        # Load Mentions:
        if 'mentions' in raw_quote.keys():
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=raw_quote['mentions'])
        return

    #################
    # To / From dict:
    #################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this quote.
        :return: dict[str, Any]: A dict to provide to __from_dict__().
        """
        quote_dict: dict[str, Any] = {
            'timestamp': None,
            'author': None,
            'text': self.text,
            'attachments': [],
            'mentions': None,
            'conversation': None,
            'conversationType': self.conversation_type.value
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

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None.
        """
        # Set timestamp:
        self.timestamp = None
        if from_dict['timestamp'] is not None:
            self.timestamp = Timestamp(from_dict=from_dict['timestamp'])
        # Set author
        self.author = None
        if from_dict['author'] is not None:
            _, self.author = self._contacts.__get_or_add__(contact_id=from_dict['author'])
        # Set text
        self.text = from_dict['text']
        # Set attachments:
        self.attachments = []
        for attachment_dict in from_dict['attachments']:
            self.attachments.append(Attachment(config_path=self._config_path, from_dict=attachment_dict))
        # Set mentions:
        self.mentions = None
        if from_dict['mentions'] is not None:
            self.mentions = Mentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Set conversation type:
        self.conversation_type = ConversationTypes(from_dict['conversationType'])
        # Set conversation:
        self.conversation = None
        if self.conversation_type == ConversationTypes.CONTACT:
            _, self.conversation = self._contacts.__get_or_add__(contact_id=from_dict['conversation'])
        elif self.conversation_type == ConversationTypes.GROUP:
            _, self.conversation = self._groups.__get_or_add__(group_id=from_dict['conversation'])
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
