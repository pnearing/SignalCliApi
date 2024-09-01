#!/usr/bin/env python3
"""
File: signalReaction.py
Store and handle a reaction to a message.
"""
import logging
from typing import TypeVar, Optional, Any
import socket
import json

from .signalCommon import __type_error__, __socket_receive_blocking__, __socket_send__, MessageTypes, RecipientTypes, \
    __parse_signal_response__, __check_response_for_error__
from .signalContact import SignalContact
from .signalContacts import SignalContacts
from .signalDevice import SignalDevice
from .signalDevices import SignalDevices
from .signalGroup import SignalGroup
from .signalGroups import SignalGroups
from .signalMessage import SignalMessage
from .signalTimestamp import SignalTimestamp

Self = TypeVar("Self", bound="SignalReaction")


class SignalReaction(SignalMessage):
    """
    Class to store a reaction message.
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
                 raw_message: Optional[dict[str, Any]] = None,
                 sync_message: Optional[dict[str, Any]] = None,
                 recipient: Optional[SignalContact | SignalGroup] = None,
                 emoji: Optional[str] = None,
                 target_author: Optional[SignalContact] = None,
                 target_timestamp: Optional[SignalTimestamp] = None,
                 is_remove: bool = False,
                 ) -> None:
        """
        Initialize a reaction message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This account's ID.
        :param config_path: str: The full path to signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object for the device we're currently on.
        :param from_dict: Optional[dict[str, Any]]: Load properties from a dict provided by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: Load properties from a dict provided by signal.
        :param sync_message: Optional[dict[str, Any]]: Load properties from a dict provided by the sync message.
        :param recipient: Optional[SignalContact | SignalGroup]: The recipient of this reaction message.
        :param emoji: Optional[str]: The unicode emoji.
        :param target_author: Optional[SignalContact]: The author of the message reacted to.
        :param target_timestamp: Optional[SignalTimestamp]: The timestamp of the message reacted to.
        :param is_remove: bool: If True, this is a removal message.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument type checks:
        if emoji is not None and not isinstance(emoji, str):
            logger.critical("Raising TypeError:")
            __type_error__("emoji", 'Optional[str]', emoji)
        if target_author is not None and not isinstance(target_author, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("target_author", "Optional[SignalContact]", target_author)
        if target_timestamp is not None and not isinstance(target_timestamp, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("target_timestamp", "Optional[SignalTimestamp]", target_timestamp)
        if not isinstance(is_remove, bool):
            logger.critical("Raising TypeError:")
            __type_error__("is_remove", 'bool', is_remove)

        # Set internal properties:
        self._has_been_removed: bool = False
        """Has the removal message been sent for this message."""
        self._is_change: bool = False  # GETTER / SETTERS ADDED AT END OF FILE
        """Is this a change message?"""

        # Set external properties:
        self.emoji: Optional[str] = emoji
        """The emoji that was reacted with."""
        self.target_author: Optional[SignalContact] = target_author
        """The SignalContact object of the author of the message that was reacted to."""
        self.target_timestamp: Optional[SignalTimestamp] = target_timestamp
        """The SignalTimestamp object of the message that was reacted to."""
        self.is_remove: bool = is_remove
        """Is this a removal message?"""
        self.previous_emoji: Optional[str] = None
        """The previous emoji if this is a change message."""
        self.is_parsed: bool = False
        """Has this reaction been parsed?"""

        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, contacts.get_self(), recipient, this_device, None, MessageTypes.REACTION)
        if sync_message is not None:
            self.__from_sync_message__(sync_message)
        # Set body:
        self.__update_body__()
        now = SignalTimestamp(now=True)
        super().mark_delivered(now)
        super().mark_read(now)
        super().mark_viewed(now)
        return

    ###############################
    # Init:
    ###############################
    def __from_sync_message__(self, sync_message: dict[str, Any]) -> None:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_sync_message__.__name__)
        logger.debug(sync_message)
        super().__from_raw_message__(sync_message)
        reaction_dict: dict[str, Any] = sync_message['syncMessage']['sentMessage']['reaction']
        self.emoji = reaction_dict['emoji']
        _, self.target_author = self._contacts.__get_or_add__(number=reaction_dict['targetAuthorNumber'],
                                                              uuid = reaction_dict['targetAuthorUuid'])
        self.target_timestamp = SignalTimestamp(timestamp=reaction_dict['targetSentTimestamp'])
        self.is_remove = reaction_dict['isRemove']
        return

    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load reaction properties from a dict provided by signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        super().__from_raw_message__(raw_message)
        reaction_dict: dict[str, Any] = raw_message['dataMessage']['reaction']
        # print(reactionDict)
        self.emoji = reaction_dict['emoji']
        _, self.target_author = self._contacts.__get_or_add__(number=reaction_dict['targetAuthorNumber'],
                                                              uuid=reaction_dict['targetAuthorUuid'])
        self.target_timestamp = SignalTimestamp(timestamp=reaction_dict['targetSentTimestamp'])
        self.is_remove = reaction_dict['isRemove']
        return

    ###############################
    # Overrides:
    ###############################
    def __eq__(self, other: Self) -> bool:
        """
        Compare equality.
        :param other: SignalReaction: The reaction to compare with.
        :return: bool
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + '__eq__')
        logger.debug("__eq__ entered.")
        if isinstance(other, SignalReaction):
            logger.debug("Instance match.")
            if self.sender == other.sender:
                logger.debug("Sender match.")
                if self.target_author == other.target_author:
                    logger.debug("Author match.")
                    if self.target_timestamp == other.target_timestamp:
                        logger.debug("timestamp match.")
                        if self.emoji == other.emoji:
                            logger.debug('Emoji match, return True.')
                            return True
        logger.debug("Returning False")
        return False

    #####################
    # To / From Dict:
    #####################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this reaction.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        reaction_dict: dict[str, Any] = super().__to_dict__()
        reaction_dict['emoji'] = self.emoji
        reaction_dict['targetAuthorId'] = None
        reaction_dict['targetTimestamp'] = None
        reaction_dict['isRemove'] = self.is_remove
        reaction_dict['isChange'] = self.is_change
        reaction_dict['previousEmoji'] = self.previous_emoji
        if self.target_author is not None:
            reaction_dict['targetAuthorId'] = self.target_author.get_id()
        if self.target_timestamp is not None:
            reaction_dict['targetTimestamp'] = self.target_timestamp.__to_dict__()
        return reaction_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        super().__from_dict__(from_dict)
        # Parse Emoji:
        self.emoji = from_dict['emoji']
        # Parse target author:
        if from_dict['targetAuthorId'] is not None:
            _, self.target_author = self._contacts.__get_or_add__(contact_id=from_dict['targetAuthorId'])
        else:
            self.target_author = None
        # Parse target timestamp:
        if from_dict['targetTimestamp'] is not None:
            self.target_timestamp = SignalTimestamp(from_dict=from_dict['targetTimestamp'])
        # Parse is remove:
        self.is_remove = from_dict['isRemove']
        # Parse is change:
        self.is_change = from_dict['isChange']
        # Parse previous emoji:
        self.previous_emoji = from_dict['previousEmoji']
        return

    ###########################
    # Send reaction:
    ###########################
    def send(self) -> tuple[bool, str]:
        """
        Send the reaction.
        :returns: tuple[bool, str]: True/False for sent status, string for an error message if False, or "SUCCESS"
            if True.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.send.__name__)

        # Check if this was already sent.
        if self.is_sent:
            error_message: str = "reaction already sent."
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)

        # Create reaction command object and json command string:
        send_reaction_command_obj = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "sendReaction",
            "params": {
                "account": self._account_id,
                "emoji": self.emoji,
                "targetAuthor": self.target_author.get_id(),
                "targetTimestamp": self.target_timestamp.timestamp,
            }
        }
        # Add recipient to the message:
        if self.recipient_type == RecipientTypes.CONTACT:
            send_reaction_command_obj['params']['recipient'] = self.sender.get_id()
        elif self.recipient_type == RecipientTypes.GROUP:
            send_reaction_command_obj['params']['groupId'] = self.recipient.get_id()
        else:
            raise ValueError("recipient type = %s" % str(self.recipient_type))

        # Create the JSON command string:
        json_command_str: str = json.dumps(send_reaction_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._command_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, error_code, error_message = __check_response_for_error__(response_obj, [])
        if error_occurred:
            error_message: str = "signal error while sending reaction. Code: %i, Message: %s" \
                                 % (error_code, error_message)
            return False, error_message

        # Parse Response:
        result_obj: dict[str, Any] = response_obj['result']
        self.timestamp = SignalTimestamp(timestamp=result_obj['timestamp'])
        # Check for delivery error:
        if result_obj['results'][0]['type'] != 'SUCCESS':
            return False, result_obj['results'][0]['type']
        return True, "SUCCESS"

    def remove(self) -> tuple[bool, str]:
        """
        Remove a reaction.
        :return: tuple[bool, str]: The first element is a boolean indicating success or failure; The second element is
            a string, either 'SUCCESS' on success, or an error message on failure.
        """
        # TODO: remove a reaction in signal.
        if self._has_been_removed:
            return False, "already removed"
        self._has_been_removed = True
        return False, "NOT-IMPLEMENTED"

    ###########################
    # Helpers:
    ###########################
    def __update_body__(self) -> None:
        if (self.sender is not None and self.recipient is not None and self.target_timestamp is not None
                and self.target_author is not None and self.recipient_type is not None):
            # Removed reaction:
            if self.is_remove:
                if self.recipient_type == RecipientTypes.CONTACT:
                    self.body = "%s removed the reaction %s from %s's message %i." % (
                        self.sender.get_display_name(),
                        self.emoji,
                        self.target_author.get_display_name(),
                        self.target_timestamp._timestamp
                    )
                elif self.recipient_type == RecipientTypes.GROUP:
                    self.body = "%s removed the reaction %s from %s's message %i in group %s" % (
                        self.sender.get_display_name(),
                        self.emoji,
                        self.target_author.get_display_name(),
                        self.target_timestamp._timestamp,
                        self.recipient.get_display_name()
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % str(self.recipient_type))
            # Changed reaction:
            elif self.is_change:
                if self.recipient_type == RecipientTypes.CONTACT:
                    self.body = "%s changed their reaction to %s's message %i, from %s to %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp._timestamp,
                        self.previous_emoji,
                        self.emoji
                    )
                elif self.recipient_type == RecipientTypes.GROUP:
                    self.body = "%s changed their reaction to %s's message %i in group %s, from %s to %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp._timestamp,
                        self.recipient.get_display_name(),
                        self.previous_emoji,
                        self.emoji
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % str(self.recipient_type))
            else:
                # Added new reaction:
                if self.recipient_type == RecipientTypes.CONTACT:
                    self.body = "%s reacted to %s's message with %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.emoji
                    )
                elif self.recipient_type == RecipientTypes.GROUP:
                    self.body = "%s reacted to %s's message %i in group %s with %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp._timestamp,
                        self.recipient.get_display_name(),
                        self.emoji
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % str(self.recipient_type))

        else:
            self.body = 'Invalid reaction.'
        return

    ###############################
    # Properties:
    ###############################
    @property
    def is_change(self) -> bool:
        """
        Is this a change reaction?
        Getter.
        :return: bool: True, this is a change message, False, it is not.
        """
        return self._is_change

    @is_change.setter
    def is_change(self, value) -> None:
        """
        Is this a change reaction?
        Setter.
        :param value: bool: The value to set to.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + 'is_change_setter()')
        # Type check value:
        if not isinstance(value, bool):
            logger.critical("Raising TypeError:")
            __type_error__('value', 'bool', value)
        old_value: bool = self._is_change
        self._is_change = value
        if old_value != value:
            self.__update_body__()
        return

    @property
    def is_sent(self) -> bool:
        """
        Is this reaction already sent?
        :return: bool: True the reaction has been sent, False it has not.
        """
        return self.timestamp is not None  # If we have a timestamp, then the reaction was sent.

