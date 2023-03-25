#! /usr/bin/env python3

from typing import Optional, Iterable, Iterator
import socket

from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalReaction import Reaction

class Reactions(object):
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    fromDict: dict[str, object] = None,
                    reactions: Optional[Iterable[Reaction]] = None,
                ) -> None:
    # Argument checks:
        if (isinstance(commandSocket, socket.socket) == False):
            __type_error__("command_socket", "socket.socket", commandSocket)
        if (isinstance(accountId, str) == False):
            __type_error__("contact_id", "str", accountId)
        if (isinstance(contacts, Contacts) == False):
            __type_error__("contacts", "Contacts", contacts)
        if (isinstance(groups, Groups) == False):
            __type_error__("groups", "Groups", groups)
        if (isinstance(devices, Devices) == False):
            __type_error__("devices", "Devices", devices)
        if (isinstance(thisDevice, Device) == False):
            __type_error__("this_device", "Device", thisDevice)
        if (fromDict != None and isinstance(fromDict, dict) == False):
            __type_error__("from_dict", "dict", fromDict)
    # Set internal vars:
        self._commandSocket: socket.socket = commandSocket
        self._accountId: str = accountId
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Devices = devices
        self._thisDevice: Device = thisDevice
        self._reactions: list[Reaction] = []
        if (reactions != None):
            i = 0
            for reaction in reactions:
                if (isinstance(reaction, Reaction) == False):
                    __type_error__("reactions[%i]" % i, "Reaction", reaction)
                i = i + 1
                self._reactions.append(reaction)
        return

############################
# Overrides:
############################
    def __iter__(self) -> Iterator[Reaction]:
        return iter(self._reactions)
    
    def __getitem__(self, index:int) -> Reaction:
        if (isinstance(index, int) == False):
            __type_error__("index", "int", index)
        return self._reactions[index]

#########################
# To / From Dict:
#########################
    def __toDict__(self) -> dict[str, object]:
        reactionsDict = {
            'reactions': []
        }
        for reaction in self._reactions:
            reactionsDict['reactions'].append(reaction.__to_dict__())
        return reactionsDict
    
    def __fromDict__(self, fromDict) -> None:
        self._reactions = []
        for reactionDict in fromDict['reactions']:
            reaction = Reaction(command_socket=self._commandSocket, contacts=self._contacts, groups=self._groups,
                                device=self._devices, from_dict=reactionDict)
            self._reactions.append(reaction)
        return

####################
# Methods:
####################
    def __parse__(self, reaction:Reaction) -> None:
    # Parse a remove request:
        if (reaction.is_remove == True):
            self.__remove__(reaction)
            return
    # Try to find a previous reaction:
        previousReaction = self.getByContact(reaction.sender)
        if (previousReaction == None):
            self.__add__(reaction)
        else:
            self.__replace__(previousReaction, reaction)
        return

    def __add__(self, newReaction:Reaction) -> None:
        if (isinstance(newReaction, Reaction) == False):
            __type_error__("newReaction", "Reaction", newReaction)
        if (newReaction in self._reactions):
            raise RuntimeError("reaction already in reactions.")
        self._reactions.append(newReaction)
        return

    def __remove__(self, targetReaction:Reaction) -> None:
        if (isinstance(targetReaction, Reaction) == False):
            __type_error__("targetReaction", "Reaction", targetReaction)
        for index in range(len(self._reactions)):
            reaction = self._reactions[index]
            if (reaction.sender == targetReaction.sender):
                self._reactions.pop(index)
                return
        raise RuntimeError("targetReaction not found in reactions.")

    def __replace__(self, oldReaction:Reaction, newReaction:Reaction) -> None:
        self.__remove__(oldReaction)
        newReaction.is_change = True
        newReaction.__update_body__()
        self.__add__(newReaction)
        return

    def reactionIn(self, targetReaction:Reaction) -> bool:
        return (targetReaction in self._reactions)

###########################
# Getters:
###########################

    def getByContact(self, contact:Contact) -> Optional[Reaction]:
        if (isinstance(contact, Contact) == False):
            __type_error__("contact", "Contact | str", contact)
        for reaction in self._reactions:
            if (reaction.sender == contact):
                return reaction
        return None

    def getByEmoji(self, emoji:str) -> tuple[Reaction]:
        if (isinstance(emoji, str) == False):
            __type_error__("emoji", "str", emoji)
        if (len(emoji) == 0 or len(emoji) > 1):
            raise ValueError("emoji must be one character")
        reactions = [ reaction for reaction in self._reactions if reaction.emoji == emoji ]
        return tuple(reactions)
    
    def getByRecipient(self, recipient: Contact | Group) -> tuple[Reaction]:
        if (isinstance(recipient, Contact) == False and isinstance(recipient, Group) == False):
            __type_error__("recipient", "Contact | Group", recipient)
        reactions = [ reaction for reaction in self._reactions if reaction.recipient == recipient]
        return tuple(reactions)