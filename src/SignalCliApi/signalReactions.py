#! /usr/bin/env python3
"""
File: signalReactions.py
Store and manage a list of Reactions.
"""
import logging
from typing import Optional, Iterable, Iterator, Any
import socket

from .signalTimestamp import Timestamp
from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalReaction import Reaction


class Reactions(object):
    """
    Class to store reactions to a message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: Optional[dict[str, Any]] = None,
                 reactions: Optional[Iterable[Reaction]] = None,
                 ) -> None:
        """
        Initialize a Reactions object.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The Device object for the device we're using.
        :param from_dict: Optional[dict[str, Any]]: The dict provided by __to_dict__().
        :param reactions: Optional[Iterable[Reaction]]: A list of reaction objects to store in the object.
        """
        # Super:
        super().__init__()

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__('config_path', 'str', config_path)
        if not isinstance(contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "Contacts", contacts)
        if not isinstance(groups, Groups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "Groups", groups)
        if not isinstance(devices, Devices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "Device", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if reactions is not None and not isinstance(reactions, Iterable):
            logger.critical("Raising TypeError:")
            __type_error__("reactions", "Optional[Iterable[Reaction]]", reactions)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to run commands on."""
        self._account_id: str = account_id
        """This accounts' ID."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._contacts: Contacts = contacts
        """This accounts' Contacts object."""
        self._groups: Groups = groups
        """This accounts' Groups object."""
        self._devices: Devices = devices
        """This accounts' Devices object."""
        self._this_device: Device = this_device
        """The Device object for the device we're currently using."""
        self._reactions: list[Reaction] = []
        """The list of reactions."""

        # Parse reactions parameter:
        if reactions is not None:
            for i, reaction in enumerate(reactions):
                if not isinstance(reaction, Reaction):
                    logger.critical("Raising TypeError:")
                    __type_error__("reactions[%i]" % i, "Reaction", reaction)
                self._reactions.append(reaction)
        return

    ############################
    # Overrides:
    ############################
    def __iter__(self) -> Iterator[Reaction]:
        """
        Iterate over the Reactions.
        :return: Iterator[Reaction]: The iterator.
        """
        return iter(self._reactions)

    def __len__(self) -> int:
        """
        The number of reactions.
        :return: int: The len of reactions.
        """
        return len(self._reactions)

    def __getitem__(self, index: int) -> Reaction:
        """
        Index reactions with square brackets.
        :param index: int: The index; Indexes as a list, raising IndexError if out of range.
        :return: Reaction: The reaction at the index.
        :raises IndexError: If the index is out of range.
        :raises TypeError: If the index isn't an int.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__getitem__.__name__)
        if not isinstance(index, int):
            logger.critical("Raising TypeError:")
            __type_error__("index", "int", index)
        return self._reactions[index]

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        reactions_dict: dict[str, Any] = {
            'reactions': []
        }
        for reaction in self._reactions:
            reactions_dict['reactions'].append(reaction.__to_dict__())
        return reactions_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        self._reactions = []
        for reaction_dict in from_dict['reactions']:
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                devices=self._devices, this_device=self._this_device, from_dict=reaction_dict
                                )
            self._reactions.append(reaction)
        return

    ####################
    # Methods:
    ####################
    def __parse__(self, reaction: Reaction) -> bool:
        """
        Parse a Reaction.
        :param reaction: Reaction: The Reaction object to parse.
        :return: bool: True = reaction parsed, False = reaction not parsed.
        :raises RuntimeError: If the reaction has already been parsed.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse__.__name__)
        # Type check reaction:
        if not isinstance(reaction, Reaction):
            logger.critical("Raising TypeError:")
            __type_error__('reaction', 'Reaction', reaction)
        # Check if the reaction already parsed:
        if reaction.is_parsed:
            error_message: str = "trying to parse a reaction that has already been parsed"
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Try to find a previous reaction:
        previous_reaction = self.get_by_sender(reaction.sender)
        # Parse a remove request:
        if reaction.is_remove:
            self.__remove_reaction__(reaction)
        # Add the reaction if no previous reaction:
        elif previous_reaction is None:
            self.__add_reaction__(reaction)
        # Otherwise, replace the existing reaction:
        else:
            reaction.is_change = True
            self.__replace_reaction__(previous_reaction, reaction)
        reaction.is_parsed = True
        return reaction.is_parsed

    def __add_reaction__(self, new_reaction: Reaction) -> None:
        """
        Add a new reaction to the reaction list.
        :param new_reaction: Reaction: The new reaction to add.
        :return: None
        :raises TypeError: If new_reaction is not of type Reaction.
        :raises RuntimeError: If the reaction is already in the list.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__add_reaction__.__name__)
        # Type check param:
        if not isinstance(new_reaction, Reaction):
            logger.critical("Raising TypeError:")
            __type_error__("new_reaction", "Reaction", new_reaction)
        # Search for reaction in the reactions, and if it exists, raise RuntimeError:
        if new_reaction in self._reactions:
            error_message: str = "reaction already in reactions."
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Add the reaction.
        self._reactions.append(new_reaction)
        return

    def __remove_reaction__(self, target_reaction: Reaction) -> None:
        """
        Remove a reaction from the reaction list.
        :param target_reaction: Reaction: The reaction to remove.
        :return: None
        :raises TypeError: If reaction is not a Reaction object.
        :raises RuntimeError: If the reaction is not in the list.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__remove_reaction__.__name__)
        # Type check param:
        if not isinstance(target_reaction, Reaction):
            logger.critical("Raising TypeError:")
            __type_error__("target_reaction", "Reaction", target_reaction)
        # Remove the reaction:
        try:
            self._reactions.remove(target_reaction)
        except ValueError:
            raise RuntimeError("target_reaction not found in reactions.")
        return

    def __replace_reaction__(self, old_reaction: Reaction, new_reaction: Reaction) -> None:
        """
        Replace a reaction with another.
        :param old_reaction: Reaction: The reaction to replace.
        :param new_reaction: Reaction: The reaction to replace with.
        :return: None:
        :raises RuntimeError: If old_reaction not in reaction list.
        :raises RuntimeError: If new_reaction already in reaction list.
        :raises TypeError: If either new_reaction or old_reaction is not of type Reaction.
        """
        self.__remove_reaction__(old_reaction)
        self.__add_reaction__(new_reaction)
        return

    def reaction_in(self, target_reaction: Reaction) -> bool:
        """
        Return True if a given reaction is in the reaction list.
        :param target_reaction: Reaction: Reaction to search for.
        :returns: bool: True if reaction in the reaction list.
        :raises TypeError: If target_reaction is not a reaction object.
        """
        if not isinstance(target_reaction, Reaction):
            __type_error__("target_reaction", "Reaction", target_reaction)
        return target_reaction in self._reactions

    ###########################
    # Getters:
    ###########################

    def get_by_sender(self, contact: Contact) -> Optional[Reaction]:
        """
        Get by sender contact
        :param: str: contact: The contact to search by.
        :returns: Optional[Reaction]: The Reaction found or None if not found.
        :raises TypeError if contact is not a Contact object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_sender.__name__)
        # Type check contact:
        if not isinstance(contact, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("contact", "Contact | str", contact)
        # Search for and return the reaction:
        for reaction in self._reactions:
            if reaction.sender == contact:
                return reaction
        # The Reaction was not found:
        return None

    def get_by_emoji(self, emoji: str) -> list[Reaction]:
        """
        Get by emoji
        :param: str: emoji: The emoji to search for.
        :returns: list[Reaction]: The reactions found; An list tuple if not found.
        :raises TypeError: If emoji is not a string.
        :raises
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_emoji.__name__)
        # Type check emoji:
        if not isinstance(emoji, str):
            logger.critical("Raising TypeError:")
            __type_error__("emoji", "str", emoji)
        # Value check emoji:
        if len(emoji) == 0 or len(emoji) > 4:
            raise ValueError("emoji must be one to 4 ascii characters")
        # Search for reactions:
        return [reaction for reaction in self._reactions if reaction.emoji == emoji]

    def get_by_recipient(self, recipient: Contact | Group) -> list[Reaction]:
        """
        Get by recipient
        :param: Contact | Group: The recipient to search for.
        :returns: list[Reaction]: The reactions found, or an empty list if not found.
        :raises: TypeError: If recipient is not a Contact object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_recipient.__name__)
        # Type check recipient:
        if not isinstance(recipient, Contact) and not isinstance(recipient, Group):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "Contact | Group", recipient)
        # Search for and return reactions:
        return [reaction for reaction in self._reactions if reaction.recipient == recipient]
