#!/usr/bin/env python3

from typing import Optional
import socket

from signalAttachment import Attachment
from signalCommon import __typeError__
from signalContact import Contact
from signalContacts import Contacts
from signalDevice import Device
from signalDevices import Devices
from signalGroup import Group
from signalGroups import Groups 
from signalMessage import Message
from signalPreview import Preview
from signalTextAttachment import TextAttachment
from signalTimestamp import Timestamp

class StoryMessage(Message):
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
                        allowsReplies: bool = True,
                        preview: Optional[Preview] = None,
                        attachment: Optional[Attachment|TextAttachment] = None,
                    ) -> None:
# Argument Checks:
    # Check allows replies:
        if (isinstance(allowsReplies, bool) == False):
            __typeError__("allowsReplies", "bool", allowsReplies)
    # Check preview:
        if (preview != None and isinstance(preview, Preview) == False):
            __typeError__("preview", "Preview", preview)
    # Check attachment:
        if (attachment != None):
            if (isinstance(attachment, Attachment) == False and isinstance(attachment, TextAttachment) == False):
                __typeError__("attachment", "Attachment | TextAttachment", attachment)
# Set external properties:
    # Allows replies:
        self.allowsReplies: bool = allowsReplies
    # Preview:
        self.preview: Optional[Preview] = preview
    # Attachment:
        self.attachment: Attachment | TextAttachment = attachment
    
    # Run super init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, sender, recipient, device, timestamp, Message.TYPE_STORY_MESSAGE)
        return
    
###########################
# Init:
###########################
    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        print(rawMessage)
    # Load allows replies:
        rawStoryMessage:dict[str,object] = rawMessage['storyMessage']
        self.allowsReplies = rawStoryMessage['allowsReplies']
    # Attachment:
        self.attachment = None
        if ('fileAttachment' in rawStoryMessage.keys()):
            self.attachment = Attachment(configPath=self._configPath, rawAttachment=rawStoryMessage['fileAttachment'])
        elif ('textAttachment' in rawStoryMessage.keys()):
            self.attachment = TextAttachment(rawAttachment=rawStoryMessage['textAttachment'])
    # Preview:
        self.preview = None
        if ('preview' in rawStoryMessage.keys()):
            self.preview = Preview(configPath=self._configPath, rawPreview=rawStoryMessage['preview'])
        return
    

###########################
# To / From Dict:
###########################
    def __toDict__(self) -> dict:
        storyMessageDict = super().__toDict__()

        return storyMessageDict

    def __fromDict__(self, fromDict: dict) -> None:
        super().__fromDict__(fromDict)
        return