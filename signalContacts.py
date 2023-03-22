#!/usr/bin/env python3

from typing import Optional, Iterator
import sys
import os
import json
import socket

from .signalCommon import __typeError__, __socketReceive__, __socketSend__, phoneNumberRegex, uuidRegex, NUMBER_FORMAT_STR, UUID_FORMAT_STR
from .signalContact import Contact
# from signalSyncMessage import SyncMessage

global DEBUG
DEBUG: bool = True

class Contacts(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    accountPath: str,
                    doLoad:bool = False,
                    doSync:bool = False,
                ) -> None:
    # TODO: Argument checks:
    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._configPath: str = configPath
        self._accountId: str = accountId
        self._accountPath: str = accountPath
        self._contacts: list[Contact] = []
    # Load from file:
        if (doLoad == True):
            try:
                self.__load__()
            except RuntimeError:
                if (DEBUG == True):
                    errorMessage = "Creating empty contacts.json file for account: %s" % self._accountId
                    print(errorMessage, file=sys.stderr)
                self.__save__()
    # Sync with signal:
        if (doSync == True):
            self.__sync__()
            self.__save__()
    # Search for self contact, and create if not found:
        selfContact = self.getByNumber(self._accountId)
        if (selfContact == None):
            self.add("Note-To-Self", self._accountId)
            self.__save__()
        else:
            selfContact.setName("Note-To-Self")
            self.__save__()
        return
##########################
# Overrides:
##########################
    def __iter__(self) -> Iterator[Contact]:
        return iter(self._contacts)
    
    def __len__(self) -> int:
        return len(self._contacts)

    def __getitem__(self, index: int | str) -> Contact:
        if (isinstance(index, int) == True):
            return self._contacts[index]
        elif (isinstance(index, str) == True):
            numberMatch = phoneNumberRegex.match(index)
            uuidMatch = uuidRegex.match(index)
            if (numberMatch != None):
                for contact in self._contacts:
                    if (contact.number == index):
                        return contact
            elif (uuidMatch != None):
                for contact in self._contacts:
                    if (contact.uuid == index):
                        return contact
            else:
                errorMessage = "index must be of format '%s' or '%s'" % (NUMBER_FORMAT_STR, UUID_FORMAT_STR)
            errorMessage = "index not found: %s" % index
            raise IndexError(errorMessage)
        else:
            __typeError__(index, "int | str", index)
##########################
# To / From Dict:
##########################
    def __toDict__(self) -> dict:
        contactsDict = {
            "contacts": [],
        }
        for contact in self._contacts:
            contactsDict['contacts'].append(contact.__toDict__())
        return contactsDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        self._contacts = []
        for contactDict in fromDict['contacts']:
            contact = Contact(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                accountPath=self._accountPath, fromDict=contactDict)
            self._contacts.append(contact)
        return

##############################
# Load / Save:
##############################
    def __save__(self) -> None:
    # Create the contacts object, and json string:
        contactsObj = self.__toDict__()
        contactsJson = json.dumps(contactsObj, indent=4)
    # Build the file Path:
        fileName = "contacts-" + self._accountId + '.json'
        filePath = os.path.join(self._accountPath, fileName)
    # Try to open the file:
        try:
            fileHandle = open(filePath, 'w')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open contacts file '%s' for writing: %s" % (filePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Write the json to the file and close it.
        fileHandle.write(contactsJson)
        fileHandle.close()
        return
    
    def __load__(self) -> None:
    # Build the file Path:
        fileName = 'contacts-' + self._accountId + '.json'
        filePath = os.path.join(self._accountPath, fileName)
    # Try and open the file for reading:
        try:
            fileHandle = open(filePath, 'r')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open '%s' for reading: %s" % (filePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Try and load the json from the file:
        try:
            contactsDict:dict = json.loads(fileHandle.read())
        except json.JSONDecodeError as e:
            errorMessage = "FATAL: Couldn't load json from file '%s': %s" % (filePath, e.msg)
            raise RuntimeError(errorMessage)
    # Load the contacts object:
        self.__fromDict__(contactsDict)
        return

######################
# Sync with signal:
######################
    def __sync__(self) -> list[Contact]:
    # Create list contacts command object, and json command string:
        listContactsCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listContacts",
            "params": {
                "account": self._accountId
            }
        }
        jsonCommandStr = json.dumps(listContactsCommandObj) + '\n'
    # Communicate with signal-cli:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj:dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "ERROR: Signal reported error during contacts sync, code: %i, message: %s" % (responseObj['error']['code'],
                                                                                        responseObj['error']['message'])
                print(errorMessage, file=sys.stderr)
                return
    # Load contacts:
        newContacts = []
        for rawContact in responseObj['result']:
        # Create new contact:
            newContact = Contact(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                    accountPath=self._accountPath, rawContact=rawContact)
        # Check for existing contact:
            contactFound = False
            for contact in self._contacts:
                if (contact.getId() == newContact.getId()):
                    contact.__merge__(newContact)
                    contactFound = True
        # If contact not found add the new contact.
            if (contactFound == False):
                self._contacts.append(newContact)
                newContacts.append(newContact)
        return newContacts
##################################
# Helpers:
##################################
    def __parseSyncMessage__(self, syncMessage) -> None: # syncMessage type = SyncMessage
        if (syncMessage.syncType == 5): # SyncMessage.TYPE_BLOCKED_SYNC
            for contactId in syncMessage.blockedContacts:
                added, contact = self.__getOrAdd__("<UNKNOWN-CONTACT>", contactId)
                contact.isBlocked = True
            self.__save__()
        else:
            errorMessage = "Contacts can only parse messages of type: SyncMessage.TYPE_BLOCKED_SYNC."
            raise TypeError(errorMessage)
        return

    def __getOrAdd__(self, name:str, number:Optional[str]=None, uuid:Optional[str] = None, id:Optional[str] = None) -> tuple[bool, Contact]:
    # Argument check
        if (number == None and uuid == None and id == None):
            RuntimeError("Either number or uuid, or id must be defined.")
    # Check id type:
        if (id != None):
            numberMatch = phoneNumberRegex.match(id)
            uuidMatch = uuidRegex.match(id)
            if (numberMatch == None and uuidMatch == None):
                errorMessage = "id must be in format '%s' or '%s'" % (NUMBER_FORMAT_STR, UUID_FORMAT_STR)
                raise ValueError(errorMessage)
            elif (numberMatch != None):
                number = id
                uuid = None
            elif( uuidMatch != None):
                number = None
                uuid = id
    # Search for contact:
        contact = None
        for contact in self._contacts:
            if (contact.number == number or contact.uuid == uuid):
                contact = contact
            # Merge contact if more info found:
                if (contact.number == None and number !=None):
                    contact.number = number
                    self.__save__()
                if (contact.uuid == None and uuid != None):
                    contact.uuid = uuid
                    self.__save__()
    # If contact found:
        if (contact != None):
            return (False, contact)
    # Set id:
        if (number != None):
            id = number
        else:
            id = uuid
    # add to signal:
        (addedToSignal, contact) = self.add(name, id)
        return (True, contact)

##################################
# Getters:
##################################
    def getByNumber(self, number:str) -> Optional[Contact]:
        numberMatch = phoneNumberRegex.match(number)
        if (numberMatch == None):
            errorMessage = "number must be in format '+nnnnnnnn...'"
            raise ValueError(errorMessage)
        for contact in self._contacts:
            if (contact.number == number):
                return contact
        return None
    
    def getByUuid(self, uuid:str) -> Optional[Contact]:
        uuidMatch = uuidRegex.match(uuid)
        if (uuidMatch == None):
            errorMessage = "uuid must be in format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'"
            raise ValueError(errorMessage)
        for contact in self._contacts:
            if (contact.uuid == uuid):
                return contact
        return None
    
    def getById(self, id:str) -> Optional[Contact]:
        numberMatch = phoneNumberRegex.match(id)
        uuidMatch = uuidRegex.match(id)
        if (numberMatch != None):
            return self.getByNumber(id)
        elif (uuidMatch != None):
            return self.getByUuid(id)
        else:
            errorMessage = "id must be in format '+nnnnnnnnn...' or 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'"
            raise ValueError(errorMessage)

    def getSelf(self) -> Contact:
        for contact in self._contacts:
            if (contact.isSelf == True):
                return contact
        raise RuntimeError("FATAL: Couldn't find self contact, should never get here.")
#########################
# Methods:
#########################
    def add(self, name: str, id: str, expiration:Optional[int]=None) -> tuple[bool, Contact]:
    # TODO: Argument checks:
        oldContact = self.getById(id)
        if (oldContact != None):
            return (False, oldContact)
    # Create add contact command object and json command string:
        addContactCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "updateContact",
            "params": {
                "account": self._accountId,
                "name": name,
                "recipient": id
            }
        }
        if (expiration != None):
            addContactCommandObj['params']['expiration'] = expiration
        jsonCommandStr = json.dumps(addContactCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj:dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "signal error. Code: %i, Message: %s" % (responseObj['error']['code'], responseObj['error']['message'])
                print(errorMessage, file=sys.stderr)
            numberMatch = phoneNumberRegex.match(id)
            uuidMatch = uuidRegex.match(id)
            if (numberMatch != None):
                newContact = Contact(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                    accountPath=self._accountPath, name=name, number=id)
            elif (uuidMatch != None):
                newContact = Contact(syncSocket=self._syncSocket, configPath=self._configPath, accountId=self._accountId,
                                        accountPath=self._accountPath, name=name, uuid=id)
            else:
                errorMessage = "id must be in format '+nnnnnn...' or 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                raise ValueError(errorMessage)
            self._contacts.append(newContact)
            return (False, newContact)
    # Parse result:
        self.__sync__()
        self.__save__()
        newContact = self.getById(id)
        return(True, newContact)
