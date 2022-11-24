#!/usr/bin/env python3

from typing import Optional, Any
from signalContacts import Contacts
from signalContact import Contact

class Mention(object):
    def __init__(self,
                    contacts: Contacts,
                    fromDict: Optional[dict[str, Any]] = None,
                    rawMention: Optional[dict[str, Any]] = None,
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
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse from raw Mention:
        elif (rawMention != None):
            self.__fromRawMention__(rawMention)
        return
########################
# Init:
########################
    def __fromRawMention__(self, rawMention:dict) -> None:
        print(rawMention)
        if (rawMention['number'] != None):
            added, self.contact = self._contacts.__getOrAdd__(rawMention['name'], rawMention['number'])
        else:
            added, self.contact = self._contacts.__getOrAdd__(rawMention['name'], rawMention['uuid'])
        self.start = rawMention['start']
        self.length = rawMention['length']
        return
######################
# Overrides:
######################
    def __str__(self) -> str:
        mentionStr = "%i:%i:%s" % (self.start, self.length, self.contact.getId())
        return mentionStr
######################
# To / From Dict:
######################
    def __toDict__(self) -> dict[str, object]:
        mentionDict = {
            "contactId": self.contact.getId(),
            "start": self.start,
            "length": self.length,
        }
        return mentionDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        added, self.contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", fromDict['contactId'])
        self.start = fromDict['start']
        self.length = fromDict['length']
        return

