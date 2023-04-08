#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalTimestamp import Timestamp

DEBUG: bool = False

Self = TypeVar("Self", bound="Reaction")


class Reaction(Message):
    """Class to store a reaction message."""
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 recipient: Optional[Contact | Group] = None,
                 emoji: Optional[str] = None,
                 target_author: Optional[Contact] = None,
                 target_timestamp: Optional[Timestamp] = None,
                 is_remove: bool = False,
                 ) -> None:
        # Argument checks:
        if not isinstance(emoji, str):
            __type_error__("emoji", "str", emoji)
        if emoji is not None and not isinstance(emoji, str):
            __type_error__("emoji", 'str', emoji)
        if target_author is not None and not isinstance(target_author, Contact):
            __type_error__("target_author", "Contact", target_author)
        if target_timestamp is not None and not isinstance(target_timestamp, Timestamp):
            __type_error__("target_timestamp", "Timestamp", target_timestamp)
        if not isinstance(is_remove, bool):
            __type_error__("is_remove", 'bool', is_remove)
        # Set external properties:
        self.emoji: str = emoji
        self.target_author: Contact = target_author
        self.target_timestamp: Timestamp = target_timestamp
        self.is_remove: bool = is_remove
        self.is_change: bool = False
        self.previous_emoji: Optional[str] = None
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, contacts.get_self(), recipient, this_device, None, Message.TYPE_REACTION_MESSAGE)

        # Set body:
        self.__update_body__()
        return

    ###############################
    # Init:
    ###############################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        reactionDict: dict = raw_message['dataMessage']['reaction']
        # print(reactionDict)
        self.emoji = reactionDict['emoji']
        added, self.target_author = self._contacts.__get_or_add__(
            name="<UNKNOWN-CONTACT>",
            number=reactionDict['targetAuthorNumber'],
            uuid=reactionDict['targetAuthorUuid'],
        )
        self.target_timestamp = Timestamp(timestamp=reactionDict['targetSentTimestamp'])
        self.is_remove = reactionDict['isRemove']
        return

    ###############################
    # Overrides:
    ###############################
    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Reaction):
            if self.sender == __o.sender and self.emoji == __o.emoji:
                return True
        return False

    #####################
    # To / From Dict:
    #####################
    def __to_dict__(self) -> dict:
        reaction_dict = super().__to_dict__()
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

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Parse Emoji:
        self.emoji = from_dict['emoji']
        # Parse target author:
        if from_dict['targetAuthorId'] is not None:
            added, self.target_author = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                      contact_id=from_dict['targetAuthorId'])
        else:
            self.target_author = None
        # Parse target timestamp:
        if from_dict['targetTimestamp'] is not None:
            self.target_timestamp = Timestamp(from_dict=from_dict['targetTimestamp'])
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
        :returns: tuple[bool, str]: True/False for sent status, string for error message if False, or "SUCCESS" if True.
        """
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
        if self.recipient_type == 'contact':
            send_reaction_command_obj['params']['recipient'] = self.sender.get_id()
        elif self.recipient_type == 'group':
            send_reaction_command_obj['params']['groupId'] = self.recipient.get_id()
        else:
            raise ValueError("recipient type = %s" % self.recipient_type)
        json_command_str = json.dumps(send_reaction_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str = __socket_receive__(self._command_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # print (responseObj)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                errorMessage = "DEBUG: Signal error while sending reaction. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(errorMessage, file=sys.stderr)
            return False, response_obj['error']['message']
        # Response:
        resultObj: dict[str, object] = response_obj['result']
        self.timestamp = Timestamp(timestamp=resultObj['timestamp'])
        # Check for delivery error:
        if resultObj['results'][0]['type'] != 'SUCCESS':
            return False, resultObj['results'][0]['type']
        return True, "SUCCESS"

    def remove(self) -> tuple[bool, str]:
        # TODO: remove a reaction.
        return

    ###########################
    # Helpers:
    ###########################
    def __update_body__(self) -> None:
        if (
                self.sender is not None and self.recipient is not None and self.target_timestamp is not None
                and self.target_author is not None and self.recipient_type is not None):
            # Removed reaction:
            if self.is_remove:
                if self.recipient_type == 'contact':
                    self.body = "%s removed the reaction %s from %s's message %i." % (
                        self.sender.get_display_name(),
                        self.emoji,
                        self.target_author.get_display_name(),
                        self.target_timestamp.timestamp
                    )
                elif self.recipient_type == 'group':
                    self.body = "%s removed the reaction %s from %s's message %i in group %s" % (
                        self.sender.get_display_name(),
                        self.emoji,
                        self.target_author.get_display_name(),
                        self.target_timestamp.timestamp,
                        self.recipient.get_display_name()
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)
            # Changed reaction:
            elif self.is_change:
                if self.recipient_type == 'contact':
                    self.body = "%s changed their reaction to %s's message %i, from %s to %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp.timestamp,
                        self.previous_emoji,
                        self.emoji
                    )
                elif self.recipient_type == 'group':
                    self.body = "%s changed their reaction to %s's message %i in group %s, from %s to %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp.timestamp,
                        self.recipient.get_display_name(),
                        self.previous_emoji,
                        self.emoji
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)
            else:
                # Added new reaction:
                if self.recipient_type == 'contact':
                    self.body = "%s reacted to %s's message with %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.emoji
                    )
                elif self.recipient_type == 'group':
                    self.body = "%s reacted to %s's message %i in group %s with %s" % (
                        self.sender.get_display_name(),
                        self.target_author.get_display_name(),
                        self.target_timestamp.timestamp,
                        self.recipient.get_display_name(),
                        self.emoji
                    )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)

        else:
            self.body = 'Invalid reaction.'
        return
