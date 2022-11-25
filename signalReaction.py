#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket
import json
import sys

from signalCommon import __typeError__, __socketReceive__, __socketSend__
from signalContact import Contact
from signalContacts import Contacts
from signalDevice import Device
from signalDevices import Devices
from signalGroup import Group
from signalGroups import Groups
from signalMessage import Message
from signalTimestamp import Timestamp

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
                    previousEmoji: Optional[str] = None,
                ) -> None:
    # TODO: Argument checks:

    # Set external properties:
        self.emoji: str = emoji
        self.targetAuthor: Contact = targetAuthor
        self.targetTimestamp: Timestamp = targetTimestamp
        self.isRemove: bool = isRemove
        self.isChange: bool = False
        self.previousEmoji: str = previousEmoji
    # Run super init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, contacts.getSelf(), recipient, self._thisDevice, None,
                            Message.TYPE_REACTION_MESSAGE)#, isDelivered, timeDelivered, isRead, timeRead, isViewed, timeViewed)

    # Set body:
        self.__updateBody__()
        return

###############################
# Init:
###############################
    def __fromRawMessage__(self, rawMessage:dict) -> None:
        super().__fromRawMessage__(rawMessage)
        added, self.sender = self._contacts.__getOrAdd__(rawMessage['sourceName'], rawMessage['source'])
        if ('groupInfo' in rawMessage['dataMessage'].keys()):
            added, group = self._groups.__getOrAdd__("<UNKNOWN-GROUP>", rawMessage['dataMessage']['groupInfo']['groupId'])
            self.recipient = group
            self.recipientType = 'group'
        else:
            self.recipient = self._contacts.getSelf()
            self.recipientType = 'contact'
        added, self.device = self.sender.devices.__getOrAdd__("<UNKNOWN-DEVICE>", rawMessage['sourceDevice'])
        self.timestamp = Timestamp(timestamp=rawMessage['timestamp'])
        reactionDict:dict = rawMessage['dataMessage']['reaction']
        self.emoji = reactionDict['emoji']
        added, self.targetAuthor = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", reactionDict['targetAuthor'])
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
            reactionDict['targetAuthorId'] = self.targetAuthor.getId()
        if (self.targetTimestamp != None):
            reactionDict['targetTimestamp'] = self.targetTimestamp.__toDict__()
        return reactionDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        super().__fromDict__(fromDict)
    # Parse Emoji:
        self.emoji = fromDict['emoji']
    # Parse target author:
        if (fromDict['targetAuthorId'] != None):
            added, self.targetAuthor = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", fromDict['targetAuthorId'])
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
            "id": 10,
            "method": "sendReaction",
            "params": {
                "account": self._accountId,
                "emoji": self.emoji,
                "targetAuthor": self.targetAuthor.getId(),
                "targetTimestamp": self.targetTimestamp.timestamp,
            }
        }
        if (self.recipientType == 'contact'):
            sendReactionCommandObj['params']['recipient'] = self.sender.getId()
        elif (self.recipientType == 'group'):
            sendReactionCommandObj['params']['groupId'] = self.recipient.getId()
        else:
            raise ValueError("recipent type = %s" % self.recipientType)
        jsonCommandStr = json.dumps(sendReactionCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._commandSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._commandSocket)
    # Parse response:
        responseObj:dict[str, object] = json.loads(responseStr)
        print (responseObj)
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
                                                                                    self.sender.getDisplayName(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.getDisplayName(),
                                                                                    self.targetTimestamp.timestamp
                                                                                )
                elif (self.recipientType == 'group'):
                    self.body = "%s removed the reaction %s from %s's message %i in group %s" % (
                                                                                    self.sender.getDisplayName(),
                                                                                    self.emoji,
                                                                                    self.targetAuthor.getDisplayName(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.getDisplayName()
                                                                                )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
        # Changed reaction:
            elif(self.isChange == True):
                if (self.recipientType == 'contact'):
                    self.body = "%s changed their reaction to %s's message %i, from %s to %s" % (
                                                                                    self.sender.getDisplayName(),
                                                                                    self.targetAuthor.getDisplayName(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                elif (self.recipientType == 'group'):
                    self.body = "%s changed their reaction to %s's message %i in group %s, from %s to %s" % (
                                                                                    self.sender.getDisplayName(),
                                                                                    self.targetAuthor.getDisplayName(),
                                                                                    self.targetTimestamp.timestamp,
                                                                                    self.recipient.getDisplayName(),
                                                                                    self.previousEmoji,
                                                                                    self.emoji
                                                                                )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
            else:
            # Added new reaction:
                if (self.recipientType == 'contact'):
                    self.body = "%s reacted to %s's message with %s" % (
                                                                            self.sender.getDisplayName(),
                                                                            self.targetAuthor.getDisplayName(),
                                                                            self.emoji
                                                                        )
                elif (self.recipientType == 'group'):
                    self.body = "%s reacted to %s's message %i in group %s with %s" % (
                                                                            self.sender.getDisplayName(),
                                                                            self.targetAuthor.getDisplayName(),
                                                                            self.targetTimestamp.timestamp,
                                                                            self.recipient.getDisplayName(),
                                                                            self.emoji
                                                                        )
                else:
                    raise ValueError("recipientType invalid value: %s" % self.recipientType)
            
        else:
            self.body = 'Invalid reaction.'
        return