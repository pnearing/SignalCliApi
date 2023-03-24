#!/usr/bin/env python3

from typing import Optional
import socket

from .signalAttachment import Attachment
from .signalCommon import __type_error__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalPreview import Preview
from .signalTextAttachment import TextAttachment
from .signalTimestamp import Timestamp

class StoryMessage(Message):
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
                 allowsReplies: bool = True,
                 preview: Optional[Preview] = None,
                 attachment: Optional[Attachment|TextAttachment] = None,
                 ) -> None:
# Argument Checks:
    # Check allows replies:
        if (isinstance(allowsReplies, bool) == False):
            __type_error__("allowsReplies", "bool", allowsReplies)
    # Check preview:
        if (preview != None and isinstance(preview, Preview) == False):
            __type_error__("preview", "Preview", preview)
    # Check attachment:
        if (attachment != None):
            if (isinstance(attachment, Attachment) == False and isinstance(attachment, TextAttachment) == False):
                __type_error__("attachment", "Attachment | TextAttachment", attachment)
# Set external properties:
    # Allows replies:
        self.allowsReplies: bool = allowsReplies
    # Preview:
        self.preview: Optional[Preview] = preview
    # Attachment:
        self.attachment: Attachment | TextAttachment = attachment
    
    # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_STORY_MESSAGE)
        return
    
###########################
# Init:
###########################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        print(raw_message)
    # Load allows replies:
        rawStoryMessage:dict[str,object] = raw_message['storyMessage']
        self.allowsReplies = rawStoryMessage['allowsReplies']
    # Attachment:
        self.attachment = None
        if ('fileAttachment' in rawStoryMessage.keys()):
            self.attachment = Attachment(configPath=self._config_path, rawAttachment=rawStoryMessage['fileAttachment'])
        elif ('textAttachment' in rawStoryMessage.keys()):
            self.attachment = TextAttachment(rawAttachment=rawStoryMessage['textAttachment'])
    # Preview:
        self.preview = None
        if ('preview' in rawStoryMessage.keys()):
            self.preview = Preview(configPath=self._config_path, rawPreview=rawStoryMessage['preview'])
        return
    

###########################
# To / From Dict:
###########################
    def __to_dict__(self) -> dict:
        storyMessageDict = super().__to_dict__()

        return storyMessageDict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        return