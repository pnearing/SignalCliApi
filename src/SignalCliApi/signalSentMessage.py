#!/usr/bin/env python3

from typing import TypeVar, Optional, Iterable
import socket
from datetime import timedelta
import json

from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalContacts import Contacts
from .signalContact import Contact
from .signalDevices import Devices
from .signalDevice import Device
from .signalGroups import Groups
from .signalGroup import Group
from .signalMention import Mention
from .signalMentions import Mentions
from .signalMessage import Message
from .signalPreview import Preview
from .signalQuote import Quote
from .signalReaction import Reaction
from .signalReactions import Reactions
from .signalReceipt import Receipt
from .signalSticker import Sticker, StickerPacks
from .signalTimestamp import Timestamp
DEBUG: bool = False
Self = TypeVar("Self", bound="SentMessage")


class SentMessage(Message):
    # noinspection GrazieInspection
    """Class to store a sent message."""
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
                 recipient: Optional[Contact | Group] = None,
                 timestamp: Optional[Timestamp] = None,
                 body: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                 reactions: Optional[Iterable[Reaction]] | Reactions | Reaction = None,
                 sticker: Optional[Sticker] = None,
                 quote: Optional[Quote] = None,
                 expiration: Optional[timedelta] = None,
                 expiration_timestamp: Optional[Timestamp] = None,
                 is_expired: bool = False,
                 is_sent: bool = False,
                 sent_to: Optional[Iterable[Contact] | Contact] = None,
                 preview: Optional[Preview] = None,
                 ) -> None:
        # Check sticker_packs:
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
        mentions_list: list[Mention] | Mentions = []
        if mentions is not None:
            if isinstance(mentions, Mentions):
                mentions_list = None
            elif isinstance(mentions, Mention):
                mentions_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, Mention):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentions_list.append(mention)
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mentions | Mention]", mentions)
        # Check reactions:
        reaction_list: list[Reaction] = []
        if reactions is not None:
            if isinstance(reactions, Reactions):
                reaction_list = None
            if isinstance(reactions, Reaction):
                reaction_list.append(reactions)
            elif isinstance(reactions, Iterable):
                for i, reaction in enumerate(reactions):
                    if not isinstance(reaction, Reaction):
                        __type_error__('reactions[%i]' % i, "Reaction", reaction)
                    reaction_list.append(reaction)
            else:
                __type_error__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction", reactions)
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
        if not isinstance(is_expired, bool):
            __type_error__("is_expired", "bool", is_expired)
        # Check is_sent:
        if not isinstance(is_sent, bool):
            __type_error__("is_sent", "bool", is_sent)
        # Check sent_to: TODO: Sent to I think can be groups too.
        sent_to_list: Optional[list[Contact]] = None
        if sent_to is not None:
            if isinstance(sent_to, Contact):
                sent_to_list = [sent_to]
            elif isinstance(sent_to, Iterable):
                sent_to_list = []
                for i, contact in enumerate(sent_to_list):
                    if not isinstance(contact, Contact):
                        __type_error__("sent_to[%i]" % i, "Contact", contact)
                    sent_to_list.append(contact)
            else:
                __type_error__("sent_to", "Iterable[Contact] | Contact", sent_to)
        # Check previews:
        if preview is not None and not isinstance(preview, Preview):
            __type_error__("preview", "Preview", preview)
        # Set internal vars:
        self._sticker_packs = sticker_packs
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
        if isinstance(mentions, Mentions):
            self.mentions = mentions
        elif len(mentions_list) == 0:
            self.mentions = None
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentions_list)
        # Set reactions:
        self.reactions: Reactions
        if isinstance(reactions, Reactions):
            self.reactions = reactions
        elif len(reaction_list) == 0:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id, contacts=contacts,
                                       groups=groups, devices=devices, this_device=this_device)
        else:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id, contacts=contacts,
                                       groups=groups, devices=devices, reactions=reaction_list)
        # Set sticker:
        self.sticker: Optional[Sticker] = sticker
        # Set quote:
        self.quote: Optional[Quote] = quote
        # Set expiry:
        self.expiration: Optional[timedelta] = expiration
        self.expiration_timestamp: Optional[Timestamp] = expiration_timestamp
        self.is_expired: bool = is_expired
        # Set is sent:
        self.is_sent: bool = is_sent
        # Set sent_to:
        self.sent_to: list[Contact]
        if sent_to_list is None:
            self.sent_to = []
        else:
            self.sent_to = sent_to_list
        # Set delivery_receipts, read_receipts and viewed_receipts:
        self.delivery_receipts: list[Receipt] = []
        self.read_receipts: list[Receipt] = []
        self.viewed_receipts: list[Receipt] = []
        # Set previews:
        self.preview: Preview = preview
        # Continue init:
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, contacts.get_self(), recipient, this_device, timestamp, Message.TYPE_SENT_MESSAGE)
        return

    ##########################
    # Init:
    ##########################
    def __from_raw_message__(self, raw_message: dict) -> None:
        # super().__from_raw_message__(raw_message)
        print("SentMessage.__from_raw_message__")
        print(raw_message)
        raw_sent_message: dict[str, object] = raw_message['sync_message']['sentMessage']
        # Load recipient and recipient type:
        if raw_sent_message['destination'] is not None:
            self.recipient_type = 'contact'
            added, self.recipient = self._contacts.__get_or_add__(name="<UNKNOWN-CONTACT>",
                                                                  number=raw_sent_message['destinationNumber'],
                                                                  uuid=raw_sent_message['destinationUuid'])
        elif 'groupInfo' in raw_sent_message.keys():
            self.recipient_type = 'group'
            added, self.recipient = self._groups.__get_or_add__("<UNKNOWN-GROUP>",
                                                                raw_sent_message['groupInfo']['groupId'])
        # Load timestamp:
        self.timestamp = Timestamp(timestamp=raw_sent_message['timestamp'])
        # Load Device:
        added, self.device = self._devices.__get_or_add__("<UNKNOWN-DEVICE>", raw_message['sourceDevice'])

        # Load body:
        self.body = raw_sent_message['message']
        # Load attachments:
        self.attachments = None
        if 'attachments' in raw_sent_message.keys():
            self.attachments = []
            for raw_attachment in raw_sent_message['attachments']:
                self.attachments.append(Attachment(config_path=self._config_path, raw_attachment=raw_attachment))
        # Load sticker:
        self.sticker = None
        if 'sticker' in raw_sent_message.keys():
            self.sticker = self._sticker_packs.get_sticker(pack_id=raw_sent_message['sticker']['pack_id'],
                                                           sticker_id=raw_sent_message['sticker']['sticker_id'])
        # Load mentions:
        self.mentions = None
        if 'mentions' in raw_sent_message.keys():
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=raw_sent_message['mentions'])
        # Load quote:
        self.quote = None
        if 'quote' in raw_sent_message.keys():
            self.quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                               raw_quote=raw_sent_message['quote'])
        # Load expiry:
        if raw_sent_message['expiresInSeconds'] == 0:
            self.expiration = None
            self.expiration_timestamp = None
            self.is_expired = False
        else:
            self.expiration = timedelta(seconds=raw_sent_message['expiresInSeconds'])
            self.expiration_timestamp = None
            self.is_expired = False
        # Load preview:
        self.preview = None
        if 'preview' in raw_sent_message.keys():
            self.preview = Preview(config_path=self._config_path, raw_preview=raw_sent_message['preview'])
        # Set sent
        self.is_sent = True
        # Set sent to, if a group, assume sent to all current members.
        self.sent_to = []
        if self.recipient_type == 'group':
            for contact in self.recipient.members:
                self.sent_to.append(contact)
        elif self.recipient_type == 'contact':
            self.sent_to = [self.recipient]
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict:
        sent_message_dict = super().__to_dict__()
        # Set body:
        sent_message_dict['body'] = self.body
        # Set attachments:
        sent_message_dict['attachments'] = None
        if self.attachments is not None:
            sent_message_dict["attachments"] = []
            for attachment in self.attachments:
                sent_message_dict["attachments"].append(attachment.__to_dict__())
        # Set Mentions:
        sent_message_dict['mentions'] = None
        if self.mentions is not None:
            sent_message_dict['mentions'] = self.mentions.__to_dict__()
        # Set Reactions:
        sent_message_dict['reactions'] = None
        if self.reactions is not None:
            sent_message_dict['reactions'] = self.reactions.__to_dict__()
        # Set sticker:
        sent_message_dict['sticker'] = None
        if self.sticker is not None:
            sent_message_dict['sticker'] = {
                'packId': self.sticker._pack_id,
                'stickerId': self.sticker.id
            }
        # Set quote:
        sent_message_dict['quote'] = None
        if self.quote is not None:
            sent_message_dict['quote'] = self.quote.__to_dict__()
        # Set expiration:
        sent_message_dict['expiration'] = None
        sent_message_dict['expirationimestamp'] = None
        sent_message_dict['isExpired'] = self.is_expired
        if self.expiration is not None:
            sent_message_dict['expiration'] = self.expiration.seconds
        if self.expiration_timestamp is not None:
            sent_message_dict['expirationTimestamp'] = self.expiration_timestamp.__to_dict__()
        # Set is sent:
        sent_message_dict['isSent'] = self.is_sent
        # Set sent_to list:
        sent_message_dict['sentTo'] = []
        for contact in self.sent_to:
            sent_message_dict['sentTo'].append(contact.get_id())
        # Set delivery_receipts list:
        sent_message_dict['deliveryReceipts'] = []
        for receipt in self.delivery_receipts:
            sent_message_dict['deliveryReceipts'].append(receipt.__to_dict__())
        # Set read_receipts list:
        sent_message_dict['readReceipts'] = []
        for receipt in self.read_receipts:
            sent_message_dict['readReceipts'].append(receipt.__to_dict__())
        # Set viewed_receipts list:
        sent_message_dict['viewedReceipts'] = []
        for receipt in self.viewed_receipts:
            sent_message_dict['viewedReceipts'].append(receipt.__to_dict__())
        return sent_message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Load Body:
        self.body = from_dict['body']
        # Load attachments:
        self.attachments = None
        if from_dict['attachments'] is not None:
            self.attachments = []
            for attachmentDict in from_dict['attachments']:
                attachment = Attachment(config_path=self._config_path, from_dict=attachmentDict)
                self.attachments.append(attachment)
        # Load mentions:
        self.mentions = None
        if from_dict['mentions'] is not None:
            self.mentions = Mentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Load reactions:
        self.reactions = None
        if from_dict['reactions'] is not None:
            self.reactions = Reactions(command_socket=self._command_socket, account_id=self._account_id,
                                       contacts=self._contacts, groups=self._groups, devices=self._devices,
                                       from_dict=from_dict['reactions'])
        # Load sticker
        self.sticker = None
        if from_dict['sticker'] is not None:
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=from_dict['sticker']['packId'],
                sticker_id=from_dict['sticker']['stickerId']
            )
        # Load Quote:
        self.quote = None
        if from_dict['quote'] is not None:
            self.quote = Quote(from_dict=from_dict['quote'])
        # Load expiration:
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.expiration_timestamp = None
        if from_dict['expirationTimestamp'] is not None:
            self.expiration_timestamp = Timestamp(from_dict=from_dict['expirationTimestamp'])
        self.is_expired = from_dict['isExpired']
        # Load is_sent:
        self.is_sent = from_dict['isSent']
        # Load sent_to:
        self.sent_to = []
        if from_dict['sentTo'] is not None:
            for contactId in from_dict['sentTo']:
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)
                self.sent_to.append(contact)
        # Load delivery_receipts:
        self.delivery_receipts = []
        for receiptDict in from_dict['deliveryReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id,
                              config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)
            self.delivery_receipts.append(receipt)
        # Load read_receipts:
        self.read_receipts = []
        for receiptDict in from_dict['readReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id,
                              config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)
            self.read_receipts.append(receipt)
        # Load viewed_receipts:
        self.viewed_receipts = []
        for receiptDict in from_dict['viewedReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id,
                              config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)

        return

    ###########################
    # Helpers:
    ###########################
    def __parse_receipt__(self, receipt: Receipt) -> None:
        if receipt.receiptType == Receipt.TYPE_DELIVERY:
            self.mark_delivered(receipt.when)
            self.delivery_receipts.append(receipt)
        elif receipt.receiptType == Receipt.TYPE_READ:
            self.mark_read(receipt.when)
            self.read_receipts.append(receipt)
        elif receipt.receiptType == Receipt.TYPE_VIEWED:
            self.mark_viewed(receipt.when)
            self.viewed_receipts.append(receipt)
        else:
            errorMessage = "FATAL: Invalid receipt type, cannot parse. SentMessage.__parse_receipt__"
            raise RuntimeError(errorMessage)
        return

    def __set_expiry__(self, time_opened: Timestamp) -> None:
        if self.expiration is not None:
            expiryDateTime = time_opened.date_time + self.expiration
            self.expiration_timestamp = Timestamp(date_time=expiryDateTime)
        return

    ###########################
    # Methods:
    ###########################
    def mark_delivered(self, when: Optional[Timestamp] = None) -> None:
        """Mark message as delivered."""
        if when is None:
            when = Timestamp(now=True)
        return super().mark_delivered(when)

    def mark_read(self, when: Optional[Timestamp] = None) -> None:
        """Mark message as read."""
        if when is None:
            when = Timestamp(now=True)
        return super().mark_read(when)

    def mark_viewed(self, when: Optional[Timestamp] = None) -> None:
        """Mark message as viewed."""
        if when is None:
            when = Timestamp(now=True)
        return super().mark_viewed(when)

    def get_quote(self) -> Quote:
        """Get a quote object for this message."""
        quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                      timestamp=self.timestamp, author=self.sender, mentions=self.mentions,
                      conversation=self.recipient)
        return quote

    def parse_mentions(self) -> str:
        """Parse mentions in this message."""
        if self.mentions is None:
            return self.body
        return self.mentions.__parse_mentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, Reaction | str]:
        """Send a reaction to this message."""
        # Argument check:
        if not isinstance(emoji, str):
            __type_error__('emoji', "str, len = 1 or 2", emoji)
        if len(emoji) != 1 and len(emoji) != 2:
            error_message = "emoji must be str of len 1 or 2"
            raise ValueError(error_message)
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
            error_message = "Invalid recipient type."
            return False, error_message
        # Send reaction:
        sent, message = reaction.send()
        if not sent:
            return False, message
        # Parse reaction:
        self.reactions.__parse__(reaction)
        return True, reaction
