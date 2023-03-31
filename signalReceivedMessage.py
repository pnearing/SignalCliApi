#!/usr/bin/env python3
from typing import TypeVar, Optional, Iterable
import socket
import json
import sys
from datetime import timedelta, datetime
import pytz

from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMention import Mention
from .signalMentions import Mentions
from .signalMessage import Message
from .signalPreview import Preview
from .signalQuote import Quote
from .signalReaction import Reaction
from .signalReactions import Reactions
from .signalSticker import Sticker, StickerPacks
from .signalTimestamp import Timestamp

DEBUG: bool = False

Self = TypeVar("Self", bound="ReceivedMessage")


class ReceivedMessage(Message):
    """Class to store a message that has been received."""

    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 sticker_packs: StickerPacks,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 is_delivered: bool = False,
                 time_delivered: Optional[Timestamp] = None,
                 is_read: bool = False,
                 time_read: Optional[Timestamp] = None,
                 is_viewed: bool = False,
                 time_viewed: Optional[Timestamp] = None,
                 body: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mention] = None,
                 reactions: Optional[Iterable[Reaction]] | Reactions | Reaction = None,
                 sticker: Optional[Sticker] = None,
                 quote: Optional[Quote] = None,
                 expiration: Optional[timedelta] = None,
                 expiration_timestamp: Optional[Timestamp] = None,
                 isExpired: bool = False,
                 previews: Optional[Iterable[Preview] | Preview] = None,
                 ) -> None:
        # Check sticker packs:
        if not isinstance(sticker_packs, StickerPacks):
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        # Check Body:
        if body is not None and not isinstance(body, str):
            __type_error__("body", "Optional[str]", body)
        # Check attachments:
        attachment_list: list[Attachment] = []
        if attachments is not None:
            if isinstance(attachments, Attachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, Attachment):
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachment_list.append(attachment)
            else:
                __type_error__("attachments", "Optional[Iterable[Attachment] | Attachment", attachments)
        # Check mentions:
        mentions_list: list[Mention] = []
        if mentions is not None:
            if isinstance(mentions, Mention):
                mentions_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, Mention):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentions_list.append(mention)
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
        # Check reactions:
        reaction_list: list[Reaction] = []
        if reactions is not None:
            if isinstance(reactions, Reactions):
                pass
            elif isinstance(reactions, Reaction):
                reaction_list.append(reactions)
            elif isinstance(reactions, Iterable):
                for i, reaction in enumerate(reactions):
                    if not isinstance(reaction, Reaction):
                        __type_error__('reactions[%i]' % i, "Reaction", reaction)
                    reaction_list.append(reaction)
            else:
                __type_error__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction]", reactions)
        # Check sticker:
        if sticker is not None and not isinstance(sticker, Sticker):
            __type_error__("sticker", "Sticker", sticker)
        # Check quote:
        if quote is not None and not isinstance(quote, Quote):
            __type_error__("quote", "Quote", quote)
        # Check expiry:
        if expiration is not None:
            if not isinstance(expiration, timedelta):
                __type_error__("expiry", "timedelta", expiration)
        if expiration_timestamp is not None:
            if not isinstance(expiration_timestamp, Timestamp):
                __type_error__("expiration_timestamp", "Timestamp", expiration_timestamp)
        if not isinstance(isExpired, bool):
            __type_error__("is_expired", "bool", isExpired)
        # Check preview:
        preview_list: list[Preview] = []
        if previews is not None:
            if isinstance(previews, Preview):
                preview_list.append(previews)
            elif isinstance(previews, Iterable):
                for i, preview in enumerate(previews):
                    if not isinstance(preview, Preview):
                        __type_error__("previews[%i]" % i, "Preview", preview)
                    preview_list.append(preview)
            else:
                __type_error__("previews", "Iterable[Preview] | Preview", previews)

        # Set internal vars:
        self._sticker_packs: StickerPacks = sticker_packs
        # Set external properties:
        # Set body:
        self.body: Optional[str] = body
        # Set Attachments:
        self.attachments: Optional[list[Attachment]]
        if len(attachment_list) == 0:
            self.attachments = None
        else:
            self.attachments = attachment_list
        # Set mentions:
        self.mentions: Mentions
        if len(mentions_list) == 0:
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentions_list)
        # Set reactions:
        self.reactions: Reactions
        if isinstance(reactions, Reactions):
            self.reactions = reactions
        if len(reaction_list) == 0:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id, contacts=contacts,
                                       groups=groups, devices=devices, this_device=this_device)
        else:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id, contacts=contacts,
                                       groups=groups, devices=devices, this_device=this_device,
                                       reactions=reaction_list)
        # Set sticker:
        self.sticker: Optional[Sticker] = sticker
        # Set quote:
        self.quote: Optional[Quote] = quote
        # Set expiry:
        self.expiration: Optional[timedelta] = expiration
        self.expiration_timestamp: Optional[Timestamp] = expiration_timestamp
        self.is_expired: bool = isExpired
        # Set preview:
        self.previews: Optional[list[Preview]] = preview_list
        # Continue Init:
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_RECEIVED_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
        # Mark this as delivered:
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)
        # Check if this is expired:
        self.__check_expired__()
        # Check if this is a group invite, it'll be a group message with no: body, attachment, sticker etc.
        self.is_group_invite = self.__check_invite__()
        if self.is_group_invite:
            self.body = "Group invite from: %s<%s>" % (self.sender.get_display_name(), self.sender.get_id())

        return

    ######################
    # Init:
    ######################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        print("ReceivedMessage.__from_raw_message__")
        print(raw_message)
        data_message: dict[str, object] = raw_message['dataMessage']
        # Parse body:
        self.body = data_message['message']
        # Parse expiry
        if data_message['expiresInSeconds'] == 0:
            self.expiration = None
        else:
            self.expiration = timedelta(seconds=data_message["expiresInSeconds"])
        # Parse attachments:
        if 'attachments' in data_message.keys():
            # print("DEBUG: %s: Started attachment decoding." % __name__)
            self.attachments = []
            for raw_attachment in data_message['attachments']:
                attachment = Attachment(config_path=self._config_path, raw_attachment=raw_attachment)
                self.attachments.append(attachment)
        # Parse mentions:
        if 'mentions' in data_message.keys():
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=data_message['mentions'])
        # Parse sticker:
        if 'sticker' in data_message.keys():
            stickerDict: dict[str, object] = data_message['sticker']
            self._sticker_packs.__update__()  # Update in case this is a new sticker.
            self.sticker = self._sticker_packs.get_sticker(pack_id=stickerDict['pack_id'],
                                                           sticker_id=stickerDict['sticker_id'])
        # Parse Quote
        if 'quote' in data_message.keys():
            if self.recipient_type == 'group':
                self.quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                   raw_quote=data_message['quote'], conversation=self.recipient)
            elif self.recipient_type == 'contact':
                self.quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                   raw_quote=data_message['quote'], conversation=self.sender)
        # Parse preview:
        self.previews = []
        if 'previews' in data_message.keys():
            for rawPreview in data_message['previews']:
                preview = Preview(config_path=self._config_path, raw_preview=rawPreview)
                self.previews.append(preview)

        return

    #####################
    # To / From Dict:
    #####################
    def __to_dict__(self) -> dict:
        received_message_dict = super().__to_dict__()
        # Set body:
        received_message_dict['body'] = self.body
        # Set attachments
        received_message_dict['attachments'] = None
        if self.attachments is not None:
            received_message_dict["attachments"] = []
            for attachment in self.attachments:
                received_message_dict["attachments"].append(attachment.__to_dict__())
        # Set mentions:
        received_message_dict['mentions'] = self.mentions.__to_dict__()
        # Set reactions:
        # receivedMessageDict['reactions'] = None
        # if (self.reactions != None):
        received_message_dict['reactions'] = self.reactions.__to_dict__()
        # Set sticker:
        received_message_dict['sticker'] = None
        if self.sticker is not None:
            received_message_dict['sticker'] = {
                'pack_id': self.sticker._pack_id,
                'sticker_id': self.sticker.id
            }
        # Set quote:
        received_message_dict['quote'] = None
        if self.quote is not None:
            received_message_dict['quote'] = self.quote.__to_dict__()
        # Set expiration:
        received_message_dict['is_expired'] = self.is_expired
        received_message_dict['expiration'] = None
        received_message_dict['expiration_timestamp'] = None
        if self.expiration is not None:
            received_message_dict['expiration'] = self.expiration.seconds
        if self.expiration_timestamp is not None:
            received_message_dict['expiration_timestamp'] = self.expiration_timestamp.__to_dict__()
        # Set previews:
        received_message_dict['previews'] = []
        for preview in self.previews:
            received_message_dict['previews'].append(preview.__to_dict__())
        return received_message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Load body:
        self.body = from_dict['body']
        # Load attachments:
        self.attachments = None
        if from_dict['attachments'] is not None:
            self.attachments = []
            for attachment_dict in from_dict['attachments']:
                attachment = Attachment(config_path=self._config_path, from_dict=attachment_dict)
                self.attachments.append(attachment)
        # Load mentions:
        self.mentions = Mentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Load reactions:
        # self.reactions = None
        # if (from_dict['reactions'] != None):
        self.reactions = Reactions(command_socket=self._command_socket, account_id=self._account_id,
                                   contacts=self._contacts, groups=self._groups, devices=self._devices,
                                   from_dict=from_dict['reactions'])
        # Load sticker:
        self.sticker = None
        if from_dict['sticker'] is not None:
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=from_dict['sticker']['pack_id'],
                sticker_id=from_dict['sticker']['sticker_id']
            )
        # Load quote
        self.quote = None
        if from_dict['quote'] is not None:
            self.quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                               from_dict=from_dict['quote'])
        # Load expiration:
        self.is_expired = from_dict['is_expired']
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.expiration_timestamp = None
        if from_dict['expiration_timestamp'] is not None:
            self.expiration_timestamp = Timestamp(from_dict=from_dict['expiration_timestamp'])
        # Load previews:
        self.previews = []
        for preview_dict in from_dict['previews']:
            self.previews.append(Preview(config_path=self._config_path, from_dict=preview_dict))
        return

    #####################
    # Helpers:
    #####################
    def __send_receipt__(self, receipt_type: str) -> Timestamp:
        # Create send receipt command object and json command string.
        send_receipt_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "send_receipt",
            "params": {
                "account": self._account_id,
                "recipient": self.sender.get_id(),
                "type": receipt_type,
                "target_timestamp": self.timestamp.timestamp,
            }
        }
        json_command_str = json.dumps(send_receipt_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str = __socket_receive__(self._command_socket)
        # Parse Response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "signal error while sending receipt. Code: %i Message: %s" % (response_obj['error']['code'],
                                                                                          response_obj["error"][
                                                                                              'message'])
            raise RuntimeError(error_message)
        # Result is a dict:
        # print(responseObj)
        when = Timestamp(timestamp=response_obj['result']['timestamp'])
        # Parse results:
        for result in response_obj['result']['results']:
            if result['type'] != 'SUCCESS':
                if DEBUG:
                    error_message = "in send receipt, result type not SUCCESS: %s" % result['type']
                    print(error_message, file=sys.stderr)
            else:
                if result['recipientAddress']['number'] is not None:
                    added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                   result['recipientAddress']['number'])
                else:
                    added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                   result['recipientAddress']['uuid'])
                contact.seen(when)
        return when

    def __set_expiry__(self, time_opened: Timestamp):
        if self.expiration is not None:
            expiryDateTime = time_opened.date_time + self.expiration
            self.expiration_timestamp = Timestamp(date_time=expiryDateTime)
        return

    def __check_expired__(self) -> bool:
        """
        Check and set is_expired.
        :returns: bool: True if this run has set the expired flag.
        """
        if self.expiration is None:
            return False
        if self.expiration_timestamp is not None:
            now = datetime.now(tz=pytz.UTC)
            if self.expiration_timestamp.get_datetime() <= now:
                self.is_expired = True
                return True
        return False

    def __check_invite__(self) -> bool:
        """
        Check if this is a group invite, it's an invitation if it's a group message without a body, a sticker, etc.
        :returns: bool: True if this is an invitation.
        """
        if self.recipient_type != 'group':
            return False
        if self.body is not None:
            return False
        if self.attachments is not None:
            return False
        if len(self.mentions) != 0:
            return False
        if self.sticker is not None:
            return False
        if self.quote is not None:
            return False
        return True
    #####################
    # Methods:
    #####################
    def mark_delivered(self, when: Timestamp) -> None:
        """
        Mark message as delivered.
        :param when: Timestamp: When the message was delivered.
        :returns: None
        :raises: TypeError: If when is not a Timestamp object, raised by super()
        """
        return super().mark_delivered(when)

    def mark_read(self, when: Timestamp = None, send_receipt: bool = True) -> None:
        """
        Mark message as read.
        :param when: Timestamp: When the message was read.
        :param send_receipt: bool: Send the read receipt.
        :returns: None
        :raises: TypeError: If when not a Timestamp object, raised by super(), or if send_receipt is not a bool.
        """
        if not isinstance(send_receipt, bool):
            __type_error__("send_receipt", "bool", send_receipt)
        if send_receipt:
            when = self.__send_receipt__('read')
        elif when is None:
            when = Timestamp(now=True)
        self.__set_expiry__(when)
        return super().mark_read(when)

    def mark_viewed(self, when: Timestamp = None, send_receipt: bool = True) -> None:
        """
        Mark message as viewed.
        :param when: Timestamp: When the message was viewed.
        :param send_receipt: bool: Send a viewed receipt.
        :returns: None
        :raises: TypeError: If when not a Timestamp object, raised by super(), or if send_receipt is not a bool.
        """
        if not isinstance(send_receipt, bool):
            __type_error__("send_receipt", "bool", send_receipt)
        if send_receipt:
            when = self.__send_receipt__('viewed')
        elif when is None:
            when = Timestamp(now=True)
        self.__set_expiry__(when)
        return super().mark_viewed(when)

    def get_quote(self) -> Quote:
        """
        Get a quote object for this message.
        :returns: Quote: This message as a quote.
        """
        quote: Quote
        if self.recipient_type == 'contact':
            quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.sender)
        elif self.recipient_type == 'group':
            quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.recipient)
        else:
            raise ValueError("invalid recipient_type in ReceivedMessage.get_quote")
        return quote

    def parse_mentions(self) -> Optional[str]:
        """
        Parse the mentions.
        :returns: Optional[str]: The body with the mentions inserted, or None if body is None.
        """
        if self.body is not None:
            return self.mentions.__parse_mentions__(self.body)
        return None

    def react(self, emoji: str) -> tuple[bool, Reaction | str]:
        """
        Create and send a Reaction to this message.
        :param emoji: str: The emoji to react with.
        :returns: tuple[bool, Reaction | str]: Returns a tuple, the bool is True if reaction sent successfully, and
                                                False if not.  If sent, the second element of the tuple will be the
                                                Reaction object, otherwise, if not sent, the second element contains an
                                                error message.
        :raises: TypeError: If emoji is not a string.
        :raises: ValueError: If emoji length is not one or two characters.
        """
        # Argument check:
        if not isinstance(emoji, str):
            __type_error__('emoji', "str, len = 1|2", emoji)
        if len(emoji) != 1 and len(emoji) != 2:
            errorMessage = "emoji must be str of len 1|2"
            raise ValueError(errorMessage)
        # Create reaction
        if self.recipient_type == 'contact':
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.sender, emoji=emoji,
                                target_author=self.sender,
                                target_timestamp=self.timestamp)
        elif self.recipient_type == 'group':
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.recipient, emoji=emoji,
                                target_author=self.sender, target_timestamp=self.timestamp)
        else:
            errorMessage = "Invalid recipient type."
            return False, errorMessage
        # Send reaction:
        sent, message = reaction.send()
        if not sent:
            return False, message
        # Parse reaction:
        self.reactions.__parse__(reaction)
        return True, reaction

    # TODO: Reply to this message, create a sent message with this as an attached quote.
