#!/usr/bin/env python3
"""
File: signalSentMessage.py
Store and maintain a sent message.
"""
import logging
from typing import TypeVar, Optional, Iterable, Any
import socket
from datetime import timedelta

from .signalAttachment import Attachment
from .signalCommon import __type_error__, __socket_receive_blocking__, __socket_send__, UNKNOWN_DEVICE_NAME, MessageTypes,\
    RecipientTypes, ReceiptTypes, __parse_signal_response__, __check_response_for_error__
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
# Define Self:
Self = TypeVar("Self", bound="SentMessage")


class SentMessage(Message):
    """
    Class to store a sent message.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 sticker_packs: StickerPacks,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 recipient: Optional[Contact | Group] = None,
                 timestamp: Optional[Timestamp] = None,
                 body: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                 reactions: Optional[Iterable[Reaction] | Reactions | Reaction] = None,
                 sticker: Optional[Sticker] = None,
                 quote: Optional[Quote] = None,
                 expiration: Optional[timedelta] = None,
                 is_sent: bool = False,
                 sent_to: Optional[Iterable[Contact] | Contact] = None,
                 preview: Optional[Preview] = None,
                 ) -> None:
        """
        Initialize a SentMessage object.
        :param command_socket: socket.socket: The socket to use for command operations.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to signal-cli config directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The Device object representing the device we're on.
        :param sticker_packs: StickerPacks: The loaded StickerPacks object.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: The dict provided by signal.
        :param recipient: Optional[Contact | Group]: The recipient of this message.
        :param timestamp: Optional[Timestamp]: The timestamp of this message.
        :param body: Optional[str]: The body of this message.
        :param attachments: Optional[Iterable[Attachment] | Attachment]: Any attachments to this message.
        :param mentions: Optional[Iterable[Mention] | Mentions | Mention]: Any mentions in this message.
        :param reactions: Optional[Iterable[Reaction] | Reactions | Reaction]: Any reactions to this message.
        :param sticker: Optional[Sticker]: The sticker for this message.
        :param quote: Optional[Quote]: The quote this message contains.
        :param expiration: Optional[timedelta]: The expiration time in seconds as a timedelta.
        :param is_sent: bool: Is this message already sent?
        :param sent_to: Optional[Iterable[Contact] | Contact]: The Contacts of the people this message was sent to, if
            the message was sent to a Group, the members of the group will show up here individually.
        :param preview: Optional[Preview]: Any URL preview this message contains.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Check sticker_packs:
        if not isinstance(sticker_packs, StickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)

        # Check Body:
        if body is not None and not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "Optional[str]", body)

        # Check attachments:
        attachment_list: list[Attachment] = []
        if attachments is not None:
            if isinstance(attachments, Attachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, Attachment):
                        logger.critical("Raising TypeError:")
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachment_list.append(attachment)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments", "Optional[Iterable[Attachment] | Attachment", attachments)

        # Check mentions:
        mentions_list: list[Mention] | Mentions = []
        if mentions is not None:
            if isinstance(mentions, Mentions):
                pass  # This is checked again later.
            elif isinstance(mentions, Mention):
                mentions_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, Mention):
                        logger.critical("Raising TypeError:")
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentions_list.append(mention)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("mentions", "Optional[Iterable[Mention] | Mentions | Mention]", mentions)

        # Check reactions:
        reaction_list: list[Reaction] = []
        if reactions is not None:
            if isinstance(reactions, Reactions):
                pass  # This is checked again later.
            if isinstance(reactions, Reaction):
                reaction_list.append(reactions)
            elif isinstance(reactions, Iterable):
                for i, reaction in enumerate(reactions):
                    if not isinstance(reaction, Reaction):
                        logger.critical("Raising TypeError:")
                        __type_error__('reactions[%i]' % i, "Reaction", reaction)
                    reaction_list.append(reaction)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction", reactions)

        # Check sticker:
        if sticker is not None and not isinstance(sticker, Sticker):
            logger.critical("Raising TypeError:")
            __type_error__("sticker", "Sticker", sticker)

        # Check quote:
        if quote is not None and not isinstance(quote, Quote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "Quote", quote)

        # Check expiry:
        if expiration is not None:
            if not isinstance(expiration, timedelta):
                logger.critical("Raising TypeError:")
                __type_error__("expiry", "timedelta", expiration)

        # Check is_sent:
        if not isinstance(is_sent, bool):
            __type_error__("is_sent", "bool", is_sent)

        # Check sent_to:
        sent_to_list: Optional[list[Contact]] = None
        if sent_to is not None:
            if isinstance(sent_to, Contact):
                sent_to_list = [sent_to]
            elif isinstance(sent_to, Iterable):
                sent_to_list = []
                for i, contact in enumerate(sent_to_list):
                    if not isinstance(contact, Contact):
                        logger.critical("Raising TypeError:")
                        __type_error__("sent_to[%i]" % i, "Contact", contact)
                    sent_to_list.append(contact)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("sent_to", "Iterable[Contact] | Contact", sent_to)

        # Check previews:
        if preview is not None and not isinstance(preview, Preview):
            logger.critical("Raising TypeError:")
            __type_error__("preview", "Preview", preview)

        # Set internal vars:
        self._sticker_packs = sticker_packs
        """The loaded sticker packs object."""

        # Set external properties:
        # Set body:
        self.body: Optional[str] = body
        """The body of the message."""
        # Set Attachments:
        self.attachments: Optional[list[Attachment]]
        """Any attachments to the message."""
        if len(attachment_list) == 0:
            self.attachments = None
        else:
            self.attachments = attachment_list
        # Set mentions:
        self.mentions: Mentions
        """Any mentions in the message."""
        if isinstance(mentions, Mentions):
            self.mentions = mentions
        elif len(mentions_list) == 0:
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentions_list)
        # Set reactions:
        self.reactions: Reactions
        """Any reactions to the message."""
        if isinstance(reactions, Reactions):
            self.reactions = reactions
        elif len(reaction_list) == 0:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id,
                                       config_path=self._config_path, contacts=contacts, groups=groups, devices=devices,
                                       this_device=this_device)
        else:
            self.reactions = Reactions(command_socket=command_socket, account_id=account_id,
                                       config_path=self._config_path, contacts=contacts, groups=groups, devices=devices,
                                       this_device=this_device, reactions=reaction_list)
        # Set sticker:
        self.sticker: Optional[Sticker] = sticker
        """The sticker for this message."""
        # Set quote:
        self.quote: Optional[Quote] = quote
        """The quote this message contains."""
        # Set expiry:
        self.expiration: Optional[timedelta] = expiration
        """The expiration time of this message in seconds as a timedelta."""
        self.expiration_timestamp: Optional[Timestamp] = None
        """The timestamp at which this message expires."""
        self.is_expired: bool = False
        """Is this message expired?"""
        # Set is sent:
        self.is_sent: bool = is_sent
        """Was this message sent?"""
        # Set sent_to:
        self.sent_to: list[Contact] = []
        """List of Contacts of who this message has been sent to."""
        if sent_to_list is not None:
            self.sent_to = sent_to_list
        # Set delivery_receipts, read_receipts and viewed_receipts:
        self.delivery_receipts: list[Receipt] = []
        """The delivery receipts for this message."""
        self.read_receipts: list[Receipt] = []
        """The read receipts for this message."""
        self.viewed_receipts: list[Receipt] = []
        """The viewed receipts for this message."""
        # Set previews:
        self.preview: Preview = preview
        """Any URL previews for this message."""

        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, contacts.get_self(), recipient, this_device, timestamp, MessageTypes.SENT)

        return

    ##########################
    # Init:
    ##########################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load from a dict provided by Signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        # super().__from_raw_message__(raw_message)
        # Set raw message dict:
        raw_sent_message: dict[str, Any] = raw_message['sync_message']['sentMessage']

        # Load recipient and recipient type:
        if raw_sent_message['destination'] is not None:
            self.recipient_type = RecipientTypes.CONTACT
            _, self.recipient = self._contacts.__get_or_add__(number=raw_sent_message['destinationNumber'],
                                                                  uuid=raw_sent_message['destinationUuid'])
        elif 'groupInfo' in raw_sent_message.keys():
            self.recipient_type = RecipientTypes.GROUP
            _, self.recipient = self._groups.__get_or_add__(group_id=raw_sent_message['groupInfo']['groupId'])

        # Load timestamp:
        self.timestamp = Timestamp(timestamp=raw_sent_message['timestamp'])

        # Load Device:
        _, self.device = self._devices.__get_or_add__(device_id=raw_message['sourceDevice'])

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

        # Set sent, since this is coming from a sync message.
        self.is_sent = True

        # Set sent to, if a group, assume sent to all current members.
        self.sent_to = []
        if self.recipient_type == RecipientTypes.GROUP:
            for contact in self.recipient.members:
                self.sent_to.append(contact)
        elif self.recipient_type == RecipientTypes.CONTACT:
            self.sent_to = [self.recipient]
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict to store this sent message in.
        :return: dict[str, Any]: A dict to provide to __from_dict__().
        """
        # Call super:
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
            sent_message_dict['sticker']: dict[str, str | int] = {
                'packId': self.sticker.pack_id,  # String
                'stickerId': self.sticker.id  # Integer
            }

        # Set quote:
        sent_message_dict['quote'] = None
        if self.quote is not None:
            sent_message_dict['quote'] = self.quote.__to_dict__()

        # Set expiration:
        sent_message_dict['expiration'] = None
        if self.expiration is not None:
            sent_message_dict['expiration'] = self.expiration.seconds

        # Set expiration timestamp:
        sent_message_dict['expirationTimestamp'] = None
        if self.expiration_timestamp is not None:
            sent_message_dict['expirationTimestamp'] = self.expiration_timestamp.__to_dict__()

        # Set is expired:
        sent_message_dict['isExpired'] = self.is_expired

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
        # Return Resulting dict:
        return sent_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
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
                                       config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                                       devices=self._devices, this_device=self._this_device,
                                       from_dict=from_dict['reactions'])

        # Load sticker
        self.sticker = None
        if from_dict['sticker'] is not None:
            sticker_dict: dict[str, str | int] = from_dict['sticker']
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=sticker_dict['packId'],  # String
                sticker_id=sticker_dict['stickerId']  # Integer
            )

        # Load Quote:
        self.quote = None
        if from_dict['quote'] is not None:
            self.quote = Quote(from_dict=from_dict['quote'])

        # Load expiration:
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])

        # Load expiration timestamp:
        self.expiration_timestamp = None
        if from_dict['expirationTimestamp'] is not None:
            self.expiration_timestamp = Timestamp(from_dict=from_dict['expirationTimestamp'])

        # Load is expired:
        self.is_expired = from_dict['isExpired']

        # Load is_sent:
        self.is_sent = from_dict['isSent']

        # Load sent_to:
        self.sent_to = []
        if from_dict['sentTo'] is not None:
            for contact_id in from_dict['sentTo']:
                _, contact = self._contacts.__get_or_add__(contact_id=contact_id)
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
        """
        Parse a receipt message, storing it in the right list, and acting on it.
        :param receipt: Receipt: The receipt to parse.
        :return:
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_receipt__.__name__)
        # Parse the receipt based on type:
        if receipt.receipt_type == ReceiptTypes.DELIVER:
            self.mark_delivered(receipt.when)
            self.delivery_receipts.append(receipt)
        elif receipt.receipt_type == ReceiptTypes.READ:
            self.mark_read(receipt.when)
            self.read_receipts.append(receipt)
        elif receipt.receipt_type == ReceiptTypes.VIEWED:
            self.mark_viewed(receipt.when)
            self.viewed_receipts.append(receipt)
        else:
            error_message: str = "invalid receipt type, cannot parse: %s" % str(receipt.receipt_type)
            logger.critical("Raising RuntimeError(%s)" % error_message)
            raise RuntimeError(error_message)
        return

    def __set_expiry__(self, time_opened: Timestamp) -> None:
        """
        Set the expiration datetime object.
        :param time_opened: Timestamp: The time the message was opened.
        :return: None
        """
        if self.expiration is not None:
            expiry_datetime = time_opened.datetime + self.expiration
            self.expiration_timestamp = Timestamp(datetime_obj=expiry_datetime)
        else:
            self.expiration_timestamp = None
        return

    ###########################
    # Methods:
    ###########################
    # def mark_delivered(self, when: Optional[Timestamp] = None) -> None:
    #     """
    #     Mark this message as delivered.
    #     :param when: Optional[Timestamp]: The timestamp for when this was delivered; If None, NOW is used.
    #     :return: None
    #     """
    #     return super().mark_delivered(when)
    #
    # def mark_read(self, when: Optional[Timestamp] = None) -> None:
    #     """
    #     Mark this message as read.
    #     :param when: Optional[Timestamp]: The timestamp for when this was read; If None, NOW is used.
    #     :return: None
    #     """
    #     return super().mark_read(when)
    #
    # def mark_viewed(self, when: Optional[Timestamp] = None) -> None:
    #     """
    #     Mark this message as viewed.
    #     :param when: Optional[Timestamp]: The timestamp for when this was viewed; If None, NOW is used.
    #     :return: None
    #     """
    #     return super().mark_viewed(when)

    def get_quote(self) -> Quote:
        """
        Get a quote object for this message.
        :return: Quote: This message as a Quote object.
        """
        quote = Quote(config_path=self._config_path, contacts=self._contacts, groups=self._groups,
                      timestamp=self.timestamp, author=self.sender, mentions=self.mentions,
                      conversation=self.recipient)
        return quote

    def parse_mentions(self) -> str:
        """
        Parse mentions in this message.
        :return: str: The body with mentions parsed; If 'mentions' is None, the original body is returned.
        """
        if self.mentions is None:
            return self.body
        return self.mentions.__parse_mentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, Reaction | str]:
        """
        Send a reaction to this message.
        :param emoji: str: The emoji to react with.
        :return: tuple[bool, Reaction | str]: The first element is a bool which is either True or False on success or
            failure.
            The second element is either the Reaction object on success, or a string with an error message on failure.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.react.__name__)

        # Type check emoji:
        if not isinstance(emoji, str):
            logger.critical("Raising TypeError:")
            __type_error__('emoji', "str, len = 1 or 2", emoji)

        # Value check emoji:
        if 1 <= len(emoji) <= 4:
            error_message: str = "emoji must be str of len 1 -> 4"
            logger.critical("Raising ValueError(%s)." % error_message)
            raise ValueError(error_message)

        # Create reaction
        if self.recipient_type == RecipientTypes.CONTACT:
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.sender, emoji=emoji,
                                target_author=self.sender,
                                target_timestamp=self.timestamp)
        elif self.recipient_type == RecipientTypes.GROUP:
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
        parsed: bool = self.reactions.__parse__(reaction)
        if not parsed:
            error_message: str = "failed to parse reaction."
            logger.critical("Raising RuntimeError(%s)." % error_message)

        # Return success:
        return True, reaction

    def reply(self,
              body: Optional[str] = None,
              attachments: Optional[Iterable[Attachment | str] | Attachment | str] = None,
              mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
              sticker: Optional[Sticker] = None,
              preview: Optional[Preview] = None,
              ) -> tuple[tuple[bool, Contact | Group, str | Self], ...]:
        """
        Send a reply to this message.
        :param body: str: The body to reply with.
        :param attachments: Optional[Iterable[Attachment | str] | Attachment | str]: Any attachments to the message.
        :param mentions: Optional[Iterable[Mention] | Mentions | Mention]: Any mentions in this message.
        :param sticker: Optional[Sticker]: The sticker to send as a message.
        :param preview: Optional[Preview]: Any URL preview for this message.
        :return: tuple[tuple[bool, Contact | Group, str | SentMessage], ...]: A tuple of tuples. One inner tuple per
            recipient of the message.
            The first element of the inner tuple is a bool which is True or False on success or failure.
            The second element of the inner tuple is the Contact or Group that this message was sent to.
            The third element of the inner tuple is either the SentMessage object on success or an error message on
            failure.
        """
        raise NotImplementedError()
