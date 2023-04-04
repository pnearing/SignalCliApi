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
DEBUG: bool = False


class StoryMessage(Message):
    """Class to store a story message."""
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
                 allows_replies: bool = True,
                 preview: Optional[Preview] = None,
                 attachment: Optional[Attachment | TextAttachment] = None,
                 ) -> None:
        # Argument Checks:
        # Check allows replies:
        if not isinstance(allows_replies, bool):
            __type_error__("allows_replies", "bool", allows_replies)
        # Check preview:
        if preview is not None and not isinstance(preview, Preview):
            __type_error__("preview", "Preview", preview)
        # Check attachment:
        if attachment is not None:
            if not isinstance(attachment, Attachment) and not isinstance(attachment, TextAttachment):
                __type_error__("attachment", "Attachment | TextAttachment", attachment)
        # Set external properties:
        # Allows replies:
        self.allows_replies: bool = allows_replies
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
        exit(251)
        # Load allows replies:
        raw_story_message: dict[str, object] = raw_message['storyMessage']
        self.allows_replies = raw_story_message['allows_replies']
        # Attachment:
        self.attachment = None
        if 'fileAttachment' in raw_story_message.keys():
            self.attachment = Attachment(config_path=self._config_path,
                                         raw_attachment=raw_story_message['fileAttachment'])
        elif 'textAttachment' in raw_story_message.keys():
            self.attachment = TextAttachment(raw_attachment=raw_story_message['textAttachment'])
        # Preview:
        self.preview = None
        if 'preview' in raw_story_message.keys():
            self.preview = Preview(config_path=self._config_path, raw_preview=raw_story_message['preview'])
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict:
        story_message_dict = super().__to_dict__()
        return story_message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        return
