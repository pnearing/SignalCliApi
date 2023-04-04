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
DEBUG: bool = False


class Reactions(object):
    """Class to store reactions to a message."""
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: dict[str, object] = None,
                 reactions: Optional[Iterable[Reaction]] = None,
                 ) -> None:
        # Argument checks:
        if not isinstance(command_socket, socket.socket):
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(account_id, str):
            __type_error__("contact_id", "str", account_id)
        if not isinstance(contacts, Contacts):
            __type_error__("contacts", "Contacts", contacts)
        if not isinstance(groups, Groups):
            __type_error__("groups", "Groups", groups)
        if not isinstance(devices, Devices):
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            __type_error__("this_device", "Device", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        self._account_id: str = account_id
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Devices = devices
        self._this_device: Device = this_device
        self._reactions: list[Reaction] = []
        if reactions is not None:
            for i, reaction in enumerate(reactions):
                if not isinstance(reaction, Reaction):
                    __type_error__("reactions[%i]" % i, "Reaction", reaction)
                self._reactions.append(reaction)
        return

    ############################
    # Overrides:
    ############################
    def __iter__(self) -> Iterator[Reaction]:
        return iter(self._reactions)

    def __getitem__(self, index: int) -> Reaction:
        if not isinstance(index, int):
            __type_error__("index", "int", index)
        return self._reactions[index]

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict[str, object]:
        reactions_dict = {
            'reactions': []
        }
        for reaction in self._reactions:
            reactions_dict['reactions'].append(reaction.__to_dict__())
        return reactions_dict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        self._reactions = []
        for reaction_dict in from_dict['reactions']:
            reaction = Reaction(command_socket=self._command_socket, contacts=self._contacts, groups=self._groups,
                                devices=self._devices, this_device=self._this_device, from_dict=reaction_dict)
            self._reactions.append(reaction)
        return

    ####################
    # Methods:
    ####################
    def __parse__(self, reaction: Reaction) -> None:
        # Parse a remove request:
        if reaction.is_remove:
            self.__remove__(reaction)
            return
        # Try to find a previous reaction:
        previousReaction = self.get_by_contact(reaction.sender)
        if previousReaction is None:
            self.__add_reaction__(reaction)
        else:
            self.__replace__(previousReaction, reaction)
        return

    def __add_reaction__(self, newReaction: Reaction) -> None:
        if not isinstance(newReaction, Reaction):
            __type_error__("new_reaction", "Reaction", newReaction)
        if newReaction in self._reactions:
            raise RuntimeError("reaction already in reactions.")
        self._reactions.append(newReaction)
        return

    def __remove__(self, target_reaction: Reaction) -> None:
        if not isinstance(target_reaction, Reaction):
            __type_error__("target_reaction", "Reaction", target_reaction)
        for index in range(len(self._reactions)):
            reaction = self._reactions[index]
            if reaction.sender == target_reaction.sender:
                self._reactions.pop(index)
                return
        raise RuntimeError("target_reaction not found in reactions.")

    def __replace__(self, old_reaction: Reaction, new_reaction: Reaction) -> None:
        self.__remove__(old_reaction)
        new_reaction.is_change = True
        new_reaction.__update_body__()
        self.__add_reaction__(new_reaction)
        return

    def reaction_in(self, target_reaction: Reaction) -> bool:
        """
        Return True if a given reaction is in the reactions list.
        :param target_reaction: Reaction: Reaction to search for.
        :returns: bool: True if reaction in reaction list.
        :raises: TypeError: If target_reaction is not a reaction object.
        """
        if not isinstance(target_reaction, Reaction):
            __type_error__("target_reaction", "Reaction", target_reaction)
        return target_reaction in self._reactions

    ###########################
    # Getters:
    ###########################

    def get_by_contact(self, contact: Contact) -> Optional[Reaction]:
        """
        Get by contact
        :param: str: contact: The contact to search by.
        :returns: The Reaction found or None if not found.
        :raises: TypeError if contact is not a Contact object.
        """
        if not isinstance(contact, Contact):
            __type_error__("contact", "Contact | str", contact)
        for reaction in self._reactions:
            if reaction.sender == contact:
                return reaction
        return None

    def get_by_emoji(self, emoji: str) -> tuple[Reaction]:
        """
        Get by emoji
        :param: str: emoji: The emoji to search for.
        :returns: tuple[Reaction]: The reactions found. an empty tuple if not found.
        :raises: TypeError: If emoji is not a string.
        """
        if not isinstance(emoji, str):
            __type_error__("emoji", "str", emoji)
        if len(emoji) == 0 or len(emoji) > 2:
            raise ValueError("emoji must be one or 2 characters")
        reactions = [reaction for reaction in self._reactions if reaction.emoji == emoji]
        return tuple(reactions)

    def get_by_recipient(self, recipient: Contact | Group) -> tuple[Reaction]:
        """
        Get by recipient
        :param: Contact | Group: The recipient to search for.
        :returns: tuple[Reaction]: The reactions found, or an empty tuple if not found.
        :raises: TypeError: If recipient is not a Contact object.
        """
        if not isinstance(recipient, Contact) and not isinstance(recipient, Group):
            __type_error__("recipient", "Contact | Group", recipient)
        reactions = [reaction for reaction in self._reactions if reaction.recipient == recipient]
        return tuple(reactions)
