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
                    commandSocket: socket.socket,
                    accountId: str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    fromDict: Optional[dict] = None,
                    rawMessage: Optional[dict] = None,
                    # sender: Optional[Contact] = None,
                    recipient: Optional[Contact | Group] = None,
                    # device: Optional[Device] = None,
                    # timestamp: Optional[Timestamp] = None,
                    # isDelivered: bool = False,
                    # timeDelivered: Optional[Timestamp] = None,
                    # isRead: bool = False,
                    # timeRead: Optional[Timestamp] = None,
                    # isViewed: bool = False,
                    # timeViewed: Optional[Timestamp] = None,
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
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                         rawMessage, contacts.get_self(), recipient, thisDevice, None,
                         Message.TYPE_REACTION_MESSAGE)#, isDelivered, timeDelivered, isRead, timeRead, isViewed, timeViewed)

    # Set body:
        self.__updateBody__()
        return

###############################
# Init:
###############################
    def __fromRawMessage__(self, rawMessage:dict) -> None:
        super().__fromRawMessage__(rawMessage)
        reactionDict:dict = rawMessage['dataMessage']['reaction']
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
    def __toDict__(self) -> dict:
        reactionDict = super().__toDict__()
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
    
    def __fromDict__(self, fromDict:dict) -> None:
        super().__fromDict__(fromDict)
    # Parse Emoji:
        self.emoji = fromDict['emoji']
    # Parse target author:
        if (fromDict['targetAuthorId'] != None):
            added, self.targetAuthor = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id=fromDict['targetAuthorId'])
        else:
            self.targetAuthor = None
    # Parse target timestamp:
        if (fromDict['targetTimestamp'] != None):
            self.targetTimestamp = Timestamp(fromDict=fromDict['targetTimestamp'])
    # Parse is remove:
        self.isRemove = fromDict['isRemove']
    # Parse is change:
        self.isChange = fromDict['isChange']
    # Parse previous emoji:
        self.previousEmoji = fromDict['previousEmoji']
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
                "account": self._accountId,
                "emoji": self.emoji,
                "targetAuthor": self.targetAuthor.get_id(),
                "targetTimestamp": self.targetTimestamp.timestamp,
            }
        }
        if (self.recipientType == 'contact'):
            sendReactionCommandObj['params']['recipient'] = self.sender.get_id()
        elif (self.recipientType == 'group'):
            sendReactionCommandObj['params']['groupId'] = self.recipient.get_id()
        else:
            raise ValueError("recipent type = %s" % self.recipientType)
        jsonCommandStr = json.dumps(sendReactionCommandObj) + '\n'
    # Communicate with signal:
        __socket_send__(self._commandSocket, jsonCommandStr)
        responseStr = __socket_receive__(self._commandSocket)
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
        if (self.sender != None and self.recipient != None and self.targetTimestamp != None and self.targetAuthor != None and self.recipientType!=None):
        # Removed reaction:
            if (self.isRemove == True):
                if (self.recipientType == 'contact'):
                    self.body = "%s removed the reaction %s from %s's message %i." % ( 
                                                                                    self.sender.get_display_name(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp
                                                                                )
                elif (self.recipientType == 'group'):
                    self.body = "%s removed the reaction %s from %s's message %i in group %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.get_display_name()
                                                                                )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
        # Changed reaction:
            elif(self.isChange == True):
                if (self.recipientType == 'contact'):
                    self.body = "%s changed their reaction to %s's message %i, from %s to %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                elif (self.recipientType == 'group'):
                    self.body = "%s changed their reaction to %s's message %i in group %s, from %s to %s" % (
                                                                                    self.sender.get_display_name(),
                                                                                    self.targetAuthor.get_display_name(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.get_display_name(),
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
            else:
            # Added new reaction:
                if (self.recipientType == 'contact'):
                    self.body = "%s reacted to %s's message with %s" % (
                                                                            self.sender.get_display_name(),
                                                                            self.targetAuthor.get_display_name(),
                                                                            self.emoji
                                                                        )
                elif (self.recipientType == 'group'):
                    self.body = "%s reacted to %s's message %i in group %s with %s" % (
                                                                            self.sender.get_display_name(),
                                                                            self.targetAuthor.get_display_name(),
                                                                            self.targetTimestamp.timestamp,
                                                                            self.recipient.get_display_name(),
                                                                            self.emoji
                                                                        )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
            
        else:
            self.body = 'Invalid reaction.'
        return