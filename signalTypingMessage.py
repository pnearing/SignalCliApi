#!/usr/bin/env python3

from typing import Optional, Iterable
import sys
import socket

from .signalAttachment import Attachment
from .signalCommon import __type_error__
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
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
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
                __type_error__("action", 'str', action)
            action = action.upper()
            if (action != 'STARTED' and action != 'STOPPED'):
                raise ValueError("action must be either STARTED or STOPPED")
        # Check time changed:
        if (timeChanged != None and isinstance(timeChanged, Timestamp) == False):
            __type_error__("timeChanged", "Timestamp", timeChanged)
    # Set external properties:
        self.action: str = action
        self.timeChanged: Timestamp = timeChanged
        self.body: str = ''
    # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_TYPING_MESSAGE)
    # update body:
        self.__updateBody__()
        return

    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        typingDict:dict[str, object] = raw_message['typingMessage']
        self.action = typingDict['action']
        self.timeChanged = Timestamp(timestamp=typingDict['timestamp'])
        return

    def __to_dict__(self) -> dict:
        typingMessage = super().__to_dict__()
        typingMessage['action'] = self.action
        if (self.timeChanged != None):
            typingMessage['timeChanged'] = self.timeChanged.__to_dict__()
        else:
            typingMessage['timeChanged'] = None
        return typingMessage

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        self.action = from_dict['action']
        if (from_dict['timeChanged'] != None):
            self.timeChanged = Timestamp(from_dict=from_dict['timeChanged'])
        else:
            self.timeChanged = None
        return
    

    def __updateBody__(self) -> None:
        if (self.sender != None and self.action != None and self.timeChanged != None ):
            if (self.recipient !=None and self.recipient_type != None):
                if (self.recipient_type == 'contact'):
                    self.body = "At %s, %s %s typing." % (self.timeChanged.get_display_time(), self.sender.get_display_name(),
                                                          self.action.lower())
                elif (self.recipient_type == 'group'):
                    self.body = "At %s, %s %s typing in group %s." %(self.timeChanged.get_display_time(), self.sender.get_display_name(),
                                                                     self.action.lower(), self.recipient.get_display_name())
                else:
                    raise ValueError("invalid recipient_type: %s" % self.recipient_type)
        else:
            self.body = "Invalid typing message."