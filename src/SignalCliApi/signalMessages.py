#!/usr/bin/env python3
"""
File: signalMessages.py
Store and handle message lists.
"""
import logging
from typing import Optional, Iterable, Any, TextIO
import os
import socket
import json
from syslog import syslog, LOG_INFO
from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive__, __socket_send__, MessageTypes, __parse_signal_response__,\
    __check_response_for_error__, RecipientTypes
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalGroupUpdate import GroupUpdate
from .signalMention import Mention
from .signalMentions import Mentions
from .signalMessage import Message
from .signalPreview import Preview
from .signalQuote import Quote
from .signalReaction import Reaction
from .signalReceipt import Receipt
from .signalReceivedMessage import ReceivedMessage
from .signalSentMessage import SentMessage
from .signalSticker import Sticker, StickerPacks
from .signalStoryMessage import StoryMessage
from .signalSyncMessage import SyncMessage
from .signalTimestamp import Timestamp
from .signalTypingMessage import TypingMessage
from .signalExceptions import InvalidDataFile, ParameterError


class Messages(object):
    """Class to hold all messages, and act like a list."""

    def __init__(self,
                 command_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 account_path: str,
                 this_device: Device,
                 sticker_packs: StickerPacks,
                 do_load: bool = False,
                 ) -> None:
        """
        Initialize the messages object.
        :param command_socket: socket.socket: The socket to run commands on.
        :param config_path: str: The full path to the signal-cli config directory.
        :param account_id: str: This account's ID.
        :param contacts: Contacts: This accounts Contacts object.
        :param groups: Groups: This accounts Groups object.
        :param devices: Devices: This account Devices object.
        :param account_path: str: The full path to the account data directory.
        :param this_device: Device: This device, Device object.
        :param sticker_packs: StickerPacks: The loaded StickerPacks object.
        :param do_load: bool: True, load from disk, False, do not.
        """
        # Super:
        super().__init__()

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if not isinstance(contacts, Contacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "Contacts", contacts)
        if not isinstance(devices, Devices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            logger.critical("Raising TypeError:")
            __type_error__("this_devices", "Device", this_device)
        if not isinstance(sticker_packs, StickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(do_load, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_load", "bool", do_load)

        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        """The socket to run commands on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """This account's ID."""
        self._contacts: Contacts = contacts
        """This account's Contacts object."""
        self._groups: Groups = groups
        """This account's Groups object."""
        self._devices: Devices = devices
        """This account's Devices object."""
        self._this_device: Device = this_device
        """This device's Device object."""
        self._sticker_packs: StickerPacks = sticker_packs
        """The loaded sticker packs object."""
        self._file_path: str = os.path.join(account_path, "messages.json")
        """The full path to the messages.json file."""
        self._sending: bool = False
        """Are we currently sending a message?"""
        # Set external properties:
        self.messages: list[SentMessage | ReceivedMessage] = []
        """List of sent / received messages."""
        self.sync: list[GroupUpdate | SyncMessage] = []
        """List of sync messages."""
        self.typing: list[TypingMessage] = []
        """List of typing messages."""
        self.story: list[StoryMessage] = []
        """List of story messages."""

        # Do load:
        if do_load:
            if os.path.exists(self._file_path):
                logger.debug("Loading from disk.")
                self.__load__()
            else:
                logger.debug("Creating empty messages.json")
                self.__save__()
        return

    ################################
    # Properties:
    ################################
    @property
    def sending(self) -> bool:
        """
        Return sending status.
        :returns: bool: Sending status. True if sending, False if not.
        """
        return self._sending

    ################################
    # To / From Dict:
    ################################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        messages_dict: dict[str, Any] = {
            "messages": [],
            "syncMessages": [],
            "typingMessages": [],
            "storyMessages": [],
        }
        # Store messages: SentMessage | ReceivedMessage
        for message in self.messages:
            messages_dict["messages"].append(message.__to_dict__())
        # Store sync messages: (sync and group update)
        for message in self.sync:
            if message is None:
                raise RuntimeError("WTF")
            messages_dict['syncMessages'].append(message.__to_dict__())
        # Store typing messages: TypingMessage
        for message in self.typing:
            messages_dict['typingMessages'].append(message.__to_dict__())
        # Store story messages: StoryMessage
        for message in self.story:
            messages_dict['storyMessages'].append(message.__to_dict__())
        return messages_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)

        # Load messages: SentMessage | ReceivedMessage
        self.messages = []
        for message_dict in from_dict['messages']:
            if message_dict['messageType'] == MessageTypes.SENT.value:
                message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      sticker_packs=self._sticker_packs,
                                      from_dict=message_dict)

            elif message_dict['messageType'] == MessageTypes.RECEIVED.value:
                message = ReceivedMessage(command_socket=self._command_socket, account_id=self._account_id,
                                          config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                          devices=self._devices, this_device=self._this_device,
                                          sticker_packs=self._sticker_packs, from_dict=message_dict)
            else:
                warning_message: str = "Invalid message type in messages from_dict: %s" % from_dict['message_type']
                logger.warning(warning_message)
                continue
            self.messages.append(message)
        # Load sync messages: GroupUpdate | SyncMessage
        self.sync = []
        for message_dict in from_dict['syncMessages']:
            if message_dict['messageType'] == MessageTypes.GROUP_UPDATE.value:
                message = GroupUpdate(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device, from_dict=message_dict)
            elif message_dict['messageType'] == MessageTypes.SYNC.value:
                message = SyncMessage(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      sticker_packs=self._sticker_packs, from_dict=message_dict)
            else:
                warning_message: str = "Invalid message type in for sync messages: message type: %i" \
                                       % message_dict['messageType']
                logger.warning(warning_message)
                continue
            self.sync.append(message)
        # Load typing messages:
        self.typing = []
        for message_dict in from_dict['typingMessages']:
            if message_dict['messageType'] == MessageTypes.TYPING.value:
                message = TypingMessage(command_socket=self._command_socket, account_id=self._account_id,
                                        config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                        devices=self._devices, this_device=self._this_device, from_dict=message_dict)
                self.typing.append(message)
            else:
                warning_message: str = "Invalid message type in typing messages: MessageType: %i" \
                                       % message_dict['messageType']
                logger.warning(warning_message)
        # Load Story Messages:
        self.story = []
        for message_dict in from_dict['storyMessages']:
            if message_dict['messageType'] == MessageTypes.STORY.value:
                message = StoryMessage(command_socket=self._command_socket, account_id=self._account_id,
                                       config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                       devices=self._devices, this_device=self._this_device, from_dict=message_dict)
                self.story.append(message)
            else:
                warning_message: str = "Invalid message type in story messages: MessageType: %i" \
                                       % message_dict['messageType']
                logger.warning(warning_message)
        return

    #################################
    # Load / save:
    #################################
    def __load__(self) -> None:
        """
        Load from disk.
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__load__.__name__)
        logger.debug("Loading messages from disk.")
        # Try to open the file:
        try:
            file_handle: TextIO = open(self._file_path, 'r')
            messages_dict: dict[str, Any] = json.loads(file_handle.read())
            file_handle.close()
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = "Couldn't open '%s' for reading: %s" % (self._file_path, str(e.args))
            logger.critical("Raising RuntimeError(%s)" % error_message)
            raise RuntimeError(error_message)
        except json.JSONDecodeError as e:
            error_message = "Couldn't load json from '%s': %s" % (self._file_path, e.msg)
            logger.critical("Raising InvalidDataFile(%s)" % error_message)
            raise InvalidDataFile(error_message, e, self._file_path)
        # Load the dict:
        self.__from_dict__(messages_dict)
        logger.debug("Messages loaded from disk.")
        return

    def __save__(self) -> None:
        """
        Save the messages to disk.
        :return: None
        :raises RuntimeError: On error opening the file for writing.
        """
        # Create a messages Object, and json save string:
        messages_dict: dict[str, Any] = self.__to_dict__()
        json_messages_str: str = json.dumps(messages_dict, indent=4)
        # Open the file and save the JSON:
        try:
            file_handle = open(self._file_path, 'w')
            file_handle.write(json_messages_str)
            file_handle.close()
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = "Failed to open '%s' for writing: %s" % (self._file_path, str(e.args))
            raise RuntimeError(error_message)
        return

    ##################################
    # Helpers:
    ##################################
    def __parse_reaction__(self, reaction: Reaction) -> bool:
        """
        Parse a Reaction message.
        :param reaction: Reaction: The reaction to parse.
        :return: bool: True if the reaction was parsed, False if not.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_reaction__.__name__)

        # Get the messages from the recipients:
        search_messages: list[Message] = []
        if reaction.recipient_type == 'contact':
            messages = self.get_by_sender(reaction.recipient)
            search_messages.extend(messages)
        elif reaction.recipient_type == 'group':
            messages = self.get_by_recipient(reaction.recipient)
            search_messages.extend(messages)
        else:
            # Invalid recipient type:
            error_message = "Invalid reaction cannot parse."
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Find the message that was reacted to:
        reacted_message: Optional[SentMessage | ReceivedMessage | Message] = None
        for message in search_messages:
            if message.sender == reaction.target_author:
                if message.timestamp == reaction.target_timestamp:
                    reacted_message = message
        # If the message isn't in history, do nothing:
        if reacted_message is None:
            return False
        # Have the message add / change / remove the reaction:
        reacted_message.reactions.__parse__(reaction)
        self.__save__()  # save the results.
        return True

    def __parse_receipt__(self, receipt: Receipt) -> None:
        """
        Parse a receipt message.
        :param receipt: Receipt: The receipt message to parse.
        :return: None
        """
        sent_messages = [message for message in self.messages if isinstance(message, SentMessage)]
        for message in sent_messages:
            for timestamp in receipt.timestamps:
                if message.timestamp == timestamp:
                    message.__parse_receipt__(receipt)
                    self.__save__()
        return

    def __parse_read_message_sync__(self, sync_message: SyncMessage) -> None:
        """
        Parse a read message sync message.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        """
        for contact, timestamp in sync_message.read_messages:
            search_messages = self.get_by_sender(contact)
            for message in search_messages:
                if message.timestamp == timestamp:
                    if not message.is_read:
                        if isinstance(message, ReceivedMessage):
                            message.mark_read(when=sync_message.timestamp, send_receipt=False)
                        else:
                            message.mark_read(when=sync_message.timestamp)
        return

    def __parse_sent_message_sync__(self, sync_message: SyncMessage) -> None:
        """
        Parse a sent messages sync message.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        """
        message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                              config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                              devices=self._devices, this_device=self._this_device, sticker_packs=self._sticker_packs,
                              raw_message=sync_message.raw_sent_message)
        self.append(message)
        return

    def __parse_sync_message__(self, sync_message: SyncMessage) -> None:
        """
        Parse a sync message, sending it where it needs to go.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        :raises TypeError: On an invalid SyncMessage type.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_sync_message__.__name__)
        if sync_message.sync_type == SyncMessage.TYPE_READ_MESSAGE_SYNC:
            self.__parse_read_message_sync__(sync_message)
        elif sync_message.sync_type == SyncMessage.TYPE_SENT_MESSAGE_SYNC:
            self.__parse_sent_message_sync__(sync_message)
        else:
            error_message = ("Can only parse SyncMessage.TYPE_READ_MESSAGE_SYNC and SyncMessage.TYPE_SENT_MESSAGE_SYNC"
                             " not: %i" % sync_message.sync_type)
            logger.critical("Raising TypeError(%s)." % error_message)
            raise TypeError(error_message)
        self.__save__()
        return

    def __check_expiries__(self) -> None:
        """
        Check expiry times on all messages.
        :return: None
        """
        for message in self.messages:
            message.__check_expired__()
        return

    def __do_expunge__(self) -> None:
        """
        Expunge expired messages.
        :return: None
        """
        saved_messages: list[SentMessage | ReceivedMessage] = []
        for message in self.messages:
            if not message.is_expired:
                saved_messages.append(message)
        self.messages = saved_messages
        self.__save__()
        return

    ##################################
    # Getters:
    ##################################
    def get_by_timestamp(self, timestamp: Timestamp) -> list[Message]:
        """
        Get messages by timestamp.
        :param timestamp: Timestamp: The timestamp to search for.
        :returns: list[SentMessage|ReceivedMessage]: The list of messages, or an empty list if none found.
        :raises: TypeError: If timestamp is not a Timestamp object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_timestamp.__name__)
        if not isinstance(timestamp, Timestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "Timestamp", timestamp)
        return [message for message in self.messages if message.timestamp == timestamp]

    def get_by_recipient(self, recipient: Group | Contact) -> list[Message]:
        """
        Get messages given a recipient.
        :param recipient: Group | Contact: The recipient to search for.
        :raises: TypeError: If recipient is not a Contact or a Group object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_recipient.__name__)
        if not isinstance(recipient, Contact) and not isinstance(recipient, Group):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "Contact | Group", recipient)
        return [message for message in self.messages if message.recipient == recipient]

    def get_by_sender(self, sender: Contact) -> list[Message]:
        """
        Get messages given a sender.
        :param sender: Contact: The sender to search for.
        :raises: TypeError if sender is not a Contact object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_sender.__name__)
        if not isinstance(sender, Contact):
            logger.critical("Raising TypeError:")
            __type_error__("sender", "Contact", sender)
        messages = [message for message in self.messages if message.sender == sender]
        return messages

    def get_conversation(self, target: Contact | Group) -> list[Message]:
        """
        Get a conversation, given a target contact or group.  Returns a list of messages either sent to or received
            from a contact or group.
        :param target: Contact | Group: The contact or group to search for.
        :returns: list[SentMessage|ReceivedMessage]: The conversation, or an empty list if not found.
        :raises: TypeError: If target is not a Contact or Group object.
        """
        # TODO: Account for when contacts.get_self() returns None. Maybe look into auto creating it.
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_conversation.__name__)
        returnMessages = []
        if isinstance(target, Contact):
            self_contact = self._contacts.get_self()
            for message in self.messages:
                if message.sender == self_contact and message.recipient == target:
                    returnMessages.append(message)
                elif message.sender == target and message.recipient == self_contact:
                    returnMessages.append(message)
        elif isinstance(target, Group):
            for message in self.messages:
                if message.recipient == target:
                    returnMessages.append(message)
        else:
            logger.critical("Raising TypeError:")
            __type_error__("target", "Contact | Group", target)
        return returnMessages

    def find(self,
             author: Contact,
             timestamp: Timestamp,
             conversation: Contact | Group,
             ) -> Optional[SentMessage | ReceivedMessage | Message]:
        """
        Get a message, given an author, a timestamp, and a conversation.
        :param author: Contact: The author of the message we're looking for.
        :param timestamp: Timestamp: The time stamp of the message we're looking for.
        :param conversation: Contact | Group: The conversation the message is in; IE: The conversation between self and
            a specified Contact or Group.
        :returns: SentMessage | ReceivedMessage: The message found, or None if not found.
        :raises: TypeError: If author is not a Contact object, if timestamp is not a Timestamp object, or if
                                conversation is not a Contact or Group object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.find.__name__)

        # Validate author:
        target_author: Contact
        if isinstance(author, Contact):
            target_author = author
        else:
            logger.critical("Raising TypeError:")
            __type_error__("author", "Contact", author)

        # Validate recipient:
        target_conversation: Contact | Group
        if isinstance(conversation, (Contact, Group)):
            target_conversation = conversation
        else:
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "Contact | Group", conversation)

        # Validate timestamp:
        target_timestamp: Timestamp
        if isinstance(timestamp, Timestamp):
            target_timestamp = timestamp
        else:
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "Timestamp", timestamp)

        # Find Message:
        search_messages = self.get_conversation(target_conversation)
        for message in search_messages:
            if message.sender == target_author and message.timestamp == target_timestamp:
                return message
        return None

    def get_quoted(self, quote: Quote) -> Optional[SentMessage | ReceivedMessage | Message]:
        """
        Get a message that contains a given Quote.
        :param quote: Quote: The quote we're looking for.
        :returns: SentMessage | ReceivedMessage: The message that contains the quote, or None if not found.
        :raises: TypeError: If quote is not a Quote object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_quoted.__name__)
        # Type check quote:
        if not isinstance(quote, Quote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "Quote", quote)
        # Search messages in conversation:
        for message in self.get_conversation(quote.conversation):
            if message.sender == quote.author:
                if message.timestamp == quote.timestamp:
                    return message
        return None

    def get_sent(self) -> list[SentMessage]:
        """
        Returns all messages that are SentMessage objects.
        :returns: list[SentMessage]: All the sent messages.
        """
        return [message for message in self.messages if isinstance(message, SentMessage)]

    ##################################
    # Methods:
    ##################################
    def append(self, message: Message) -> None:
        """
        Append a message to the appropriate message list.
        :param message: Message: The message to append.
        :returns: None
        :raises TypeError: If 'message' is not a Message.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.append.__name__)

        # Type check the message:
        if not isinstance(message, (SentMessage, ReceivedMessage, GroupUpdate, SyncMessage, TypingMessage)):
            logger.critical("Raising TypeError:")
            __type_error__("message", "Message", message)

        # Sort the message based on the message type:
        if isinstance(message, (SentMessage, ReceivedMessage)):
            self.messages.append(message)
        elif isinstance(message, (GroupUpdate, SyncMessage)):
            self.sync.append(message)
        elif isinstance(message, TypingMessage):
            self.typing.append(message)
        # Save the messages.
        self.__save__()
        return

    def send_message(self,
                     recipients: Iterable[Contact | Group] | Contact | Group,
                     body: Optional[str] = None,
                     attachments: Optional[Iterable[Attachment | str] | Attachment | str] = None,
                     mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                     quote: Optional[Quote] = None,
                     sticker: Optional[Sticker] = None,
                     preview: Optional[Preview] = None,
                     ) -> tuple[tuple[bool, Contact | Group, str | SentMessage], ...]:

        """
        Send a message.
        :param recipients: Iterable[Contact | Group] | Contact | Group: The recipients of the message.
        :param body: Optional[str]: The body of the message.
        :param attachments: Optional[Iterable[Attachment | str] | Attachment | str ]: Attachments to the message.
        :param mentions: Optional[Iterable[Mention] | Mentions | Mention]: Mentions in the message.
        :param quote: Optional[Quote]: A Quote object for the message.
        :param sticker: Optional[Sticker]: A sticker to send.
        :param preview: Optional[Preview]: A preview for the url in the message, url must appear in the body of the
            message.
        :returns: tuple[tuple[bool, Contact | Group, str | SentMessage]]: A tuple of tuples, the outer tuple is one
            element per message sent.
            The inner tuple's first element, a bool, is True or False for if the message was sent successfully or not.
            The second element of the inner tuple is the Contact | Group the message was sent to.
            The third element of the inner tuple, a str | SentMessage, is either a string containing an error message
            when sending fails, or the SentMessage object on sending success.
        :raises: TypeError: If a recipient is not a Contact or Group object, if body is not a string, if attachments is
            not an Attachment object or a string, or a list of Attachment objects, or strings, if mentions is not a
            list of Mention objects, or not a Mentions object, if quote is not a Quote object, if sticker is not a
            Sticker object, or if preview is not a Preview object.
        :raises: ValueError: If body is an empty string, if attachments is an empty list, or if mentions is an empty
            list.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.send_message.__name__)

        # Validate recipients:
        recipient_type: Optional[RecipientTypes] = None
        target_recipients: list[Contact | Group]
        if isinstance(recipients, Contact):
            recipient_type = RecipientTypes.CONTACT
            target_recipients = [recipients]
        elif isinstance(recipients, Group):
            recipient_type = RecipientTypes.GROUP
            target_recipients = [recipients]
        elif isinstance(recipients, Iterable):
            target_recipients = []
            checkType = None
            for i, recipient in enumerate(recipients):
                if not isinstance(recipient, (Contact, Group)):
                    logger.critical("Raising TypeError:")
                    __type_error__("recipients[%i]" % i, "Contact | Group", recipient)
                if i == 0:
                    checkType = type(recipient)
                    if isinstance(recipient, Contact):
                        recipient_type = RecipientTypes.CONTACT
                    else:
                        recipient_type = RecipientTypes.GROUP
                elif not isinstance(recipient, checkType):
                    logger.critical("Raising TypeError:")
                    __type_error__("recipients[%i]", str(checkType), recipient)
                target_recipients.append(recipient)
        else:
            logger.critical("Raising TypeError:")
            __type_error__("recipients", "Iterable[Contact | Group] | Contact | Group", recipients)
        if len(target_recipients) == 0:
            error_message: str = "recipients cannot be of zero length"
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)

        # Validate body Type and value:
        if body is not None and not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "str | None", body)
        elif body is not None and len(body) == 0:
            error_message: str = "body cannot be empty string"
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)

        # Validate attachments:
        target_attachments: Optional[list[Attachment]] = None
        if attachments is not None:
            if isinstance(attachments, Attachment):
                target_attachments = [attachments]
            elif isinstance(attachments, str):
                target_attachments = [Attachment(config_path=self._config_path, local_path=attachments)]
            elif isinstance(attachments, Iterable):
                target_attachments = []
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, (Attachment, str)):
                        logger.critical("Raising TypeError:")
                        __type_error__("attachments[%i]" % i, "Attachment | str", attachment)
                    if isinstance(attachment, Attachment):
                        target_attachments.append(attachment)
                    else:
                        target_attachments.append(Attachment(config_path=self._config_path, local_path=attachment))
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments", "Iterable[Attachment | str] | Attachment | str", attachments)
        if target_attachments is not None and len(target_attachments) == 0:
            error_message: str = "attachments cannot be empty"
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)

        # Validate mentions:
        target_mentions: Optional[list[Mention] | Mentions] = None
        if mentions is not None:
            if isinstance(mentions, Mentions):
                target_mentions = mentions
            elif isinstance(mentions, Mention):
                target_mentions = [mentions]
            elif isinstance(mentions, Iterable):
                target_mentions = []
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, Mention):
                        logger.critical("Raising TypeError:")
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    target_mentions.append(mention)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
        if target_mentions is not None and len(target_mentions) == 0:
            error_message: str = "mentions cannot be empty"
            logger.critical("Raising ValueError(%s).")
            raise ValueError(error_message)

        # Validate quote:
        if quote is not None and not isinstance(quote, Quote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "SentMessage | ReceivedMessage", quote)

        # Validate sticker:
        if sticker is not None:
            if not isinstance(sticker, Sticker):
                logger.critical("Raising TypeError:")
                raise __type_error__("sticker", "Sticker", sticker)

        # Validate preview:
        if preview is not None:
            if not isinstance(preview, Preview):
                logger.critical("Raising TypeError:")
                __type_error__("preview", "Preview", preview)
            if body.find(preview.url) == -1:
                error_message: str = "preview URL must appear in body of message."
                logger.critical("Raising ValueError(%s)." % error_message)
                raise ValueError(error_message)

        # Validate conflicting options:
        if sticker is not None:
            if body is not None or attachments is not None:
                error_message: str = "If body or attachments are defined, sticker must be None."
                logger.critical("Raising ParameterError(%s).")
                raise ParameterError(error_message)
            if mentions is not None:
                error_message: str = "If sticker is defined, mentions must be None"
                logger.critical("Raising ParameterError(%s).")
                raise ParameterError(error_message)
            if quote is not None:
                error_message: str = "If sticker is defined, quote must be None"
                logger.critical("Raising ParameterError(%s).")
                raise ParameterError(error_message)

        # Create the send message command object:
        send_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "send",
            "params": {
                "account": self._account_id,
            }
        }

        # Add recipients:
        if recipient_type == RecipientTypes.GROUP:
            send_command_obj['params']['groupId'] = []
            for group in target_recipients:
                send_command_obj['params']['groupId'].append(group.get_id())
        elif recipient_type == RecipientTypes.CONTACT:
            send_command_obj['params']['recipient'] = []
            for contact in target_recipients:
                send_command_obj['params']['recipient'].append(contact.get_id())
        else:
            error_message: str = ("'recipient_type' (which might be None) must be either 'contact' or 'group', we should"
                                  " never get here.")
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)

        # Add body:
        if body is not None:
            send_command_obj['params']['message'] = body

        # Add attachments:
        if target_attachments is not None:
            send_command_obj['params']['attachments'] = []
            for attachment in target_attachments:
                send_command_obj['params']['attachments'].append(attachment.local_path)

        # Add mentions:
        if target_mentions is not None:
            send_command_obj['params']['mention'] = []
            for mention in target_mentions:
                send_command_obj['params']['mention'].append(str(mention))

        # Add quote:
        if quote is not None:
            send_command_obj['params']['quoteTimestamp'] = quote.timestamp.timestamp
            send_command_obj['params']['quoteAuthor'] = quote.author.get_id()
            send_command_obj['params']['quoteMessage'] = quote.text
            if quote.mentions is not None:
                send_command_obj['params']['quoteMention'] = []
                for mention in quote.mentions:
                    send_command_obj['params']['quoteMention'].append(str(mention))

        # Add sticker:
        if sticker is not None:
            send_command_obj['params']['sticker'] = str(sticker)

        # Add preview:
        if preview is not None:
            send_command_obj['params']['previewUrl'] = preview.url
            send_command_obj['params']['previewTitle'] = preview.title
            send_command_obj['params']['previewDescription'] = preview.description
            if preview.image is not None:
                send_command_obj['params']['previewImage'] = preview.image.local_path

        # Create json command string:
        json_command_str = json.dumps(send_command_obj) + '\n'

        # Mark system as sending:
        self._sending = True
        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str = __socket_receive__(self._command_socket)
        # Mark system as finished sending
        self._sending = False

        # Parse response and check for error:
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        # TODO: Check if there are other errors somehow.
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])

        # Check for error:
        if error_occurred:
            return_value: list[tuple[bool, Contact | Group, str]] = []
            error_message: str = "signal error while sending message: Code: %i, Message: %s" \
                                 % (signal_code, signal_message)
            if recipient_type == RecipientTypes.CONTACT:
                for recipient in target_recipients:
                    return_value.append((False, recipient, error_message))
            elif recipient_type == RecipientTypes.GROUP:
                for group in target_recipients:
                    for recipient in group.members:
                        return_value.append((False, recipient, error_message))
            return tuple(return_value)

        # Some messages sent, some may have failed.
        results_list: list[dict[str, Any]] = response_obj['result']['results']

        # Gather timestamp:
        timestamp = Timestamp(timestamp=response_obj['result']['timestamp'])

        # Parse results:
        return_value: list[tuple[bool, Contact | Group, SentMessage]] = []
        if recipient_type == RecipientTypes.GROUP:
            sent_messages: list[SentMessage] = []
            for recipient in target_recipients:
                sent_message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                                           config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                           devices=self._devices, this_device=self._this_device,
                                           sticker_packs=self._sticker_packs, recipient=recipient,
                                           timestamp=timestamp, body=body, attachments=target_attachments,
                                           mentions=target_mentions, quote=quote, sticker=sticker, is_sent=True,
                                           sent_to=target_recipients, preview=preview)
                self.append(sent_message)
                sent_messages.append(sent_message)
            for result in results_list:
                # Gather the group and contact:
                group_id = result['groupId']
                _, group = self._groups.__get_or_add__(group_id=group_id)
                contact_id = result['recipientAddress']['number']
                if contact_id is None or contact_id == '':
                    contact_id = result['recipientAddress']['uuid']
                _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
                # Message sent successfully
                if result['type'] == "SUCCESS":
                    for message in sent_messages:
                        if message.recipient == group:
                            message.sent_to.append(contact)
                            return_value.append((True, contact, message))
                # Message failed to send:
                else:
                    return_value.append((False, contact, result['type']))
            return tuple(return_value)

        elif recipient_type == RecipientTypes.CONTACT:
            for result in results_list:
                # Gather contact:
                contact_id = result['recipientAddress']['number']
                if contact_id is None or contact_id == '':
                    contact_id = result['recipientAddress']['uuid']
                _, contact = self._contacts.__get_or_add__(contact_id=contact_id)

                # Message Sent successfully:
                if result['type'] == 'SUCCESS':
                    # Create a sent message
                    sent_message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                                               config_path=self._config_path, contacts=self._contacts,
                                               groups=self._groups, devices=self._devices,
                                               this_device=self._this_device, sticker_packs=self._sticker_packs,
                                               recipient=contact, timestamp=timestamp, body=body,
                                               attachments=target_attachments, mentions=target_mentions, quote=quote,
                                               sticker=sticker, is_sent=True, sent_to=target_recipients,
                                               preview=preview)
                    return_value.append((True, contact, sent_message))
                    self.append(sent_message)
                    self.__save__()
                # Message failed to send:
                else:
                    return_value.append((False, contact, result['type']))
            return tuple(return_value)
