#!/usr/bin/env python3

from typing import Optional, Iterable, Tuple
import sys
import os
import socket
import json
from syslog import syslog, LOG_INFO
from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive__, __socket_send__
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

DEBUG: bool = False


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
        # Argument checks:
        if not isinstance(command_socket, socket.socket):
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            __type_error__("account_id", "str", account_id)
        if not isinstance(contacts, Contacts):
            __type_error__("contacts", "Contacts", contacts)
        if not isinstance(devices, Devices):
            __type_error__("devices", "Devices", devices)
        if not isinstance(this_device, Device):
            __type_error__("this_devices", "Device", this_device)
        if not isinstance(sticker_packs, StickerPacks):
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Set internal vars:
        self._command_socket: socket.socket = command_socket
        self._config_path: str = config_path
        self._account_id: str = account_id
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Devices = devices
        self._this_device: Device = this_device
        self._sticker_packs: StickerPacks = sticker_packs
        self._file_path: str = os.path.join(account_path, "messages.json")
        # Set external properties:
        self.messages: list[SentMessage | ReceivedMessage] = []
        self.sync: list[GroupUpdate | SyncMessage] = []
        self.typing: list[TypingMessage] = []
        self.story: list[StoryMessage] = []
        # self.calls: list[]
        self._sending: bool = False
        # Do load:
        if do_load:
            try:
                self.__load__()
            except RuntimeError:
                if DEBUG:
                    errorMessage = "warning, creating empy messages: %s" % self._file_path
                    print(errorMessage, file=sys.stderr)
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
    def __to_dict__(self) -> dict:
        messages_dict = {
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

    def __from_dict__(self, fromDict: dict) -> None:
        # Load messages: SentMessage | ReceivedMessage
        self.messages = []
        for message_dict in fromDict['messages']:
            if message_dict['message_type'] == Message.TYPE_SENT_MESSAGE:
                message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      sticker_packs=self._sticker_packs,
                                      from_dict=message_dict)

            elif message_dict['message_type'] == Message.TYPE_RECEIVED_MESSAGE:
                message = ReceivedMessage(command_socket=self._command_socket, account_id=self._account_id,
                                          config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                          devices=self._devices, this_device=self._this_device,
                                          sticker_packs=self._sticker_packs, from_dict=message_dict)
            else:
                error_message = "FATAL: Invalid message type in messages from_dict: %s" % fromDict['message_type']
                raise RuntimeError(error_message)
            self.messages.append(message)
        # Load sync messages: GroupUpdate | SyncMessage
        self.sync = []
        for message_dict in fromDict['syncMessages']:
            if message_dict['message_type'] == Message.TYPE_GROUP_UPDATE_MESSAGE:
                message = GroupUpdate(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device, from_dict=message_dict)
            elif message_dict['message_type'] == Message.TYPE_SYNC_MESSAGE:
                message = SyncMessage(command_socket=self._command_socket, account_id=self._account_id,
                                      config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      sticker_packs=self._sticker_packs, from_dict=message_dict)
            else:
                error_message = "FATAL: Invalid message type in for sync messages in Messages.__from_dict__"
                raise RuntimeError(error_message)
            self.sync.append(message)
        # Load typing messages:
        self.typing = []
        for message_dict in fromDict['typingMessages']:
            message = TypingMessage(command_socket=self._command_socket, account_id=self._account_id,
                                    config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                    devices=self._devices, this_device=self._this_device, from_dict=message_dict)
            self.typing.append(message)
        # Load Story Messages:
        self.story = []
        for message_dict in fromDict['storyMessages']:
            message = StoryMessage(command_socket=self._command_socket, account_id=self._account_id,
                                   config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                   devices=self._devices, this_device=self._this_device, from_dict=message_dict)
            self.story.append(message)
        return

    #################################
    # Load / save:
    #################################
    def __load__(self) -> None:
        # Try to open the file:
        try:
            file_handle = open(self._file_path, 'r')
        except Exception as e:
            error_message = "FATAL: Couldn't open '%s' for reading: %s" % (self._file_path, str(e.args))
            raise RuntimeError(error_message)
        # Try to load the json from the file:
        try:
            messages_dict: dict = json.loads(file_handle.read())
        except json.JSONDecodeError as e:
            error_message = "FATAL: Couldn't load json from '%s': %s" % (self._file_path, e.msg)
            raise RuntimeError(error_message)
        # Load the dict:
        self.__from_dict__(messages_dict)
        return

    def __save__(self) -> None:
        # Create messages Object, and json save string:
        messages_dict = self.__to_dict__()
        json_messages_str = json.dumps(messages_dict, indent=4)
        # Try to open the file for writing:
        try:
            file_handle = open(self._file_path, 'w')
        except Exception as e:
            error_message = "FATAL: Failed to open '%s' for writing: %s" % (self._file_path, str(e.args))
            raise RuntimeError(error_message)
        # Write to the file and close it.
        file_handle.write(json_messages_str)
        file_handle.close()
        return

    ##################################
    # Helpers:
    ##################################
    def __parse_reaction__(self, reaction: Reaction) -> bool:
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
            raise RuntimeError(error_message)
        # Find the message that was reacted to:
        reactedMessage: Optional[SentMessage | ReceivedMessage | Message] = None
        for message in search_messages:
            if message.sender == reaction.target_author:
                if message.timestamp == reaction.target_timestamp:
                    reactedMessage = message
        # If the message isn't in history do nothing:
        if reactedMessage is None:
            return False
        # Have the message add / change / remove the reaction:
        reactedMessage.reactions.__parse__(reaction)
        return True

    def __parse_receipt__(self, receipt: Receipt) -> None:
        sentMessages = [message for message in self.messages if isinstance(message, SentMessage)]
        for message in sentMessages:
            for timestamp in receipt.timestamps:
                if message.timestamp == timestamp:
                    message.__parse_receipt__(receipt)
                    self.__save__()
        return

    def __parse_read_message_sync__(self, sync_message: SyncMessage) -> None:
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
        message = SentMessage(command_socket=self._command_socket, account_id=self._account_id,
                              config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, sticker_packs=self._sticker_packs,
                              raw_message=sync_message.raw_sent_message)
        self.append(message)
        return

    def __parse_sync_message__(self, sync_message: SyncMessage) -> None:
        if sync_message.sync_type == SyncMessage.TYPE_READ_MESSAGE_SYNC:
            self.__parse_read_message_sync__(sync_message)
        elif sync_message.sync_type == SyncMessage.TYPE_SENT_MESSAGE_SYNC:
            self.__parse_sent_message_sync__(sync_message)
        else:
            error_message = "Can only parse SyncMessage.TYPE_READ_MESSAGE_SYNC"
            error_message += " and SyncMessage.TYPE_SENT_MESSAGE_SYNC not: %i" % sync_message.sync_type
            raise TypeError(error_message)
        self.__save__()
        return

    def __check_expiries__(self) -> None:
        for message in self.messages:
            message.__check_expired__()
        return

    def __do_expunge__(self) -> None:
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
        if not isinstance(timestamp, Timestamp):
            __type_error__("timestamp", "Timestamp", timestamp)
        return [message for message in self.messages if message.timestamp == timestamp]

    def get_by_recipient(self, recipient: Group | Contact) -> list[Message]:
        """
        Get messages given a recipient.
        :param recipient: Group | Contact: The recipient to search for.
        :raises: TypeError: If recipient is not a Contact or o Group object.
        """
        if not isinstance(recipient, Contact) and not isinstance(recipient, Group):
            __type_error__("recipient", "Contact | Group", recipient)
        return [message for message in self.messages if message.recipient == recipient]

    def get_by_sender(self, sender: Contact) -> list[Message]:
        """
        Get messages given a sender.
        :param sender: Contact: The sender to search for.
        :raises: TypeError if sender is not a Contact object.
        """
        if not isinstance(sender, Contact):
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
        returnMessages = []
        if isinstance(target, Contact):
            selfContact = self._contacts.get_self()
            for message in self.messages:
                if message.sender == selfContact and message.recipient == target:
                    returnMessages.append(message)
                elif message.sender == target and message.recipient == selfContact:
                    returnMessages.append(message)
        elif isinstance(target, Group):
            for message in self.messages:
                if message.recipient == target:
                    returnMessages.append(message)
        else:
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
        :param conversation: Contact | Group: The conversation the message is in.
        :returns: SentMessage | ReceivedMessage: The message found, or None if not found.
        :raises: TypeError: If author is not a Contact object, if timestamp is not a Timestamp object, or if
                                conversation os not a Contact or Group object.
        """
        # Validate  author:
        target_author: Optional[Contact] = None
        if isinstance(author, Contact):
            target_author = author
        else:
            __type_error__("author", "Contact", author)
        # Validate recipient:
        target_conversation: Optional[Contact | Group] = None
        if isinstance(conversation, Contact):
            target_conversation = conversation
        elif isinstance(conversation, Group):
            target_conversation = conversation
        else:
            __type_error__("recipient", "Contact | Group", conversation)
        # Validate timestamp:
        targetTimestamp: Optional[Timestamp] = None
        if isinstance(timestamp, Timestamp):
            targetTimestamp = timestamp
        else:
            __type_error__("timestamp", "Timestamp", timestamp)
        # Find Message:
        searchMessages = self.get_conversation(target_conversation)
        for message in searchMessages:
            if message.sender == target_author and message.timestamp == targetTimestamp:
                return message
        return None

    def get_quoted(self, quote: Quote) -> Optional[SentMessage | ReceivedMessage | Message]:
        """
        Get a message that contains a given Quote.
        :param quote: Quote: The quote we're looking for.
        :returns: SentMessage | ReceivedMessage: The message that contains the quote, or None if not found.
        :raises: TypeError: If quote is not a Quote object.
        """
        if not isinstance(quote, Quote):
            __type_error__("quote", "Quote", quote)
        searchMessages = self.get_conversation(quote.conversation)
        for message in searchMessages:
            if message.sender == quote.author:
                if message.timestamp == quote.timestamp:
                    return message
        return None

    def get_sent(self) -> list[SentMessage]:
        """
        Returns all messages that are SentMessage objects.
        """
        return [message for message in self.messages if isinstance(message, SentMessage)]

    ##################################
    # Methods:
    ##################################
    def append(self, message: Message) -> None:
        """
        Append a message.
        :param message: Message: The message to append.
        :returns: None
        :raises TypeError: If message is not a Message.
        """
        if not isinstance(message, Message):
            __type_error__("message", "Message", message)
        # if message is None:
        #     if DEBUG:
        #         print("ATTEMPTING TO APPEND NONE TYPE to messages", file=sys.stderr)
        #     raise RuntimeError()
        #     return
        if isinstance(message, SentMessage) or isinstance(message, ReceivedMessage):
            self.messages.append(message)
        elif isinstance(message, GroupUpdate) or isinstance(message, SyncMessage):
            self.sync.append(message)
        elif isinstance(message, TypingMessage):
            self.typing.append(message)

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
                     ) -> tuple[
        tuple[bool, Contact, str] | tuple[bool, Contact | Group, str] | tuple[bool, Contact, SentMessage] | tuple[
            bool, Contact, object], ...]:
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
        :returns: tuple[tuple[bool, Contact | Group, str | SentMessage]]: True / False for message sent successfully,
                                                                            Contact | Group the message was sent to,
                                                                            str | SentMessage, a string containing an
                                                                            error message or the SentMessage object.
        :raises: TypeError: If a recipient is not a Contact or Group object, if body is not a string, if attachments is
                                not an Attachment object or a string, or a list of Attachment objects, or strings, if
                                mentions is not a list of Mention objects, or not a Mentions object, if quote is not a
                                Quote object, if sticker is not a Sticker object, or if preview is not a Preview object.
        :raises: ValueError: If body is an empty string, if attachments is an empty list, or if mentions is an empty
                                list.
        """
        # Validate recipients:
        recipient_type: str = ''
        target_recipients: list[Contact | Group] = []
        if isinstance(recipients, Contact):
            recipient_type = 'contact'
            target_recipients = [recipients]
        elif isinstance(recipients, Group):
            recipient_type = 'group'
            target_recipients = [recipients]
        elif isinstance(recipients, Iterable):
            target_recipients = []
            checkType = None
            for i, recipient in enumerate(recipients):
                if not isinstance(recipient, Contact) and not isinstance(recipient, Group):
                    __type_error__("recipients[%i]" % i, "Contact | Group", recipient)
                if i == 0:
                    checkType = type(recipient)
                    if isinstance(recipient, Contact):
                        recipient_type = 'contact'
                    else:
                        recipient_type = 'group'
                elif not isinstance(recipient, checkType):
                    __type_error__("recipients[%i]", str(type(checkType)), recipient)
                target_recipients.append(recipient)
        else:
            __type_error__("recipients", "Iterable[Contact | Group] | Contact | Group", recipients)
        if len(target_recipients) == 0:
            raise ValueError("recipients cannot be of zero length")
        # Validate body Type and value:
        if body is not None and not isinstance(body, str):
            __type_error__("body", "str | None", body)
        elif body is not None and len(body) == 0:
            raise ValueError("body cannot be empty string")
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
                    if not isinstance(attachment, Attachment) and not isinstance(attachment, str):
                        __type_error__("attachments[%i]" % i, "Attachment | str", attachment)
                    if isinstance(attachment, Attachment):
                        target_attachments.append(attachment)
                    else:
                        target_attachments.append(Attachment(config_path=self._config_path, local_path=attachment))
            else:
                __type_error__("attachments", "Iterable[Attachment | str] | Attachment | str", attachments)
        if target_attachments is not None and len(target_attachments) == 0:
            raise ValueError("attachments cannot be empty")
        # Validate mentions:
        target_mentions: Optional[list[Mention] | Mentions] = None
        if mentions is not None:
            if isinstance(mentions, Mentions):
                target_mentions = mentions
            elif isinstance(mentions, Mention):
                target_mentions = [mentions]
            elif isinstance(mentions, Iterable):
                target_mentions = []
                i = 0
                for mention in mentions:
                    if not isinstance(mention, Mention):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    target_mentions.append(mention)
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
        if target_mentions is not None and len(target_mentions) == 0:
            raise ValueError("mentions cannot be empty")
        # Validate quote:
        if quote is not None and not isinstance(quote, Quote):
            __type_error__("quote", "SentMessage | ReceivedMessage", quote)
        # Validate sticker:
        if sticker is not None:
            if not isinstance(sticker, Sticker):
                raise __type_error__("sticker", "Sticker", sticker)
        # Validate preview:
        if preview is not None:
            if not isinstance(preview, Preview):
                __type_error__("preview", "Preview", preview)
            if body.find(preview.url) == -1:
                error_message = "FATAL: error while sending message. preview URL must appear in body of message."
                raise ValueError(error_message)
        # Validate conflicting options:
        if sticker is not None:
            if body is not None or attachments is not None:
                error_message = "If body or attachments are defined, sticker must be None."
                raise ValueError(error_message)
            if mentions is not None:
                error_message = "If sticker is defined, mentions must be None"
                raise ValueError(error_message)
            if quote is not None:
                error_message = "If sticker is defined, quote must be None"
                raise ValueError(error_message)
        # Create send message command object:
        send_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "send",
            "params": {
                "account": self._account_id,
            }
        }
        # Add recipients:
        if recipient_type == 'group':
            send_command_obj['params']['groupId'] = []
            for group in target_recipients:
                send_command_obj['params']['groupId'].append(group.get_id())
        elif recipient_type == 'contact':
            send_command_obj['params']['recipient'] = []
            for contact in target_recipients:
                send_command_obj['params']['recipient'].append(contact.get_id())
        else:
            raise ValueError("recipient_type must be either 'contact' or 'group'")
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
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Mark system as finished sending
        self._sending = False
        #***********************DEBUG:**************************************
        debug_message = "DEBUG: response_obj = '%s'" % str(response_obj)
        syslog(LOG_INFO, debug_message)
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "ERROR: failed to send message, signal error. Code: %i Message: %s" % (
                response_obj['error']['code'],
                response_obj['error']['message'])
            if DEBUG:
                print(error_message, file=sys.stderr)
            return_value = []
            for recipient in target_recipients:
                if recipient_type == 'group':
                    for member in recipient.members:
                        return_value.append((False, member, error_message))
                else:
                    return_value.append((False, recipient, error_message))
            return_value = tuple(return_value)
            return return_value
        # Some messages sent, some may have failed.
        results_list: list[dict[str, object]] = response_obj['result']['results']
        # Gather timestamp:
        timestamp = Timestamp(timestamp=response_obj['result']['timestamp'])
        # Parse results:
        return_value = []
        if recipient_type == 'group':
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
                # Gather group and contact:
                group_id = result['groupId']
                added, group = self._groups.__get_or_add__("<UNKNOWN-GROUP>", group_id)
                contact_id = result['recipientAddress']['number']
                if contact_id is None:
                    contact_id = result['recipientAddress']['uuid']
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id)
                # Message sent successfully
                if result['type'] == "SUCCESS":
                    for message in sent_messages:
                        if message.recipient == group:
                            message.sent_to.append(contact)
                            return_value.append((True, contact, message))
                # Message failed to send:
                else:
                    return_value.append((False, contact, result['type']))
            self._sending = False
            return tuple(return_value)
        # Recipient type == Contact
        else:
            for result in results_list:
                # Gather contact:
                contact_id = result['recipientAddress']['number']
                if contact_id is None or contact_id == '':
                    contact_id = result['recipientAddress']['uuid']
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id)

                # Message Sent successfully:
                if result['type'] == 'SUCCESS':
                    # Create sent message
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
