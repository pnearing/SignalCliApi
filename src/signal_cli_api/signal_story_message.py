#!/usr/bin/env python3
"""
File: signal_story_message.py
Store and handle a story message.
"""
# pylint: disable=R0913, R0914, W0511
import logging
from typing import Optional, Any
import socket

from .signal_attachment import SignalAttachment
from .signal_common import __type_error__, MessageTypes, AttachmentTypes
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_message import SignalMessage
from .signal_preview import SignalPreview
from .signal_text_attachment import SignalTextAttachment
from .signal_timestamp import SignalTimestamp


class SignalStoryMessage(SignalMessage):
    """
    Class to store a story message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 this_device: SignalDevice,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 sender: Optional[SignalContact] = None,
                 recipient: Optional[SignalContact | SignalGroup] = None,
                 device: Optional[SignalDevice] = None,
                 timestamp: Optional[SignalTimestamp] = None,
                 allows_replies: bool = True,
                 preview: Optional[SignalPreview] = None,
                 attachment: Optional[SignalAttachment | SignalTextAttachment] = None,
                 ) -> None:
        """
        Initialize a story message.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to the signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object representing this device.
        :param from_dict: Optional[dict[str, Any]]: A dict provided by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: A dict provided by Signal.
        :param sender: Optional[SignalContact]: The sender of this message.
        # TODO: Check if this is needed:
        :param recipient: Optional[SignalContact | SignalGroup]: The recipient of this message.
        :param device: Optional[SignalDevice]: The device sending this message.
        :param timestamp: Optional[SignalTimestamp]: The timestamp of this message.
        :param allows_replies: bool: Does this message allow replies? Defaults to True.
        :param preview: Optional[SignalPreview]: Any URL preview this message contains.
        :param attachment: Optional[SignalAttachment | SignalTextAttachment]: Any attachment to
            this message.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument Checks:
        # Check allows replies:
        if not isinstance(allows_replies, bool):
            logger.critical("Raising TypeError:")
            __type_error__("allows_replies", "bool", allows_replies)

        # Check preview:
        if preview is not None and not isinstance(preview, SignalPreview):
            logger.critical("Raising TypeError:")
            __type_error__("preview", "Optional[SignalPreview]", preview)

        # Check attachment:
        if attachment is not None:
            if not isinstance(attachment, (SignalAttachment, SignalTextAttachment)):
                logger.critical("Raising TypeError:")
                __type_error__("attachment", "Optional[SignalAttachment | SignalTextAttachment]",
                               attachment)

        # Set external properties:
        # Allows replies:
        self.allows_replies: bool = allows_replies
        """Does this story message allow replies?"""

        # Preview:
        self.preview: Optional[SignalPreview] = preview
        """Any URL preview this story holds."""

        # Attachment:
        self.attachment: SignalAttachment | SignalTextAttachment = attachment
        self.attachment_type: AttachmentTypes = AttachmentTypes.NOT_SET
        if attachment is not None:
            if isinstance(attachment, SignalAttachment):
                self.attachment_type = AttachmentTypes.FILE
            else:
                self.attachment_type = AttachmentTypes.TEXT
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, sender, recipient, device, timestamp,
                         MessageTypes.STORY)

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
            self.attachment = SignalAttachment(config_path=self._config_path,
                                               raw_attachment=raw_story_message['fileAttachment'])
            self.attachment_type = AttachmentTypes.FILE
        elif 'textAttachment' in raw_story_message.keys():
            self.attachment = SignalTextAttachment(
                raw_attachment=raw_story_message['textAttachment'])
            self.attachment_type = AttachmentTypes.TEXT
        # Preview:
        self.preview = None
        if 'preview' in raw_story_message.keys():
            self.preview = SignalPreview(config_path=self._config_path,
                                         raw_preview=raw_story_message['preview'])

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
            self.preview = SignalPreview(config_path=self._config_path,
                                         from_dict=from_dict['preview'])
        self.attachment_type = AttachmentTypes(from_dict['attachmentType'])
        self.attachment = None
        if from_dict['attachment'] is not None:
            if self.attachment_type == AttachmentTypes.FILE:
                self.attachment = SignalAttachment(config_path=self._config_path,
                                                   from_dict=from_dict['attachment'])
            elif self.attachment_type == AttachmentTypes.TEXT:
                self.attachment = SignalTextAttachment(from_dict=from_dict['attachment'])
            else:
                raise ValueError(f"Invalid attachment type in StoryMessage: {self.attachment_type}")

    # TODO: reply to this message.
    # TODO: react to this message.
