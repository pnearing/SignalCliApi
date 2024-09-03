#! /usr/bin/env python3
"""
File: signal_reactions.py
Store and manage a list of SignalReactions.
"""
# pylint: disable=R0902, R0913, W0511
import logging
from typing import Optional, Iterator, Any
import socket

# from .signal_timestamp import SignalTimestamp
from .signal_common import __type_error__
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_reaction import SignalReaction


class SignalReactions:
    """
    Class to store reactions to a message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 this_device: SignalDevice,
                 from_dict: Optional[dict[str, Any]] = None,
                 ) -> None:
        """
        Initialize a SignalReactions object.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object for the device we're using.
        :param from_dict: Optional[dict[str, Any]]: The dict provided by __to_dict__().
        """
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
        if not isinstance(contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "SignalContacts", contacts)
        if not isinstance(groups, SignalGroups):
            logger.critical("Raising TypeError:")
            __type_error__("groups", "SignalGroups", groups)
        if not isinstance(devices, SignalDevices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "SignalDevices", devices)
        if not isinstance(this_device, SignalDevice):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "SignalDevice", this_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to run commands on."""
        self._account_id: str = account_id
        """This accounts' ID."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._contacts: SignalContacts = contacts
        """This accounts' SignalContacts object."""
        self._groups: SignalGroups = groups
        """This accounts' SignalGroups object."""
        self._devices: SignalDevices = devices
        """This accounts' SignalDevices object."""
        self._this_device: SignalDevice = this_device
        """The SignalDevice object for the device we're currently using."""
        self._reactions: list[SignalReaction] = []
        """The list of reactions."""

        if from_dict is not None:
            self.__from_dict__(from_dict)

    ############################
    # Overrides:
    ############################
    def __iter__(self) -> Iterator[SignalReaction]:
        """
        Iterate over the SignalReactions.
        :return: Iterator[SignalReaction]: The iterator.
        """
        return iter(self._reactions)

    def __len__(self) -> int:
        """
        The number of reactions.
        :return: int: The len of reactions.
        """
        return len(self._reactions)

    def __getitem__(self, index: int) -> SignalReaction:
        """
        Index reactions with square brackets.
        :param index: int: The index; Indexes as a list, raising IndexError if out of range.
        :return: SignalReaction: The reaction at the index.
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
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__to_dict__.__name__)
        reactions_dict: dict[str, Any] = {
            'reactions': []
        }

        for reaction in self._reactions:
            reactions_dict['reactions'].append(reaction.__to_dict__())
        logger.debug("Saved %i reactions to the dict.", len(reactions_dict['reactions']))
        return reactions_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)
        logger.debug("Entered")
        self._reactions = []
        for reaction_dict in from_dict['reactions']:
            reaction = SignalReaction(command_socket=self._command_socket,
                                      account_id=self._account_id, config_path=self._config_path,
                                      contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      from_dict=reaction_dict )
            self._reactions.append(reaction)
        logger.debug("Loaded %i reactions.", len(self._reactions))

    ####################
    # Methods:
    ####################
    def __parse__(self, reaction: SignalReaction) -> bool:
        """
        Parse a SignalReaction.
        :param reaction: SignalReaction: The SignalReaction object to parse.
        :return: bool: True = reaction parsed, False = reaction not parsed.
        :raises RuntimeError: If the reaction has already been parsed.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse__.__name__)
        # Type check reaction:
        if not isinstance(reaction, SignalReaction):
            logger.critical("Raising TypeError:")
            __type_error__('reaction', 'SignalReaction', reaction)
        # Check if the reaction already parsed:
        if reaction.is_parsed:
            error_message: str = "trying to parse a reaction that has already been parsed"
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)
        # Try to find a previous reaction:
        previous_reaction = self.get_by_sender(reaction.sender)
        # Parse a remove request:
        if reaction.is_remove:
            self.__remove_reaction__(reaction)
            reaction.is_parsed = True
        # Add the reaction if no previous reaction:
        elif previous_reaction is None:
            self.__add_reaction__(reaction)
            reaction.is_parsed = True
        # Otherwise, replace the existing reaction:
        else:
            reaction.is_change = True
            reaction.previous_emoji = previous_reaction.emoji
            self.__replace_reaction__(previous_reaction, reaction)
            reaction.is_parsed = True
        return reaction.is_parsed

    def __add_reaction__(self, new_reaction: SignalReaction) -> None:
        """
        Add a new reaction to the reaction list.
        :param new_reaction: SignalReaction: The new reaction to add.
        :return: None
        :raises TypeError: If new_reaction is not of type SignalReaction.
        :raises RuntimeError: If the reaction is already in the list.
        """
        # TODO: Rewrite this.
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__add_reaction__.__name__)
        logger.debug("Entered.")
        # Type check param:
        if not isinstance(new_reaction, SignalReaction):
            logger.critical("Raising TypeError:")
            __type_error__("new_reaction", "SignalReaction", new_reaction)
        # Search for reaction in the reactions, and if it exists, raise RuntimeError:
        reaction_found: bool = False
        for reaction in self._reactions:
            logger.debug("new_reaction: %s", str(new_reaction.__to_dict__()))
            logger.debug("old_reaction: %s", str(reaction.__to_dict__()))
            if reaction == new_reaction:
                logger.debug("Reaction found.")
                reaction_found = True
        if not reaction_found:
            logger.debug("Reaction not found, adding.")
            self._reactions.append(new_reaction)
            new_reaction.is_parsed = True
        # if new_reaction not in self._reactions:
        #     self._reactions.append(new_reaction)

    def __remove_reaction__(self, target_reaction: SignalReaction) -> None:
        """
        Remove a reaction from the reaction list.
        :param target_reaction: SignalReaction: The reaction to remove.
        :return: None
        :raises TypeError: If reaction is not a SignalReaction object.
        :raises RuntimeError: If the reaction is not in the list.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__remove_reaction__.__name__)
        # Type check param:
        if not isinstance(target_reaction, SignalReaction):
            logger.critical("Raising TypeError:")
            __type_error__("target_reaction", "SignalReaction", target_reaction)
        # Remove the reaction:
        try:
            self._reactions.remove(target_reaction)
        except ValueError as e:
            raise RuntimeError("target_reaction not found in reactions.") from e

    def __replace_reaction__(self,
                             old_reaction: SignalReaction,
                             new_reaction: SignalReaction
                             ) -> None:
        """
        Replace a reaction with another.
        :param old_reaction: SignalReaction: The reaction to replace.
        :param new_reaction: SignalReaction: The reaction to replace with.
        :return: None:
        :raises RuntimeError: If old_reaction not in reaction list.
        :raises RuntimeError: If new_reaction already in reaction list.
        :raises TypeError: If either new_reaction or old_reaction is not of type SignalReaction.
        """
        self.__remove_reaction__(old_reaction)
        self.__add_reaction__(new_reaction)

    def reaction_in(self, target_reaction: SignalReaction) -> bool:
        """
        Return True if a given reaction is in the reaction list.
        :param target_reaction: SignalReaction: SignalReaction to search for.
        :returns: bool: True if reaction in the reaction list.
        :raises TypeError: If target_reaction is not a reaction object.
        """
        if not isinstance(target_reaction, SignalReaction):
            __type_error__("target_reaction", "SignalReaction", target_reaction)
        return target_reaction in self._reactions

    ###########################
    # Getters:
    ###########################

    def get_by_sender(self, contact: SignalContact) -> Optional[SignalReaction]:
        """
        Get by sender contact
        :param: str: contact: The contact to search by.
        :returns: Optional[SignalReaction]: The SignalReaction found or None if not found.
        :raises TypeError if contact is not a SignalContact object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_sender.__name__)
        # Type check contact:
        if not isinstance(contact, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("contact", "SignalContact | str", contact)
        # Search for and return the reaction:
        for reaction in self._reactions:
            if reaction.sender == contact:
                return reaction
        # The Reaction was not found:
        return None

    def get_by_emoji(self, emoji: str) -> list[SignalReaction]:
        """
        Get by emoji
        :param: str: emoji: The emoji to search for.
        :returns: list[SignalReaction]: The reactions found; An list tuple if not found.
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

    def get_by_recipient(self, recipient: SignalContact | SignalGroup) -> list[SignalReaction]:
        """
        Get by recipient
        :param: SignalContact | SignalGroup: The recipient to search for.
        :returns: list[SignalReaction]: The reactions found, or an empty list if not found.
        :raises: TypeError: If recipient is not a SignalContact object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_recipient.__name__)
        # Type check recipient:
        if not isinstance(recipient, SignalContact) and not isinstance(recipient, SignalGroup):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "SignalContact | SignalGroup", recipient)
        # Search for and return reactions:
        return [reaction for reaction in self._reactions if reaction.recipient == recipient]
