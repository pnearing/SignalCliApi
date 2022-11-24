#!/usr/bin/env python3
from typing import Optional, Iterable, Iterator
import re

from signalCommon import __typeError__
from signalContact import Contact
from signalContacts import Contacts
from signalMention import Mention

class Mentions(object):
    def __init__(self,
                    contacts:Contacts,
                    fromDict:Optional[dict[str, object]] = None,
                    rawMentions: Optional[list[dict[str, object]]] = None,
                    mentions:Optional[Iterable[Mention]] = None,
                ) -> None:
    # Argument check contacts:
        if (isinstance(contacts, Contacts) == False):
            __typeError__("contacts", "Contacts", contacts)
    # Argument check fromDict:
        if (fromDict != None and isinstance(fromDict,dict) == False):
            __typeError__("fromDict", "dict", fromDict)
    # Argument check rawMentions:
        if (rawMentions != None):
            if (isinstance(rawMentions, list) == False):
                __typeError__("rawMentions", "list[dict[str, object]]", rawMentions)
            i = 0
            for rawMention in rawMentions:
                if (isinstance(rawMention, dict) == False):
                    __typeError__("rawMention[%i]" % i, "dict", rawMention)
                i = i + 1
    # Argument Check mentions:
        mentionsList: list[Mention] = []
        if (mentions != None):
            if (isinstance(mentions, Iterable) == False):
                __typeError__("mentions", "Optional[Iterable[Mention]]", mentions)
            i = 0
            for mention in mentions:
                if (isinstance(mention, Mention) == False):
                    __typeError__("mentions[%i]" % i, "Mention", mention)
                mentionsList.append(mention)
                i = i + 1
        if (mentions != None):
            if (len(mentionsList) == 0):
                raise ValueError("mentions cannot be empty")
    # Set internal vars:
        self._contacts: Contacts = contacts
        self._mentions: list[Mention] = mentionsList
    # Parse from Dict:  
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse raw Mentions:
        elif (rawMentions != None):
            self.__fromRawMentions__(rawMentions)
        return
##############################
# Init:
##############################
    def __fromRawMentions__(self, rawMentions:list[dict]) -> None:
        self._mentions = []
        for rawMention in rawMentions:
            mention = Mention(contacts=self._contacts, rawMention=rawMention)
            self._mentions.append(mention)
        return
#######################################
# Overrides:
#######################################
    def __iter__(self) -> Iterator[Mention]:
        return iter(self._mentions)

    def __len__(self) -> int:
        return len(self._mentions)
    
    def __getitem__(self, index:int|Contact) -> Mention:
        if (isinstance(index, int) == True):
            return self._mentions[index]
        elif (isinstance(index, Contact) == True):
            for mention in self._mentions:
                if (mention.contact == index):
                    return mention
            raise IndexError("Mention with contactId: %s not found." % index.getId())
        else:
            __typeError__("index", "int | Contact", index)

#######################################
# To / From Dict:
#######################################
    def __toDict__(self) -> dict[str, object]:
        mentionsDict = {
            "mentions": [],
        }
        for mention in self._mentions:
            mentionsDict['mentions'].append(mention.__toDict__())
        return mentionsDict
    
    def __fromDict__(self, fromDict:dict[str, object]) -> None:
        self._mentions = []
        for mentionDict in fromDict['mentions']:
            self._mentions.append(Mention(contacts=self._contacts, fromDict=mentionDict))
        return
#########################################
# Helpers:
#########################################
    def __parseMentions__(self, body) -> str:
        for mention in self._mentions:
            bodyStart = body[:mention.start]
            bodyEnd = body[mention.start + mention.length:]
            body = bodyStart + mention.contact.getDisplayName() + bodyEnd
        return body

#######################################
# Getters:
#######################################
    def getByContact(self, contact:Contact) -> list[Mention]:
        return [mention for mention in self._mentions if mention.contact == contact]
    
    def getByStartPos(self, start:int) -> list[Mention]:
        return [mention for mention in self._mentions if mention.start == start]
    
    def getByLength(self, length:int) -> list[Mention]:
        return [mention for mention in self._mentions if mention.length == length]


#######################################
# Methods:
#######################################
    def append(self, mention:Mention) -> None:
        if (mention in self._mentions):
            errorMessage = "mention already exists."
            raise RuntimeError(errorMessage)
        self._mentions.append(mention)
        return

    def create(self, contact:Contact, start:int, length:int) -> Mention:
        mention = Mention(contacts=self._contacts, contact=contact, start=start, length=length)
        self.append(mention)
        return mention
    
    def createFromBody(self, body:str) -> list[Mention]:
        if (isinstance(body, str) == False):
            __typeError__("body", "str", body)
        regex = re.compile(r'(@<(\+\d+|[0-9a-fA-F]{8}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{4}-[0-9a-f-A-F]{12})>)')
        matchList = regex.findall(body)
        lastFind = 0
        returnValue = []
        for (match, contactId) in matchList:
            added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", contactId)
            start = body.find(match,lastFind)
            length = len(match)
            lastFind = start
            mention = Mention(contacts=self._contacts, contact=contact, start=start,length=length)
            self._mentions.append(mention)
            returnValue.append(mention)
            # print(match, " ", str(mention))
        return returnValue

