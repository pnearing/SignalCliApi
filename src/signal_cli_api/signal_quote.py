#!/usr/bin/env python3
"""
File: signal_quote.py
Store and manage a signal quote.
"""
# pylint: disable=R0902, R0903, R0912, R0913, R0914, R0915
import logging
from typing import Optional, Iterable, Any

from .signal_attachment import SignalAttachment
from .signal_common import __type_error__, ConversationTypes
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_mention import SignalMention
from .signal_mentions import SignalMentions
from .signal_timestamp import SignalTimestamp
from .signal_exceptions import ParameterError


class SignalQuote:
    """
    Class to store a quote for a message.
    """
    def __init__(self,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_quote: Optional[dict[str, Any]] = None,
                 timestamp: Optional[SignalTimestamp] = None,
                 author: Optional[SignalContact] = None,
                 text: Optional[str] = None,
                 attachments: Optional[Iterable[SignalAttachment] | SignalAttachment] = None,
                 mentions: Optional[Iterable[SignalMention]| SignalMentions | SignalMention] = None,
                 conversation: Optional[SignalContact | SignalGroup] = None,
                 ) -> None:
        """
        Initialize a quote.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__().
        :param raw_quote: Optional[dict[str, Any]]: The dict provided by signal.
        :param timestamp: Optional[SignalTimestamp]: The timestamp of the quoted message.
        :param author: Optional[SignalContact]: The author of the quote.
        :param text: Optional[str]: The text of the quote.
        :param attachments: Optional[Iterable[SignalAttachment] | SignalAttachment]: Any
            attachments of the quote.
        :param mentions: Optional[Iterable[SignalMention] | SignalMention]: Any mentions in the
            quote.
        :param conversation: Optional[SignalContact | SignalGroup]: The conversation this quote
            is in.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Check config_path:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        # Check contacts:
        if not isinstance(contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "SignalContacts", contacts)
        # Check groups:
        if not isinstance(groups, SignalGroups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "SignalGroups", groups)
        # Check from_dict:
        if from_dict is not None and isinstance(from_dict, dict) is None:
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, object]", from_dict)
        # Check raw_quote:
        if raw_quote is not None and not isinstance(raw_quote, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_quote", "dict[str, object]", raw_quote)
        # Check timestamp:
        if timestamp is not None and not isinstance(timestamp, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "SignalTimestamp", timestamp)
        # Check author:
        if author is not None and not isinstance(author, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("author", "SignalContact", author)
        # Check text:
        if text is not None and not isinstance(text, str):
            logger.critical("Raising TypeError:")
            __type_error__("text", "str", text)
        # Check attachments:
        attachment_list: list[SignalAttachment] = []
        if attachments is not None:
            if isinstance(attachments, SignalAttachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, SignalAttachment):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"attachments[{i}]", "SignalAttachment", attachment)
                    attachment_list.append(attachment)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments", "Iterable[SignalAttachment] | SignalAttachment",
                               attachments)
        # Check mentions:
        mention_list: list[SignalMention] = []
        if mentions is not None:
            if isinstance(mentions, SignalMentions):
                pass
            elif isinstance(mentions, SignalMention):
                mention_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, SignalMention):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"mentions[{i}]", "SignalMention", mention)
                    mention_list.append(mention)
            else:
                __type_error__("mentions", "Iterable[SignalMention] | SignalMentions "
                                           "| SignalMention", mentions)
        # Check conversation:
        if conversation is not None:
            if (not isinstance(conversation, SignalContact) and
                    not isinstance(conversation, SignalGroup)):
                logger.critical("Raising TypeError:")
                __type_error__("conversation", "SignalContact | SignalGroup", conversation)

        # Parameter check:
        if conversation is None and raw_quote is not None:
            error_message: str = "'conversation' must be defined if using 'raw_quote'"
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        # Set internal vars:
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._contacts: SignalContacts = contacts
        """This accounts' SignalContacts object."""
        self._groups: SignalGroups = groups
        """This accounts' SignalGroups object."""

        # Set external properties:
        self.timestamp: SignalTimestamp = timestamp
        """The timestamp of this quote?"""
        self.author: SignalContact = author
        """The author of the quoted message."""
        self.text: str
        """The body of the quoted message."""
        if text is None:
            self.text = ''
        else:
            self.text = text
        self.attachments: list[SignalAttachment] = attachment_list
        """Any attachments of the quoted message."""
        self.mentions: SignalMentions
        """Any mentions in the quoted message."""
        if isinstance(mentions, SignalMentions):
            self.mentions = mentions
        elif len(mention_list) == 0:
            self.mentions = SignalMentions(contacts=contacts)
        else:
            self.mentions = SignalMentions(contacts=contacts, mentions=mention_list)
        self.conversation: Optional[SignalContact | SignalGroup] = conversation
        """The conversation SignalContact or SignalGroup the quoted message is in."""
        self.conversation_type: Optional[ConversationTypes] = None
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw quote
        elif raw_quote is not None:
            self.__from_raw_quote__(raw_quote)
        # Set conversation type based on conversation value.
        if self.conversation is not None:
            if isinstance(self.conversation, SignalContact):
                self.conversation_type = ConversationTypes.CONTACT
            else:
                self.conversation_type = ConversationTypes.GROUP

    #################
    # Init:
    #################
    def __from_raw_quote__(self, raw_quote: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_quote: dict[str, Any]: The dict to load from.
        :return: None
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' +
        #                                            self.__from_raw_quote__.__name__)
        # logger.debug("'raw_quote': %s" % str(raw_quote))
        # Load timestamp
        self.timestamp = SignalTimestamp(timestamp=raw_quote['id'])
        # Load author
        author_number: str = raw_quote['authorNumber']
        author_uuid: str = raw_quote['authorUuid']
        _, self.author = self._contacts.__get_or_add__(number=author_number, uuid=author_uuid,)
        # Load text
        self.text = raw_quote['text']
        # Load attachments
        self.attachments = []
        raw_attachments: list[dict[str, Any]] = raw_quote['attachments']
        for raw_attachment in raw_attachments:
            self.attachments.append(SignalAttachment(config_path=self._config_path,
                                                     raw_attachment=raw_attachment))
        # Load Mentions:
        if 'mentions' in raw_quote.keys():
            self.mentions = SignalMentions(contacts=self._contacts,
                                           raw_mentions=raw_quote['mentions'])

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
            self.timestamp = SignalTimestamp(from_dict=from_dict['timestamp'])
        # Set author
        self.author = None
        if from_dict['author'] is not None:
            _, self.author = self._contacts.__get_or_add__(contact_id=from_dict['author'])
        # Set text
        self.text = from_dict['text']
        # Set attachments:
        self.attachments = []
        for attachment_dict in from_dict['attachments']:
            self.attachments.append(SignalAttachment(config_path=self._config_path,
                                                     from_dict=attachment_dict))
        # Set mentions:
        self.mentions = None
        if from_dict['mentions'] is not None:
            self.mentions = SignalMentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Set conversation type:
        self.conversation_type = ConversationTypes(from_dict['conversationType'])
        # Set conversation:
        self.conversation = None
        if self.conversation_type == ConversationTypes.CONTACT:
            _, self.conversation = self._contacts.__get_or_add__(
                contact_id=from_dict['conversation'])
        elif self.conversation_type == ConversationTypes.GROUP:
            _, self.conversation = self._groups.__get_or_add__(group_id=from_dict['conversation'])

    ##########################
    # Methods:
    ##########################
    def parse_mentions(self) -> str:
        """
        Parse the mentions contained in the quote.
        :returns: str: The text with the mentions inserted.
        """
        return self.mentions.__parse_mentions__(self.text)
