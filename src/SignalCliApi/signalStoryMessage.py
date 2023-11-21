#!/usr/bin/env python3
"""
File: signalStoryMessage.py
Store and handle a story message.
"""
import logging
from typing import Optional, Any
import socket

from .signalAttachment import Attachment
from .signalCommon import __type_error__, MessageTypes, AttachmentTypes
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
    """
    Class to store a story message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 allows_replies: bool = True,
                 preview: Optional[Preview] = None,
                 attachment: Optional[Attachment | TextAttachment] = None,
                 ) -> None:
        """
        Initialize a story message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The Device object representing this device.
        :param from_dict: Optional[dict[str, Any]]: A dict provided by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: A dict provided by Signal.
        :param sender: Optional[Contact]: The sender of this message.
        :param recipient: Optional[Contact | Group]: The recipient of this message. # TODO: Check if this is needed.
        :param device: Optional[Device]: The device sending this message.
        :param timestamp: Optional[Timestamp]: The timestamp of this message.
        :param allows_replies: bool: Does this message allow replies? Defaults to True.
        :param preview: Optional[Preview]: Any URL preview this message contains.
        :param attachment: Optional[Attachment | TextAttachment]: Any attachment to this message.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument Checks:
        # Check allows replies:
        if not isinstance(allows_replies, bool):
            logger.critical("Raising TypeError:")
            __type_error__("allows_replies", "bool", allows_replies)

        # Check preview:
        if preview is not None and not isinstance(preview, Preview):
            logger.critical("Raising TypeError:")
            __type_error__("preview", "Optional[Preview]", preview)

        # Check attachment:
        if attachment is not None:
            if not isinstance(attachment, (Attachment, TextAttachment)):
                logger.critical("Raising TypeError:")
                __type_error__("attachment", "Optional[Attachment | TextAttachment]", attachment)

        # Set external properties:
        # Allows replies:
        self.allows_replies: bool = allows_replies
        """Does this story message allow replies?"""

        # Preview:
        self.preview: Optional[Preview] = preview
        """Any URL preview this story holds."""

        # Attachment:
        self.attachment: Attachment | TextAttachment = attachment
        self.attachment_type: AttachmentTypes = AttachmentTypes.NOT_SET
        if attachment is not None:
            if isinstance(attachment, Attachment):
                self.attachment_type = AttachmentTypes.FILE
            else:
                self.attachment_type = AttachmentTypes.TEXT
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, MessageTypes.STORY)
        return

    ###########################
    # Init:
    ###########################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        # TODO: Look into this.
        # Fetch story message:
        raw_story_message: dict[str, Any] = raw_message['storyMessage']
        # Load allows replies:
        self.allows_replies = raw_story_message['allowsReplies']
        # Attachment:
        self.attachment = None
        self.attachment_type = AttachmentTypes.NOT_SET
        if 'fileAttachment' in raw_story_message.keys():
            self.attachment = Attachment(config_path=self._config_path,
                                         raw_attachment=raw_story_message['fileAttachment'])
            self.attachment_type = AttachmentTypes.FILE
        elif 'textAttachment' in raw_story_message.keys():
            self.attachment = TextAttachment(raw_attachment=raw_story_message['textAttachment'])
            self.attachment_type = AttachmentTypes.TEXT
        # Preview:
        self.preview = None
        if 'preview' in raw_story_message.keys():
            self.preview = Preview(config_path=self._config_path, raw_preview=raw_story_message['preview'])
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this story message.
        :return: dict[str, Any]: The dict to provide to __from_dict__()
        """
        story_message_dict: dict[str, Any] = super().__to_dict__()
        story_message_dict['allowsReplies'] = self.allows_replies
        if self.attachment is None:
            story_message_dict['attachment'] = None
            story_message_dict['attachmentType'] = AttachmentTypes.NOT_SET.value
        else:
            story_message_dict['attachment'] = self.attachment.__to_dict__()
            story_message_dict['attachmentType'] = self.attachment_type.value
        if self.preview is None:
            story_message_dict['preview'] = None
        else:
            story_message_dict['preview'] = self.preview.__to_dict__()
        return story_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        self.allows_replies = from_dict['allowsReplies']
        self.preview = None
        if from_dict['preview'] is not None:
            self.preview = Preview(config_path=self._config_path, from_dict=from_dict['preview'])
        self.attachment_type = AttachmentTypes(from_dict['attachmentType'])
        self.attachment = None
        if from_dict['attachment'] is not None:
            if self.attachment_type == AttachmentTypes.FILE:
                self.attachment = Attachment(config_path=self._config_path, from_dict=from_dict['attachment'])
            elif self.attachment_type == AttachmentTypes.TEXT:
                self.attachment = TextAttachment(from_dict=from_dict['attachment'])
            else:
                raise ValueError("Invalid attachment type in StoryMessage: %s" % self.attachment_type)
        return

    # TODO: reply to this message.
    # TODO: react to this message.
