#!/usr/bin/env python3

from typing import Optional, Iterable
import sys
import socket

from .signalAttachment import Attachment
from .signalCommon import __typeError__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMention import Mention
from .signalMessage import Message
from .signalReaction import Reaction
from .signalSticker import Sticker
from .signalTimestamp import Timestamp

class TypingMessage(Message):
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
                    sender: Optional[Contact] = None,
                    recipient: Optional[Contact | Group] = None,
                    device: Optional[Device] = None,
                    timestamp: Optional[Timestamp] = None,
                    action: Optional[str] = None,
                    timeChanged: Optional[Timestamp] = None,
                ) -> None:
    # Arg Checks:
        # Check action
        if (action != None):
            if(isinstance(action, str) == False):
                __typeError__("action", 'str', action)
            action = action.upper()
            if (action != 'STARTED' and action != 'STOPPED'):
                raise ValueError("action must be either STARTED or STOPPED")
        # Check time changed:
        if (timeChanged != None and isinstance(timeChanged, Timestamp) == False):
            __typeError__("timeChanged", "Timestamp", timeChanged)
    # Set external properties:
        self.action: str = action
        self.timeChanged: Timestamp = timeChanged
        self.body: str = ''
    # Run super init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, sender, recipient, device, timestamp, Message.TYPE_TYPING_MESSAGE)
    # update body:
        self.__updateBody__()
        return

    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        typingDict:dict[str, object] = rawMessage['typingMessage']
        self.action = typingDict['action']
        self.timeChanged = Timestamp(timestamp=typingDict['timestamp'])
        return

    def __toDict__(self) -> dict:
        typingMessage = super().__toDict__()
        typingMessage['action'] = self.action
        if (self.timeChanged != None):
            typingMessage['timeChanged'] = self.timeChanged.__toDict__()
        else:
            typingMessage['timeChanged'] = None
        return typingMessage

    def __fromDict__(self, fromDict: dict) -> None:
        super().__fromDict__(fromDict)
        self.action = fromDict['action']
        if (fromDict['timeChanged'] != None):
            self.timeChanged = Timestamp(fromDict=fromDict['timeChanged'])
        else:
            self.timeChanged = None
        return
    

    def __updateBody__(self) -> None:
        if (self.sender != None and self.action != None and self.timeChanged != None ):
            if (self.recipient !=None and self.recipientType != None):
                if (self.recipientType == 'contact'):
                    self.body = "At %s, %s %s typing." % (self.timeChanged.get_display_time(), self.sender.getDisplayName(),
                                                          self.action.lower())
                elif (self.recipientType == 'group'):
                    self.body = "At %s, %s %s typing in group %s." %(self.timeChanged.get_display_time(), self.sender.getDisplayName(),
                                                                     self.action.lower(), self.recipient.getDisplayName())
                else:
                    raise ValueError("invalid recipientType: %s" % self.recipientType)
        else:
            self.body = "Invalid typing message."