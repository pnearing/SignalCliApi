#!/usr/bin/env python3
"""
File: signal_messages.py
Store and handle message lists.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915, W0511, W1116, C0302
import logging
from typing import Optional, Iterable, Any
import os
import socket
import json
from .signal_attachment import SignalAttachment
from .signal_common import __type_error__, __socket_receive_blocking__, __socket_send__, \
    MessageTypes, \
    __parse_signal_response__, \
    __check_response_for_error__, RecipientTypes, SyncTypes, MessageFilter, __socket_create__, \
    __socket_connect__, __socket_close__, HONOUR_VIEW_ONCE, HONOUR_EXPIRY
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_group_update import SignalGroupUpdate
from .signal_mention import SignalMention
from .signal_mentions import SignalMentions
from .signal_message import SignalMessage
from .signal_preview import SignalPreview
from .signal_quote import SignalQuote
from .signal_reaction import SignalReaction
from .signal_receipt import SignalReceipt
from .signal_received_message import SignalReceivedMessage
from .signal_sent_message import SignalSentMessage
from .signal_sticker import SignalSticker, SignalStickerPacks
from .signal_story_message import SignalStoryMessage
from .signal_sync_message import SignalSyncMessage
from .signal_timestamp import SignalTimestamp
from .signal_typing_message import SignalTypingMessage
from .signal_exceptions import InvalidDataFile, ParameterError


class SignalMessages:
    """Class to hold all messages, and act like a list."""

    def __init__(self,
                 command_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 account_path: str,
                 this_device: SignalDevice,
                 sticker_packs: SignalStickerPacks,
                 do_load: bool = False,
                 ) -> None:
        """
        Initialize the messages object.
        :param command_socket: socket.socket: The socket to run commands on.
        :param config_path: str: The full path to the signal-cli config directory.
        :param account_id: str: This account's ID.
        :param contacts: SignalContacts: This accounts SignalContacts object.
        :param groups: SignalGroups: This accounts SignalGroups object.
        :param devices: SignalDevices: This account SignalDevices object.
        :param account_path: str: The full path to the account data directory.
        :param this_device: SignalDevice: This device, SignalDevice object.
        :param sticker_packs: SignalStickerPacks: The loaded SignalStickerPacks object.
        :param do_load: bool: True, load from disk, False, do not.
        """
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
        if not isinstance(contacts, SignalContacts):
            logger.critical("Raising TypeError:")
            __type_error__("contacts", "SignalContacts", contacts)
        if not isinstance(devices, SignalDevices):
            logger.critical("Raising TypeError:")
            __type_error__("devices", "SignalDevices", devices)
        if not isinstance(this_device, SignalDevice):
            logger.critical("Raising TypeError:")
            __type_error__("this_devices", "SignalDevice", this_device)
        if not isinstance(sticker_packs, SignalStickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "SignalStickerPacks", sticker_packs)
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
        self._contacts: SignalContacts = contacts
        """This account's SignalContacts object."""
        self._groups: SignalGroups = groups
        """This account's SignalGroups object."""
        self._devices: SignalDevices = devices
        """This account's SignalDevices object."""
        self._this_device: SignalDevice = this_device
        """This device's SignalDevice object."""
        self._sticker_packs: SignalStickerPacks = sticker_packs
        """The loaded sticker packs object."""
        self._file_path: str = os.path.join(account_path, "messages.json")
        """The full path to the messages.json file."""
        self._sending: bool = False
        """Are we currently sending a message?"""
        self._unparsed_receipts: list[SignalReceipt] = []
        """A list of un-parsed receipts."""

        # Set external properties:
        self.messages: list[SignalSentMessage | SignalReceivedMessage] = []
        """List of sent / received messages."""
        self.sync: list[SignalGroupUpdate | SignalSyncMessage] = []
        """List of sync messages."""
        self.typing: list[SignalTypingMessage] = []
        """List of typing messages."""
        self.story: list[SignalStoryMessage] = []
        """List of story messages."""

        # Do load:
        if do_load:
            if os.path.exists(self._file_path):
                logger.debug("Loading from disk.")
                self.__load__()
            else:
                logger.debug("Creating empty messages.json")
                self.__save__()

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
            "unparsedReceipts": [],
        }
        # Store messages: SignalSentMessage | SignalReceivedMessage
        for message in self.messages:
            if (not message.is_expired or not HONOUR_EXPIRY) and (
                    not message.view_once or not HONOUR_VIEW_ONCE):
                messages_dict["messages"].append(message.__to_dict__())
        # Store sync messages: (sync and group update)
        for message in self.sync:
            if message is None:
                raise RuntimeError("WTF")
            messages_dict['syncMessages'].append(message.__to_dict__())
        # Store typing messages: SignalTypingMessage
        for message in self.typing:
            messages_dict['typingMessages'].append(message.__to_dict__())
        # Store story messages: SignalStoryMessage
        for message in self.story:
            messages_dict['storyMessages'].append(message.__to_dict__())
        # Store unparsed receipts:
        for receipt in self._unparsed_receipts:
            messages_dict['unparsedReceipts'].append(receipt.__to_dict__())

        return messages_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)

        # Load messages: SignalSentMessage | SignalReceivedMessage
        self.messages = []
        for message_dict in from_dict['messages']:
            if message_dict['messageType'] == MessageTypes.SENT.value:
                message = SignalSentMessage(command_socket=self._command_socket,
                                            account_id=self._account_id,
                                            config_path=self._config_path, contacts=self._contacts,
                                            groups=self._groups, devices=self._devices,
                                            this_device=self._this_device,
                                            sticker_packs=self._sticker_packs,
                                            from_dict=message_dict)

            elif message_dict['messageType'] == MessageTypes.RECEIVED.value:
                message = SignalReceivedMessage(command_socket=self._command_socket,
                                                account_id=self._account_id,
                                                config_path=self._config_path,
                                                contacts=self._contacts, groups=self._groups,
                                                devices=self._devices,
                                                this_device=self._this_device,
                                                sticker_packs=self._sticker_packs,
                                                from_dict=message_dict)
            else:
                warning_message: str = (f"Invalid message type in messages "
                                        f"from_dict: {from_dict['message_type']}")
                logger.warning(warning_message)
                continue
            self.messages.append(message)
        # Load sync messages: SignalGroupUpdate | SignalSyncMessage
        self.sync = []
        for message_dict in from_dict['syncMessages']:
            if message_dict['messageType'] == MessageTypes.GROUP_UPDATE.value:
                message = SignalGroupUpdate(command_socket=self._command_socket,
                                            account_id=self._account_id,
                                            config_path=self._config_path, contacts=self._contacts,
                                            groups=self._groups, devices=self._devices,
                                            this_device=self._this_device, from_dict=message_dict)
            elif message_dict['messageType'] == MessageTypes.SYNC.value:
                message = SignalSyncMessage(command_socket=self._command_socket,
                                            account_id=self._account_id,
                                            config_path=self._config_path, contacts=self._contacts,
                                            groups=self._groups, devices=self._devices,
                                            this_device=self._this_device,
                                            sticker_packs=self._sticker_packs,
                                            from_dict=message_dict)
            else:
                warning_message: str = ("Invalid message type in for sync messages:"
                                        f"message type: {message_dict['messageType']}")
                logger.warning(warning_message)
                continue
            self.sync.append(message)
        # Load typing messages:
        self.typing = []
        for message_dict in from_dict['typingMessages']:
            if message_dict['messageType'] == MessageTypes.TYPING.value:
                message = SignalTypingMessage(command_socket=self._command_socket,
                                              account_id=self._account_id,
                                              config_path=self._config_path,
                                              contacts=self._contacts,
                                              groups=self._groups, devices=self._devices,
                                              this_device=self._this_device, from_dict=message_dict)
                self.typing.append(message)
            else:
                warning_message: str = (f"Invalid message type in typing messages: "
                                        f"MessageType: {message_dict['messageType']}")
                logger.warning(warning_message)
        # Load Story Messages:
        self.story = []
        for message_dict in from_dict['storyMessages']:
            if message_dict['messageType'] == MessageTypes.STORY.value:
                message = SignalStoryMessage(command_socket=self._command_socket,
                                             account_id=self._account_id,
                                             config_path=self._config_path, contacts=self._contacts,
                                             groups=self._groups, devices=self._devices,
                                             this_device=self._this_device, from_dict=message_dict)
                self.story.append(message)
            else:
                warning_message: str = ("Invalid message type in story messages: "
                                        f"MessageType: {message_dict['messageType']}")
                logger.warning(warning_message)

        # Load unparsed receipts:
        self._unparsed_receipts = []
        for receipt_dict in from_dict['unparsedReceipts']:
            receipt = SignalReceipt(command_socket=self._command_socket,
                                    account_id=self._account_id,
                                    config_path=self._config_path, contacts=self._contacts,
                                    groups=self._groups, devices=self._devices,
                                    this_device=self._this_device, from_dict=receipt_dict)
            self.__parse_receipt__(receipt)

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
            with open(self._file_path, 'r', encoding='utf-8') as file_handle:
                messages_dict: dict[str, Any] = json.loads(file_handle.read())
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = f"Couldn't open '{self._file_path}' for reading: {str(e.args)}"
            logger.critical("Raising RuntimeError(%s)", error_message)
            raise RuntimeError(error_message) from e
        except json.JSONDecodeError as e:
            error_message = f"Couldn't load json from '{self._file_path}': {e.msg}"
            logger.critical("Raising InvalidDataFile(%s)", error_message)
            raise InvalidDataFile(error_message, e, self._file_path) from e
        # Load the dict:
        self.__from_dict__(messages_dict)
        logger.debug("Messages loaded from disk.")

    def __save__(self) -> None:
        """
        Save the messages to disk.
        :return: None
        :raises RuntimeError: On error opening the file for writing.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__save__.__name__)
        logger.debug("Saving messages.")
        # Create a messages Object, and json save string:
        messages_dict: dict[str, Any] = self.__to_dict__()
        json_messages_str: str = json.dumps(messages_dict, indent=4)
        # Open the file and save the JSON:
        try:
            with open(self._file_path, 'w', encoding='utf-8') as file_handle:
                file_handle.write(json_messages_str)
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message = f"Failed to open '{self._file_path}' for writing: {str(e.args)}"
            raise RuntimeError(error_message) from e

    ##################################
    # Helpers:
    ##################################
    def __parse_reaction__(self, reaction: SignalReaction) -> bool:
        """
        Parse a Reaction message.
        :param reaction: SignalReaction: The reaction to parse.
        :return: bool: True if the reaction was parsed, False if not.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_reaction__.__name__)

        # Get the messages from the recipients:
        search_messages: list[SignalMessage] = []
        if reaction.recipient_type == RecipientTypes.CONTACT:
            messages = self.get_by_sender(reaction.recipient)
            search_messages.extend(messages)
        elif reaction.recipient_type == RecipientTypes.GROUP:
            messages = self.get_by_recipient(reaction.recipient)
            search_messages.extend(messages)
        else:
            # Invalid recipient type:
            error_message = "Invalid reaction cannot parse."
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)
        # Find the message that was reacted to:
        reacted_message: Optional[SignalSentMessage | SignalReceivedMessage | SignalMessage] = None
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

    def __parse_receipt__(self, receipt: SignalReceipt) -> None:
        """
        Parse a receipt message.
        :param receipt: SignalReceipt: The receipt message to parse.
        :return: None
        """
        # Mark seen:
        receipt.sender.__seen__(receipt.timestamp)
        receipt.device.__seen__(receipt.timestamp)
        receipt.recipient.__seen__(receipt.timestamp)
        # Build a list of unparsed receipts
        receipts = [receipt, *self._unparsed_receipts]
        self._unparsed_receipts = []
        should_save: bool = False
        for _receipt in receipts:
            # Parse receipts:
            receipt_parsed: bool = False
            for message in self.get_sent_messages():
                for timestamp in _receipt.timestamps:
                    if message.timestamp == timestamp:
                        message.__parse_receipt__(_receipt)
                        receipt_parsed = True
            if receipt_parsed:
                should_save = True
            else:
                self._unparsed_receipts.append(_receipt)
        if should_save:
            self.__save__()

    def __parse_read_message_sync__(self, sync_message: SignalSyncMessage) -> None:
        """
        Parse a read message sync message.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        """
        # Mark sync_message seen:
        sync_message.sender.__seen__(sync_message.timestamp)
        sync_message.device.__seen__(sync_message.timestamp)
        sync_message.recipient.__seen__(sync_message.timestamp)

        # Parse the read message sync message:
        should_save: bool = False
        for contact, timestamp in sync_message.read_messages:
            search_messages = self.get_by_sender(contact)
            for message in search_messages:
                if message.timestamp == timestamp:
                    if not message.is_read:
                        should_save = True
                        if isinstance(message, SignalReceivedMessage):
                            message.mark_read(when=sync_message.timestamp, send_receipt=False)
                        else:
                            message.mark_read(when=sync_message.timestamp)
        if should_save:
            self.__save__()

    def __parse_sent_message_sync__(self, sync_message: SignalSyncMessage) -> None:
        """
        Parse a sent messages sync message.
        :param sync_message: SyncMessage: The sync message to parse.
        :return: None
        """
        message = SignalSentMessage(command_socket=self._command_socket,
                                    account_id=self._account_id, config_path=self._config_path,
                                    contacts=self._contacts, groups=self._groups,
                                    devices=self._devices, this_device=self._this_device,
                                    sticker_packs=self._sticker_packs,
                                    raw_message=sync_message.raw_sent_message)
        message.mark_delivered()
        self.append(message)

    def __parse_sent_reaction_sync__(self, sync_message: SignalSyncMessage) -> None:
        reaction = SignalReaction(command_socket=self._command_socket, account_id=self._account_id,
                                  config_path=self._config_path, contacts=self._contacts,
                                  groups=self._groups, devices=self._devices,
                                  this_device=self._this_device,
                                  sync_message=sync_message.raw_sent_message)
        self.__parse_reaction__(reaction)

    def __parse_sync_message__(self, sync_message: SignalSyncMessage) -> None:
        """
        Parse a sync message, sending it where it needs to go.
        :param sync_message: SignalSyncMessage: The sync message to parse.
        :return: None
        :raises TypeError: On an invalid SignalSyncMessage type.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_sync_message__.__name__)
        if sync_message.sync_type == SyncTypes.READ_MESSAGES:
            self.__parse_read_message_sync__(sync_message)
        elif sync_message.sync_type == SyncTypes.SENT_MESSAGES:
            self.__parse_sent_message_sync__(sync_message)
        elif sync_message.sync_type == SyncTypes.SENT_REACTION:
            self.__parse_sent_reaction_sync__(sync_message)
        else:
            error_message = ("Can only parse SyncTypes.READ_MESSAGES, SyncTypes.SENT_MESSAGES,"
                             f" and SyncTypes.SENT_REACTION, not: {str(sync_message.sync_type)}")
            logger.critical("Raising TypeError(%s).", error_message)
            raise TypeError(error_message)
        self.__save__()

    ##################################
    # Getters:
    ##################################
    def get_by_timestamp(self, timestamp: SignalTimestamp) -> list[SignalMessage]:
        """
        Get messages by timestamp.
        :param timestamp: SignalTimestamp: The timestamp to search for.
        :returns: list[SentMessage|ReceivedMessage]: The list of messages, or an empty list if
        none found.
        :raises: TypeError: If timestamp is not a SignalTimestamp object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_timestamp.__name__)
        if not isinstance(timestamp, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "SignalTimestamp", timestamp)
        return [message for message in self.messages if message.timestamp == timestamp]

    def get_by_recipient(self, recipient: SignalGroup | SignalContact) -> list[SignalMessage]:
        """
        Get messages given a recipient.
        :param recipient: SignalGroup | SignalContact: The recipient to search for.
        :raises: TypeError: If recipient is not a SignalContact or a SignalGroup object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_recipient.__name__)
        if not isinstance(recipient, SignalContact) and not isinstance(recipient, SignalGroup):
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "SignalContact | SignalGroup", recipient)
        return [message for message in self.messages if message.recipient == recipient]

    def get_by_sender(self, sender: SignalContact) -> list[SignalMessage]:
        """
        Get messages given a sender.
        :param sender: SignalContact: The sender to search for.
        :raises: TypeError if sender is not a SignalContact object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_sender.__name__)
        if not isinstance(sender, SignalContact):
            logger.critical("Raising TypeError:")
            __type_error__("sender", "SignalContact", sender)
        messages = [message for message in self.messages if message.sender == sender]
        return messages

    def get_received_messages(self) -> list[SignalReceivedMessage]:
        """
        Get a list of received messages, returns an empty list if none found.
        """
        return [message for message in self.messages if isinstance(message, SignalReceivedMessage)]

    def get_sent_messages(self) -> list[SignalSentMessage]:
        """
        Get a list of sent messages, returns an empty list if none found.
        """
        return [message for message in self.messages if isinstance(message, SignalSentMessage)]

    def get_received_unread(self, sender: Optional[SignalContact] = None) -> list[SignalMessage]:
        """

        This method returns a list of unread Signal messages received by the user.

        Parameters:
        - sender (Optional[SignalContact]): The sender of the messages. If None is passed, all
        received unread messages will be returned.

        Returns:
        - list[SignalMessage]: A list of unread SignalMessage objects.

        Note:
        - If the 'sender' parameter is None, all received unread messages will be considered.
        - If the 'sender' parameter is not None, only the unread messages from the specified sender
        will be considered.

        """
        if sender is None:
            messages = self.get_received_messages()
        else:
            messages = self.get_by_sender(sender)
        return [message for message in messages if message.is_read is False]

    def get_sent_unread(self,
                        recipient: Optional[SignalContact | SignalGroup] = None,
                        ) -> list[SignalMessage]:
        """
        Get a list of unread sent messages, return an empty list if none found.
        """
        if recipient is None:
            messages = self.get_sent_messages()
        else:
            messages = self.get_by_recipient(recipient)
        return [message for message in messages if message.is_read is False]

    def get_conversation(self,
                         target: SignalContact | SignalGroup,
                         message_filter: int = MessageFilter.NONE,
                         ) -> list[SignalMessage]:
        """
        Get a conversation, given a target contact or group.  Returns a list of messages either
        sent to or received from a contact or group.
        :param target: SignalContact | SignalGroup: The contact or group to search for.
        :param message_filter: int: The filter. Use signalCommon.MessageFilter flag values.
        :returns: list[SentMessage|ReceivedMessage]: The conversation, or an empty list if not
        found.
        :raises: TypeError: If target is not a SignalContact or SignalGroup object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_conversation.__name__)
        return_messages = []
        if isinstance(target, SignalContact):
            self_contact = self._contacts.get_self()
            for message in self.messages:
                if message.sender == self_contact and message.recipient == target:
                    return_messages.append(message)
                elif message.sender == target and message.recipient == self_contact:
                    return_messages.append(message)
        elif isinstance(target, SignalGroup):
            for message in self.messages:
                if message.recipient.get_id() == target.get_id():
                    return_messages.append(message)
                # if message.recipient == target:
                #     return_messages.append(message)
        else:
            logger.critical("Raising TypeError:")
            __type_error__("target", "SignalContact | SignalGroup", target)
        # Apply filters:
        if message_filter == MessageFilter.NONE:
            return return_messages
        if message_filter & MessageFilter.READ:
            return_messages = [message for message in return_messages if message.is_read is True]
        elif message_filter & MessageFilter.NOT_READ:
            return_messages = [message for message in return_messages if message.is_read is False]
        if message_filter & MessageFilter.VIEWED:
            return_messages = [message for message in return_messages if message.is_viewed is True]
        elif message_filter & MessageFilter.NOT_VIEWED:
            return_messages = [message for message in return_messages if message.is_viewed is False]
        if message_filter & MessageFilter.DELIVERED:
            return_messages = [message for message in return_messages if
                               message.is_delivered is True]
        elif message_filter & MessageFilter.NOT_DELIVERED:
            return_messages = [message for message in return_messages if
                               message.is_delivered is False]
        return return_messages

    def find(self,
             author: SignalContact,
             timestamp: SignalTimestamp,
             conversation: SignalContact | SignalGroup,
             ) -> Optional[SignalSentMessage | SignalReceivedMessage | SignalMessage]:
        """
        Get a message, given an author, a timestamp, and a conversation.
        :param author: SignalContact: The author of the message we're looking for.
        :param timestamp: SignalTimestamp: The time stamp of the message we're looking for.
        :param conversation: SignalContact | SignalGroup: The conversation the message is in;
        IE: The conversation between self and a specified SignalContact or SignalGroup.
        :returns: SentMessage | ReceivedMessage: The message found, or None if not found.
        :raises: TypeError: If author is not a SignalContact object, if timestamp is not a
        SignalTimestamp object, or if conversation is not a SignalContact or SignalGroup object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.find.__name__)

        # Validate author:
        target_author: SignalContact
        if isinstance(author, SignalContact):
            target_author = author
        else:
            logger.critical("Raising TypeError:")
            __type_error__("author", "SignalContact", author)

        # Validate recipient:
        target_conversation: SignalContact | SignalGroup
        if isinstance(conversation, (SignalContact, SignalGroup)):
            target_conversation = conversation
        else:
            logger.critical("Raising TypeError:")
            __type_error__("recipient", "SignalContact | SignalGroup", conversation)

        # Validate timestamp:
        target_timestamp: SignalTimestamp
        if isinstance(timestamp, SignalTimestamp):
            target_timestamp = timestamp
        else:
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "SignalTimestamp", timestamp)

        # Find Message:
        search_messages = self.get_conversation(target_conversation)
        for message in search_messages:
            if message.sender == target_author and message.timestamp == target_timestamp:
                return message
        return None

    def get_quoted(self, quote: SignalQuote) -> Optional[SignalSentMessage | SignalReceivedMessage
                                                         | SignalMessage]:
        """
        Get a message that contains a given SignalQuote.
        :param quote: SignalQuote: The quote we're looking for.
        :returns: SentMessage | ReceivedMessage: The message that contains the
        quote, or None if not found.
        :raises: TypeError: If quote is not a SignalQuote object.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_quoted.__name__)
        # Type check quote:
        if not isinstance(quote, SignalQuote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "SignalQuote", quote)
        # Search messages in conversation:
        for message in self.get_conversation(quote.conversation):
            if message.sender == quote.author:
                if message.timestamp == quote.timestamp:
                    return message
        return None

    def get_mentioned(self, contact: Optional[SignalContact]) -> list[SignalReceivedMessage]:
        """
        Retrieves a list of messages in which the specified contact is mentioned.

        If the contact is not provided, the method defaults to using the instance's own contact.

        Parameters:
            contact (Optional[SignalContact]): The contact to check for mentions. If None, the
                instance's own contact is used.

        Returns:
            list[SignalReceivedMessage]: A list of received messages where the given contact is
                mentioned.
        """
        if contact is None:
            contact = self._contacts.get_self()

        messages: list[SignalReceivedMessage] = self.get_received_messages()
        mentioned: list[SignalReceivedMessage] = []
        for message in messages:
            if message.mentions.contact_mentioned(contact):
                mentioned.append(message)
        return mentioned

    ##################################
    # Methods:
    ##################################
    def do_expunge(self) -> None:
        """
        Expunge expired messages.
        :return: None
        """
        saved_messages: list[SignalSentMessage | SignalReceivedMessage] = []
        for message in self.messages:
            if not message.is_expired:
                saved_messages.append(message)
        self.messages = saved_messages
        self.__save__()

    def append(self, message: SignalMessage) -> None:
        """
        Append a message to the appropriate message list.
        :param message: SignalMessage: The message to append.
        :returns: None
        :raises TypeError: If 'message' is not a SignalMessage.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.append.__name__)
        # Type check message:
        if not isinstance(message, (
                SignalSentMessage, SignalReceivedMessage, SignalGroupUpdate, SignalSyncMessage,
                SignalTypingMessage)):
            logger.critical("Raising TypeError:")
            __type_error__("message", "SignalSentMessage | SignalReceivedMessage | "
                                      "SignalGroupUpdate | SignalSyncMessage | SignalTypingMessage",
                           message)

        # Mark seen:
        message.sender.__seen__(message.timestamp)
        message.recipient.__seen__(message.timestamp)
        message.device.__seen__(message.timestamp)
        # Sort the message based on the message type:
        if isinstance(message, (SignalSentMessage, SignalReceivedMessage)):
            self.messages.append(message)
        elif isinstance(message, (SignalGroupUpdate, SignalSyncMessage)):
            self.sync.append(message)
        elif isinstance(message, SignalTypingMessage):
            self.typing.append(message)

        # Save the messages.
        self.__save__()

    def send_message(self,
                     recipients: Iterable[
                                     SignalContact | SignalGroup] | SignalContact | SignalGroup,
                     body: Optional[str] = None,
                     attachments: Optional[
                         Iterable[SignalAttachment | str] | SignalAttachment | str] = None,
                     mentions: Optional[
                         Iterable[SignalMention] | SignalMentions | SignalMention] = None,
                     quote: Optional[SignalQuote] = None,
                     sticker: Optional[SignalSticker] = None,
                     previews: Optional[Iterable[SignalPreview]] = None,
    ) -> tuple[tuple[bool, SignalContact | SignalGroup, str | SignalSentMessage], ...]:

        """
        Send a message.
        :param recipients: Iterable[SignalContact | SignalGroup] | SignalContact | SignalGroup:
        The recipients of the message.
        :param body: Optional[str]: The body of the message.
        :param attachments: Optional[Iterable[SignalAttachment | str] | SignalAttachment | str ]:
        Attachments to the message.
        :param mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention]:
        Mentions in the message.
        :param quote: Optional[SignalQuote]: A SignalQuote object for the message.
        :param sticker: Optional[SignalSticker]: A sticker to send.
        :param previews: Optional[Iterable[SignalPreview]]: A preview for the url in the message,
        url must appear in the body of the message.
        :returns: tuple[tuple[bool, SignalContact | SignalGroup, str | SentMessage]]: A tuple of
        tuples, the outer-tuple is one element per message sent.
        The inner tuple's first element, a bool, is True or False for if the message was sent
        successfully or not.
        The second element of the inner tuple is the SignalContact | SignalGroup the message was
        sent to.
        The third element of the inner tuple, a str | SentMessage, is either a string containing an
        error message when sending fails, or the SentMessage object on sending success.
        :raises: TypeError: If a recipient is not a SignalContact or SignalGroup object, if body is
        not a string, if attachments is not an SignalAttachment object or a string, or a list of
        SignalAttachment objects, or strings, if mentions is not a list of SignalMention objects,
        or not a SignalMentions object, if quote is not a SignalQuote object, if sticker is not a
        SignalSticker object, or if previews is not an Optional[Iterable[SignalPreview] object.
        :raises: ValueError: If body is an empty string, if attachments is an empty list, or if
        mentions is an empty list.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.send_message.__name__)

        # Validate recipients:
        recipient_type: Optional[RecipientTypes] = None
        target_recipients: list[SignalContact | SignalGroup]
        if isinstance(recipients, SignalContact):
            recipient_type = RecipientTypes.CONTACT
            target_recipients = [recipients]
        elif isinstance(recipients, SignalGroup):
            recipient_type = RecipientTypes.GROUP
            target_recipients = [recipients]
        elif isinstance(recipients, Iterable):
            target_recipients = []
            check_type = None
            for i, recipient in enumerate(recipients):
                if not isinstance(recipient, (SignalContact, SignalGroup)):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"recipients[{i}]", "SignalContact | SignalGroup", recipient)
                if i == 0:
                    check_type = type(recipient)
                    if isinstance(recipient, SignalContact):
                        recipient_type = RecipientTypes.CONTACT
                    else:
                        recipient_type = RecipientTypes.GROUP
                elif not isinstance(recipient, check_type):
                    logger.critical("Raising TypeError:")
                    __type_error__(f"recipients[{i}]", str(check_type), recipient)
                target_recipients.append(recipient)
        else:
            logger.critical("Raising TypeError:")
            __type_error__("recipients",
                           "Iterable[SignalContact | SignalGroup] | SignalContact | SignalGroup",
                           recipients)
        if len(target_recipients) == 0:
            error_message: str = "recipients cannot be of zero length"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Validate body Type and value:
        if body is not None and not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "str | None", body)
        elif body is not None and len(body) == 0:
            error_message: str = "body cannot be empty string"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Validate attachments:
        target_attachments: Optional[list[SignalAttachment]] = None
        if attachments is not None:
            if isinstance(attachments, SignalAttachment):
                target_attachments = [attachments]
            elif isinstance(attachments, str):
                target_attachments = [
                    SignalAttachment(config_path=self._config_path, local_path=attachments)]
            elif isinstance(attachments, Iterable):
                target_attachments = []
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, (SignalAttachment, str)):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"attachments[{i}]", "SignalAttachment | str", attachment)
                    if isinstance(attachment, SignalAttachment):
                        target_attachments.append(attachment)
                    else:
                        target_attachments.append(
                            SignalAttachment(config_path=self._config_path, local_path=attachment))
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments",
                               "Iterable[SignalAttachment | str] | SignalAttachment | str",
                               attachments)
        if target_attachments is not None and len(target_attachments) == 0:
            error_message: str = "attachments cannot be empty"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Validate mentions:
        target_mentions: Optional[list[SignalMention] | SignalMentions] = None
        if mentions is not None:
            if isinstance(mentions, SignalMentions):
                target_mentions = mentions
            elif isinstance(mentions, SignalMention):
                target_mentions = [mentions]
            elif isinstance(mentions, Iterable):
                target_mentions = []
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, SignalMention):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"mentions[{i}]", "SignalMention", mention)
                    target_mentions.append(mention)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("mentions", "Optional[Iterable[SignalMention] | SignalMention]",
                               mentions)
        if target_mentions is not None and len(target_mentions) == 0:
            error_message: str = "mentions cannot be empty"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Validate quote:
        if quote is not None and not isinstance(quote, SignalQuote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "SentMessage | ReceivedMessage", quote)

        # Validate sticker:
        if sticker is not None:
            if not isinstance(sticker, SignalSticker):
                logger.critical("Raising TypeError:")
                __type_error__("sticker", "SignalSticker", sticker)

        # Validate preview:
        preview_list: list[SignalPreview] = []
        if previews is not None:
            if not isinstance(previews, Iterable):
                logger.critical("Raising TypeError:")
                __type_error__("previews", "Optional[Iterable[SignalPreview]]", previews)
            for i, preview in enumerate(previews):
                if not isinstance(preview, SignalPreview):
                    __type_error__(f'previews[{i}]', 'SignalPreview', preview)
                if body.find(preview.url) == -1:
                    error_message: str = (f"preview URL: '{preview.url}' must appear in the "
                                          f"body of message.")
                    logger.critical("Raising ValueError(%s).", error_message)
                    raise ValueError(error_message)
                preview_list.append(preview)

        # Validate conflicting options:
        if sticker is not None:
            if body is not None or attachments is not None:
                error_message: str = "If body or attachments are defined, sticker must be None."
                logger.critical("Raising ParameterError(%s).", error_message)
                raise ParameterError(error_message)
            if mentions is not None:
                error_message: str = "If sticker is defined, mentions must be None"
                logger.critical("Raising ParameterError(%s).", error_message)
                raise ParameterError(error_message)
            if quote is not None:
                error_message: str = "If sticker is defined, quote must be None"
                logger.critical("Raising ParameterError(%s).", error_message)
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
            error_message: str = (
                "'recipient_type' (which might be None) must be either 'contact' or 'group', "
                "we should never get here.")
            logger.critical("Raising ValueError(%s).", error_message)
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

        # Add previews:
        if previews is not None:
            preview_list: list[dict[str, Any]] = []
            for preview in previews:
                preview_dict: dict[str, Any] = {
                    'previewUrl': preview.url,
                    'previewTitle': preview.title,
                    'previewDescription': preview.description,
                }
                if preview.image is not None:
                    preview_dict['previewImage'] = preview.image.local_path
                preview_list.append(preview_dict)
            send_command_obj['params']['previews'] = preview_list

        # Create json command string:
        json_command_str = json.dumps(send_command_obj) + '\n'

        # Mark system as sending:
        self._sending = True
        # Create socket:
        sock = __socket_create__()
        __socket_connect__(sock)
        # Communicate with signal:
        __socket_send__(sock, json_command_str)
        response_str = __socket_receive_blocking__(sock)
        __socket_close__(sock)
        # Mark system as finished sending
        self._sending = False

        # Parse response and check for error:
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        # TODO: Check if there are other errors somehow.
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])

        # Check for error:
        if error_occurred:
            return_value: list[tuple[bool, SignalContact | SignalGroup, str]] = []
            error_message: str = (f"signal error while sending message: "
                                  f"Code: {signal_code}, Message: {signal_message}")
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
        timestamp = SignalTimestamp(timestamp=response_obj['result']['timestamp'])

        # Parse results:
        return_value: list[tuple[bool, SignalContact | SignalGroup, SignalSentMessage]] = []
        if recipient_type == RecipientTypes.GROUP:
            sent_messages: list[SignalSentMessage] = []
            for recipient in target_recipients:
                sent_message = SignalSentMessage(command_socket=self._command_socket,
                                                 account_id=self._account_id,
                                                 config_path=self._config_path,
                                                 contacts=self._contacts,
                                                 groups=self._groups, devices=self._devices,
                                                 this_device=self._this_device,
                                                 sticker_packs=self._sticker_packs,
                                                 recipient=recipient, timestamp=timestamp,
                                                 body=body,
                                                 attachments=target_attachments,
                                                 mentions=target_mentions, quote=quote,
                                                 sticker=sticker, is_sent=True,
                                                 sent_to=target_recipients,
                                                 previews=previews, expiration=recipient.expiration)
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

        if recipient_type == RecipientTypes.CONTACT:
            for result in results_list:
                # Gather contact:
                contact_id = result['recipientAddress']['number']
                if contact_id is None or contact_id == '':
                    contact_id = result['recipientAddress']['uuid']
                _, contact = self._contacts.__get_or_add__(contact_id=contact_id)

                # Message Sent successfully:
                if result['type'] == 'SUCCESS':

                    # Create a sent message
                    sent_message = SignalSentMessage(command_socket=self._command_socket,
                                                     account_id=self._account_id,
                                                     config_path=self._config_path,
                                                     contacts=self._contacts,
                                                     groups=self._groups, devices=self._devices,
                                                     this_device=self._this_device,
                                                     sticker_packs=self._sticker_packs,
                                                     recipient=contact, timestamp=timestamp,
                                                     body=body,
                                                     attachments=target_attachments,
                                                     mentions=target_mentions,
                                                     quote=quote, sticker=sticker, is_sent=True,
                                                     sent_to=target_recipients, previews=previews,
                                                     expiration=contact.expiration)
                    return_value.append((True, contact, sent_message))
                    if sent_message.recipient == self._contacts.get_self():
                        sent_message.mark_delivered(sent_message.timestamp)
                    self.append(sent_message)
                    self.__save__()
                # Message failed to send:
                else:
                    return_value.append((False, contact, result['type']))
            return tuple(return_value)
        return tuple(return_value)

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

    @property
    def num_received_unread(self) -> int:
        """
        Return the number of unread received messages
        :return: int
        """
        return len(self.get_received_unread())

    @property
    def num_sent_unread(self) -> int:
        """
        Return the number of unread sent messages
        :return: int
        """
        return len(self.get_sent_unread())
