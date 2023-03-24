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

global DEBUG
DEBUG: bool = True

class Quote(object):
    def __init__(self,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    fromDict:Optional[dict[str, object]] = None,
                    rawQuote:Optional[dict[str, object]] = None,
                    timestamp: Optional[Timestamp] = None,
                    author: Optional[Contact] = None,
                    text: Optional[str] = None,
                    attachments: Optional[Iterable[Attachment] | Attachment] = None,
                    mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                    conversation: Optional[Contact|Group] = None,
                ) -> None:
    # Check config_path:
        if (isinstance(configPath, str) == False):
            __type_error__("config_path", "str", configPath)
    # Check contacts:
        if (isinstance(contacts, Contacts) == False):
            __type_error__("contacts", "Contacts", contacts)
    # Check groups:
        if (isinstance(groups, Groups) == False):
            __type_error__("groups", "Groups", groups)
    # Check from_dict:
        if (fromDict != None and isinstance(fromDict, dict) == None):
            __type_error__("from_dict", "dict[str, object]", fromDict)
    # Check rawQuote:
        if (rawQuote != None and isinstance(rawQuote, dict) == False):
            __type_error__("rawQuote", "dict[str, object]", rawQuote)
    # Check timestamp:
        if (timestamp != None and isinstance(timestamp, Timestamp) == False):
            __type_error__("timestamp", "Timestamp", timestamp)
    # Check author: 
        if (author != None and isinstance(author, Contact) == False):
            __type_error__("author", "Contact", author)
    # Check text:
        if (text != None and isinstance(text, str) == False):
            __type_error__("text", "str", text)
    # Check attachments:
        attachmentList: list[Attachment] = []
        if (attachments != None):
            if (isinstance(attachments, Attachment) == True):
                attachmentList.append(attachments)
            elif (isinstance(attachments, Iterable) == True):
                i = 0
                for attachment in attachments:
                    if (isinstance(attachment, Attachment) == False):
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachmentList.append(attachment)
                    i = i + 1
            else:
                __type_error__("attachments", "Iterable[Attachment] | Attachment")
    # Check mentions:
        mentionList: list[Mention] = []
        if (mentions != None):
            if (isinstance(mentions, Mentions) == True):
                pass
            elif (isinstance(mentions, Mention) == True):
                mentionList.append(mentions)
            elif (isinstance(mentions, Iterable) == True):
                i = 0
                for mention in mentions:
                    if (isinstance(mention, Mention) == False):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentionList.append(mention)
                    i = i + 1
            else:
                __type_error__("mentions", "Iterable[Mention] | Mentions | Mention", mentions)
    # Check conversation:
        if (conversation != None):
            if (isinstance(conversation, Contact) == False and isinstance(conversation, Group) == False):
                __type_error__("conversation", "Contact | Group", conversation)
# Set internal vars:
        self._configPath: str = configPath
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
# Set external properties:
    # Set timestamp:
        self.timestamp: Timestamp = timestamp
    # Set author:
        self.author: Contact = author
    # Set text:
        self.text: str
        if (text == None):
            self.text = ''
        else:
            self.text = text
    # Set attachements
        self.attachments: list[Attachment] = attachmentList
    # Set mentions:
        self.mentions: Mentions
        if (isinstance(mentions, Mentions) == True):
            self.mentions = mentions
        elif (len(mentionList) == 0):
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentionList)
    # Set conversation:
        self.conversation: Optional[Contact | Group] = conversation
# Load from dict or rawQuote:
    # Parse from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse raw quote
        elif (rawQuote != None):
            if (self.conversation == None):
                raise RuntimeError("conversation must be defined if using rawQuote")
            self.__fromRawQuote__(rawQuote)
        return

#################
# Init:
#################
    def __fromRawQuote__(self, rawQuote:dict[str, object]) -> None:
        # print(rawQuote)
    # Load timestamp
        self.timestamp = Timestamp(timestamp=rawQuote['id'])
    # Load author
# 'authorNumber': '+16134548055', 'authorUuid'
        added, self.author = self._contacts.__getOrAdd__(
                                                            name="<UNKNOWN-CONTACT>",
                                                            number=rawQuote['authorNumber'],
                                                            uuid=rawQuote['authorUuid']
                                                        )
    # Load text
        self.text = rawQuote['text']
    # Load attachments
        self.attachments = []
        for rawAttachment in rawQuote['attachments']:
            self.attachments.append( Attachment(configPath=self._configPath, rawAttachment=rawAttachment))
    # Load Mentions:
        if ('mentions' in rawQuote.keys()):
            self.mentions = Mentions(contacts=self._contacts, rawMentions=rawQuote['mentions'])
        return

#################
# To / From dict:
#################
    def __toDict__(self) -> dict[str, object]:
        quoteDict = {
            'timestamp': None,
            'author': None,
            'text': self.text,
            'attachments': [],
            'mentions': None,
            'conversation': None,
        }
    # Store timestamp
        if (self.timestamp != None):
            quoteDict['timestamp'] = self.timestamp.__toDict__()
    # Store author:
        if (self.author != None):
            quoteDict['author'] = self.author.getId()
    # Store attachments:
        for attachment in self.attachments:
            quoteDict['attachments'].append(attachment.__toDict__())
    # Store mentions:
        quoteDict['mentions'] = self.mentions.__toDict__()
    # Store conversation:
        if (self.conversation != None):
            quoteDict['conversation'] = self.conversation.getId()
        return quoteDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
    # Set timestamp:
        self.timestamp = None
        if (fromDict['timestamp'] != None):
            self.timestamp = Timestamp(fromDict=fromDict['timestamp'])
    # Set author
        self.author = None
        if (fromDict['author'] != None):
            added, self.author = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=fromDict['author'])
    # Set text
        self.text = fromDict['text']
    # Set attachments:
        self.attachments = []
        for attachmentDict in fromDict['attachments']:
            self.attachments.append( Attachment( configPath=self._configPath, fromDict=attachmentDict ) )
    # Set mentions:
        self.mentions = None
        if (fromDict['mentions'] != None):
            self.mentions = Mentions(contacts=self._contacts, fromDict=fromDict['mentions'])
    # Set conversation:
        self.conversation = None
        if (fromDict["conversationType"] == 'contact'):
            added, self.conversation = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", id=fromDict['conversation'])
        elif (fromDict["conversationType"] == 'group'):
            added, self.conversation = self._groups.__getOrAdd__("<UNKNOWN-GROUP>", fromDict['conversation'])
        return

##########################
# Methods:
##########################
    def parseMentions(self) -> str:
        return self.mentions.__parseMentions__(self.text)