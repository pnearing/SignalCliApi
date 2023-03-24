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

global DEBUG
DEBUG: bool = True

Self = TypeVar("Self", bound="Reaction")

class Reaction(Message):
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
                 # sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 # device: Optional[Device] = None,
                 # timestamp: Optional[Timestamp] = None,
                 # is_delivered: bool = False,
                 # time_delivered: Optional[Timestamp] = None,
                 # is_read: bool = False,
                 # time_read: Optional[Timestamp] = None,
                 # is_viewed: bool = False,
                 # time_viewed: Optional[Timestamp] = None,
                 emoji: Optional[str] = None,
                 targetAuthor: Optional[Contact] = None,
                 targetTimestamp: Optional[Timestamp] = None,
                 isRemove: bool = False,
                 # isChange: bool = False,
                 # previousEmoji: Optional[str] = None,
                 ) -> None:
    # TODO: Argument checks:

    # Set external properties:
        self.emoji: str = emoji
        self.targetAuthor: Contact = targetAuthor
        self.targetTimestamp: Timestamp = targetTimestamp
        self.isRemove: bool = isRemove
        self.isChange: bool = False
        self.previousEmoji: Optional[str] = None
    # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, contacts.get_self(), recipient, this_device, None,
                         Message.TYPE_REACTION_MESSAGE)#, is_delivered, time_delivered, is_read, time_read, is_viewed, time_viewed)

    # Set body:
        self.__updateBody__()
        return

###############################
# Init:
###############################
    def __from_raw_message__(self, raw_message:dict) -> None:
        super().__from_raw_message__(raw_message)
        reactionDict:dict = raw_message['dataMessage']['reaction']
        # print(reactionDict)
        self.emoji = reactionDict['emoji']
        added, self.targetAuthor = self._contacts.__get_or_add__(
                                                                name="<UNKNOWN-CONTACT>",
                                                                number=reactionDict['targetAuthorNumber'],
                                                                uuid=reactionDict['targetAuthorUuid'],
                                                            )
        self.targetTimestamp = Timestamp(timestamp=reactionDict['targetSentTimestamp'])
        self.isRemove = reactionDict['isRemove']
        return
###############################
# Overrides:
###############################
    def __eq__(self, __o: Self) -> bool:
        if (isinstance(__o, Reaction) == True):
            if (self.sender == __o.sender and self.emoji == __o.emoji):
                return True
        return False
        
#####################
# To / From Dict:
#####################
    def __to_dict__(self) -> dict:
        reactionDict = super().__to_dict__()
        reactionDict['emoji'] = self.emoji
        reactionDict['targetAuthorId'] = None
        reactionDict['targetTimestamp'] = None
        reactionDict['isRemove'] = self.isRemove
        reactionDict['isChange'] = self.isChange
        reactionDict['previousEmoji'] = self.previousEmoji
        if (self.targetAuthor != None):
            reactionDict['targetAuthorId'] = self.targetAuthor.get_id()
        if (self.targetTimestamp != None):
            reactionDict['targetTimestamp'] = self.targetTimestamp.__toDict__()
        return reactionDict
    
    def __from_dict__(self, from_dict:dict) -> None:
        super().__from_dict__(from_dict)
    # Parse Emoji:
        self.emoji = from_dict['emoji']
    # Parse target author:
        if (from_dict['targetAuthorId'] != None):
            added, self.targetAuthor = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=from_dict['targetAuthorId'])
        else:
            self.targetAuthor = None
    # Parse target timestamp:
        if (from_dict['targetTimestamp'] != None):
            self.targetTimestamp = Timestamp(fromDict=from_dict['targetTimestamp'])
    # Parse is remove:
        self.isRemove = from_dict['isRemove']
    # Parse is change:
        self.isChange = from_dict['isChange']
    # Parse previous emoji:
        self.previousEmoji = from_dict['previousEmoji']
        return
###########################
# Send reaction:
###########################
    def send(self) -> tuple[bool, str]:
# Create reaction command object and json command string:
        sendReactionCommandObj = {
            "jsonrpc": "2.0",
            "contact_id": 10,
            "method": "sendReaction",
            "params": {
                "account": self._account_id,
                "emoji": self.emoji,
                "targetAuthor": self.targetAuthor.get_id(),
                "targetTimestamp": self.targetTimestamp.timestamp,
            }
        }
        if (self.recipient_type == 'contact'):
            sendReactionCommandObj['params']['recipient'] = self.sender.get_id()
        elif (self.recipient_type == 'group'):
            sendReactionCommandObj['params']['groupId'] = self.recipient.get_id()
        else:
            raise ValueError("recipent type = %s" % self.recipient_type)
        jsonCommandStr = json.dumps(sendReactionCommandObj) + '\n'
    # Communicate with signal:
        __socket_send__(self._command_socket, jsonCommandStr)
        responseStr = __socket_receive__(self._command_socket)
    # Parse response:
        responseObj:dict[str, object] = json.loads(responseStr)
        # print (responseObj)
    # Check for error:
        if ('error' in responseObj.keys()):
            if (DEBUG == True):
                errorMessage = "DEBUG: Signal error while sending reaction. Code: %i Message: %s" % (
                                                                                        responseObj['error']['code'],
                                                                                        responseObj['error']['message']
                                                                                    )
                print(errorMessage, file=sys.stderr)
            return (False, responseObj['error']['message'])
    # Response:
        resultObj: dict[str, object] = responseObj['result']
        self.timestamp = Timestamp(timestamp=resultObj['timestamp'])
    # Check for delivery error:
        if (resultObj['results'][0]['type'] != 'SUCCESS'):
            return (False, resultObj['results'][0]['type'])
        return (True, "SUCCESS")

    def remove(self) -> tuple[bool, str]:
        return
###########################
# Helpers:
###########################
    def __updateBody__(self) -> None:
        if (self.sender != None and self.recipient != None and self.targetTimestamp != None and self.targetAuthor != None and self.recipient_type!=None):
        # Removed reaction:
            if (self.isRemove == True):
                if (self.recipient_type == 'contact'):
                    self.body = "%s removed the reaction %s from %s's message %i." % ( 
                                                                                    self.sender.get_display_name(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp
                                                                                )
                elif (self.recipient_type == 'group'):
                    self.body = "%s removed the reaction %s from %s's message %i in group %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.get_display_name()
                                                                                )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)
        # Changed reaction:
            elif(self.isChange == True):
                if (self.recipient_type == 'contact'):
                    self.body = "%s changed their reaction to %s's message %i, from %s to %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                elif (self.recipient_type == 'group'):
                    self.body = "%s changed their reaction to %s's message %i in group %s, from %s to %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.get_display_name(),
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)
            else:
            # Added new reaction:
                if (self.recipient_type == 'contact'):
                    self.body = "%s reacted to %s's message with %s" % (
                                                                            self.sender.get_display_name(),
                                                                            self.targetAuthor.get_display_name(),
                                                                            self.emoji
                                                                        )
                elif (self.recipient_type == 'group'):
                    self.body = "%s reacted to %s's message %i in group %s with %s" % (
                                                                            self.sender.get_display_name(),
                                                                            self.targetAuthor.get_display_name(),
                                                                            self.targetTimestamp.timestamp,
                                                                            self.recipient.get_display_name(),
                                                                            self.emoji
                                                                        )
                else:
                    raise ValueError("recipient_type invalid value: %s" % self.recipient_type)
            
        else:
            self.body = 'Invalid reaction.'
        return