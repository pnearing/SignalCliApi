#!/usr/bin/env python3
"""
File: signal_sent_message.py
    Store and maintain a sent message.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915, W0511, E0401
import logging
from typing import TypeVar, Optional, Iterable, Any
import socket
from datetime import timedelta, datetime

import pytz

from .signal_attachment import SignalAttachment
from .signal_common import (__type_error__, MessageTypes, RecipientTypes, ReceiptTypes,)
from .signal_contacts import SignalContacts
from .signal_contact import SignalContact
from .signal_devices import SignalDevices
from .signal_device import SignalDevice
from .signal_groups import SignalGroups
from .signal_group import SignalGroup
from .signal_mention import SignalMention
from .signal_mentions import SignalMentions
from .signal_message import SignalMessage
from .signal_preview import SignalPreview
from .signal_quote import SignalQuote
from .signal_reaction import SignalReaction
from .signal_reactions import SignalReactions
from .signal_receipt import SignalReceipt
from .signal_sticker import SignalSticker, SignalStickerPacks
from .signal_timestamp import SignalTimestamp

# Define Self:
Self = TypeVar("Self", bound="SentMessage")


def __expiration_int_to_timedelta__(expiration: int) -> Optional[timedelta]:
    if expiration == 0:
        return None
    return timedelta(seconds=expiration)


def __timedelta_to_expiration_int__(timedelta_obj: Optional[timedelta]) -> int:
    if timedelta_obj is None:
        return 0
    return int(timedelta_obj.total_seconds())


class SignalSentMessage(SignalMessage):
    """
    Class to store a sent message.
    """

    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: SignalContacts,
                 groups: SignalGroups,
                 devices: SignalDevices,
                 this_device: SignalDevice,
                 sticker_packs: SignalStickerPacks,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 recipient: Optional[SignalContact | SignalGroup] = None,
                 timestamp: Optional[SignalTimestamp] = None,
                 body: Optional[str] = None,
                 attachments: Optional[Iterable[SignalAttachment] | SignalAttachment] = None,
                 mentions: Optional[Iterable[SignalMention] | SignalMentions |
                                    SignalMention] = None,
                 reactions: Optional[Iterable[SignalReaction] | SignalReactions |
                                     SignalReaction] = None,
                 sticker: Optional[SignalSticker] = None,
                 quote: Optional[SignalQuote] = None,
                 expiration: Optional[timedelta | int] = None,
                 is_sent: bool = False,
                 sent_to: Optional[Iterable[SignalContact] | SignalContact] = None,
                 previews: Optional[Iterable[SignalPreview]] = None,
                 view_once: bool = False,
                 ) -> None:
        """
        Initialize a SentMessage object.
        :param command_socket: socket.socket: The socket to use for command operations.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object representing the device we're on.
        :param sticker_packs: SignalStickerPacks: The loaded SignalStickerPacks object.
        :param from_dict: Optional[dict[str, Any]]: The dict created by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: The dict provided by signal.
        :param recipient: Optional[SignalContact | SignalGroup]: The recipient of this message.
        :param timestamp: Optional[SignalTimestamp]: The timestamp of this message.
        :param body: Optional[str]: The body of this message.
        :param attachments: Optional[Iterable[SignalAttachment] | SignalAttachment]: Any
            attachments to this message.
        :param mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention]: Any
            mentions in this message.
        :param reactions: Optional[Iterable[SignalReaction] | SignalReactions | SignalReaction]:
            Any reactions to this message.
        :param sticker: Optional[SignalSticker]: The sticker for this message.
        :param quote: Optional[SignalQuote]: The quote this message contains.
        :param expiration: Optional[timedelta]: The expiration time in seconds as a timedelta.
        :param is_sent: bool: Is this message already sent?
        :param sent_to: Optional[Iterable[SignalContact] | SignalContact]: The SignalContacts of
            the people this message was sent to, if the message was sent to a SignalGroup,
            the members of the group will show up here individually.
        :param previews: Optional[Iterable[SignalPreview]]: Any URL previews this message contains.
        :param view_once: bool: Is this a view once message?
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Check sticker_packs:
        if not isinstance(sticker_packs, SignalStickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "SignalStickerPacks", sticker_packs)

        # Check Body:
        if body is not None and not isinstance(body, str):
            logger.critical("Raising TypeError:")
            __type_error__("body", "Optional[str]", body)

        # Check attachments:
        attachment_list: list[SignalAttachment] = []
        if attachments is not None:
            if isinstance(attachments, SignalAttachment):
                attachment_list.append(attachments)
            elif isinstance(attachments, Iterable):
                for i, attachment in enumerate(attachments):
                    if not isinstance(attachment, SignalAttachment):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"attachments[{i}]", "SignalAttachment", attachment)
                    attachment_list.append(attachment)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("attachments",
                               "Optional[Iterable[SignalAttachment] | SignalAttachment",
                               attachments)

        # Check mentions:
        mentions_list: list[SignalMention] | SignalMentions = []
        if mentions is not None:
            if isinstance(mentions, SignalMentions):
                pass  # This is checked again later.
            elif isinstance(mentions, SignalMention):
                mentions_list.append(mentions)
            elif isinstance(mentions, Iterable):
                for i, mention in enumerate(mentions):
                    if not isinstance(mention, SignalMention):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"mentions[{i}]", "SignalMention", mention)
                    mentions_list.append(mention)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("mentions", "Optional[Iterable[SignalMention] | "
                                           "SignalMentions | SignalMention]",
                               mentions)

        # Check reactions:
        reaction_list: list[SignalReaction] = []
        if reactions is not None:
            if isinstance(reactions, SignalReactions):
                pass  # This is checked again later.
            if isinstance(reactions, SignalReaction):
                reaction_list.append(reactions)
            elif isinstance(reactions, Iterable):
                for i, reaction in enumerate(reactions):
                    if not isinstance(reaction, SignalReaction):
                        logger.critical("Raising TypeError:")
                        __type_error__(f'reactions[{i}]', "SignalReaction", reaction)
                    reaction_list.append(reaction)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("reactions", "Optional[Iterable[SignalReaction] | "
                                            "SignalReactions | SignalReaction]",
                               reactions)

        # Check sticker:
        if sticker is not None and not isinstance(sticker, SignalSticker):
            logger.critical("Raising TypeError:")
            __type_error__("sticker", "SignalSticker", sticker)

        # Check quote:
        if quote is not None and not isinstance(quote, SignalQuote):
            logger.critical("Raising TypeError:")
            __type_error__("quote", "SignalQuote", quote)

        # Check expiry:
        if expiration is not None:
            if not isinstance(expiration, (timedelta, int)):
                logger.critical("Raising TypeError:")
                __type_error__("expiry", "timedelta | int", expiration)

        # Check is_sent:
        if not isinstance(is_sent, bool):
            __type_error__("is_sent", "bool", is_sent)

        # Check sent_to:
        sent_to_list: Optional[list[SignalContact]] = None
        if sent_to is not None:
            if isinstance(sent_to, SignalContact):
                sent_to_list = [sent_to]
            elif isinstance(sent_to, Iterable):
                sent_to_list = []
                for i, contact in enumerate(sent_to_list):
                    if not isinstance(contact, SignalContact):
                        logger.critical("Raising TypeError:")
                        __type_error__(f"sent_to[{i}]", "SignalContact", contact)
                    sent_to_list.append(contact)
            else:
                logger.critical("Raising TypeError:")
                __type_error__("sent_to", "Iterable[SignalContact] | SignalContact", sent_to)

        # Check previews:
        preview_list: list[SignalPreview] = []
        if previews is not None and not isinstance(previews, Iterable):
            logger.critical("Raising TypeError:")
            __type_error__("previews", "Optional[Iterable[SignalPreview]]", previews)
        if previews is not None:
            for i, preview in enumerate(previews):
                if not isinstance(preview, SignalPreview):
                    __type_error__(f'previews[{i}]', 'SignalPreview', preview)
                preview_list.append(preview)

        # Check view once:
        if not isinstance(view_once, bool):
            __type_error__('view_once', 'bool', view_once)

        # Set internal vars:
        self._sticker_packs = sticker_packs
        """The loaded sticker packs object."""

        # Set external properties:
        # Set body:
        self.body: Optional[str] = body
        """The body of the message."""
        # Set Attachments:
        self.attachments: Optional[list[SignalAttachment]]
        """Any attachments to the message."""
        if len(attachment_list) == 0:
            self.attachments = None
        else:
            self.attachments = attachment_list
        # Set mentions:
        self.mentions: SignalMentions
        """Any mentions in the message."""
        if isinstance(mentions, SignalMentions):
            self.mentions = mentions
        elif len(mentions_list) == 0:
            self.mentions = SignalMentions(contacts=contacts)
        else:
            self.mentions = SignalMentions(contacts=contacts, mentions=mentions_list)
        # Set reactions:
        self.reactions: SignalReactions
        """Any reactions to the message."""
        if isinstance(reactions, SignalReactions):
            self.reactions = reactions
        elif len(reaction_list) == 0:
            self.reactions = SignalReactions(command_socket=command_socket, account_id=account_id,
                                             config_path=config_path, contacts=contacts,
                                             groups=groups, devices=devices,
                                             this_device=this_device)
        # TODO: Fix:
        # else:
        #     self.reactions = SignalReactions(command_socket=command_socket, account_id=account_id,
        #                                      config_path=config_path, contacts=contacts,
        #                                      groups=groups, devices=devices,
        #                                      this_device=this_device, reactions=reaction_list)
        # Set sticker:
        self.sticker: Optional[SignalSticker] = sticker
        """The sticker for this message."""
        # Set quote:
        self.quote: Optional[SignalQuote] = quote
        """The quote this message contains."""
        # Set expiry:
        self.expiration: Optional[timedelta] = None
        """The expiration time of this message in seconds as a timedelta."""
        if isinstance(expiration, timedelta):
            self.expiration = expiration
        elif isinstance(expiration, int):
            self.expiration = timedelta(seconds=float(expiration))

        self.expiration_timestamp: Optional[SignalTimestamp] = None
        """The timestamp at which this message expires."""
        # self.is_expired: bool = False
        # """Is this message expired?"""
        self.view_once: bool = view_once
        """Is this a view once message?"""
        # Set is sent:
        self.is_sent: bool = is_sent
        """Was this message sent?"""
        # Set sent_to:
        self.sent_to: list[SignalContact] = []
        """List of Contacts of who this message has been sent to."""
        if sent_to_list is not None:
            self.sent_to = sent_to_list
        # Set delivery_receipts, read_receipts and viewed_receipts:
        self.delivery_receipts: list[SignalReceipt] = []
        """The delivery receipts for this message."""
        self.read_receipts: list[SignalReceipt] = []
        """The read receipts for this message."""
        self.viewed_receipts: list[SignalReceipt] = []
        """The viewed receipts for this message."""
        # Set previews:
        self.previews: list[SignalPreview] = preview_list
        """Any URL previews for this message."""

        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, contacts.get_self(), recipient,
                         this_device, timestamp, MessageTypes.SENT)
        self.is_expiration_update: bool = self.__check_expiry_update__()
        """Is this an expiration update message?"""
        if self.is_expiration_update:
            # Set the recipient expiration:
            self.recipient.expiration = self.expiration
            # If it's a contact save the contact list:
            if self.recipient.recipient_type == RecipientTypes.CONTACT:
                self._contacts.__save__()
            # Set the sender string:
            sender: str
            if self.sender == self._contacts.get_self():
                sender = "You"
            else:
                sender = self.sender.get_display_name()
            # Set the body:
            if self.expiration is None:
                self.body = f"{sender} disabled disappearing messages."
            else:
                self.body = f"{sender} set the disappearing message timer to: {self.expiration}"
        if self.expiration is not None and self.expiration.total_seconds() == 0:
            raise ValueError("timedelta with 0 seconds.")

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
        # logger: logging.Logger = logging.getLogger(__name__ + '.' +
        #                                            self.__from_raw_message__.__name__)
        raw_sent_message = raw_message['syncMessage']['sentMessage']
        # Load recipient and recipient type:
        if raw_sent_message['destination'] is not None:
            self._recipient_type = RecipientTypes.CONTACT
            _, self._recipient = self._contacts.__get_or_add__(
                number=raw_sent_message['destinationNumber'],
                uuid=raw_sent_message['destinationUuid'])
        elif 'groupInfo' in raw_sent_message.keys():
            self._recipient_type = RecipientTypes.GROUP
            _, self._recipient = self._groups.__get_or_add__(
                group_id=raw_sent_message['groupInfo']['groupId'])

        # Load timestamp:
        self._timestamp = SignalTimestamp(timestamp=raw_sent_message['timestamp'])

        # Load Device: NOTE: This in the raw_message not the raw_sent_message
        _, self._device = self._devices.__get_or_add__(device_id=raw_message['sourceDevice'])

        # Load body:
        self.body = raw_sent_message['message']

        # Load attachments:
        self.attachments = None
        if 'attachments' in raw_sent_message.keys():
            self.attachments = []
            for raw_attachment in raw_sent_message['attachments']:
                self.attachments.append(SignalAttachment(config_path=self._config_path,
                                                         raw_attachment=raw_attachment))

        # Load sticker:
        self.sticker = None
        if 'sticker' in raw_sent_message.keys():
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=raw_sent_message['sticker']['pack_id'],
                sticker_id=raw_sent_message['sticker']['sticker_id'])

        # Load mentions:
        if 'mentions' in raw_sent_message.keys():
            self.mentions = SignalMentions(contacts=self._contacts,
                                           raw_mentions=raw_sent_message['mentions'])
        else:
            self.mentions = SignalMentions(contacts=self._contacts)

        # Load quote:
        self.quote = None
        if 'quote' in raw_sent_message.keys():
            self.quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                     groups=self._groups, raw_quote=raw_sent_message['quote'],
                                     conversation=self.recipient)

        # Load expiry:
        if raw_sent_message['expiresInSeconds'] == 0:
            self.expiration = None
            self.expiration_timestamp = None
        else:
            self.expiration = timedelta(seconds=raw_sent_message['expiresInSeconds'])
            self.expiration_timestamp = None

        # Load view once:
        self.view_once = raw_sent_message['viewOnce']

        # Load previews:
        self.previews = []
        if 'previews' in raw_sent_message.keys():
            for raw_preview in raw_sent_message['previews']:
                preview = SignalPreview(config_path=self._config_path, raw_preview=raw_preview)
                self.previews.append(preview)

        # Set sent, since this is coming from a sync message.
        self.is_sent = True

        # Set sent to, if a group, assume sent to all current members.
        self.sent_to = []
        if self.recipient_type == RecipientTypes.GROUP:
            for contact in self.recipient.members:
                self.sent_to.append(contact)
        elif self.recipient_type == RecipientTypes.CONTACT:
            self.sent_to = [self.recipient]

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
        sent_message_dict['mentions'] = self.mentions.__to_dict__()
        # if self.mentions is not None:
        #     sent_message_dict['mentions'] = self.mentions.__to_dict__()

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
            sent_message_dict['expiration'] = self.expiration.total_seconds()

        # Set expiration timestamp:
        sent_message_dict['expirationTimestamp'] = None
        if self.expiration_timestamp is not None:
            sent_message_dict['expirationTimestamp'] = self.expiration_timestamp.__to_dict__()

        # # Set is expired:
        # sent_message_dict['isExpired'] = self.is_expired

        # Set view once:
        sent_message_dict['viewOnce'] = self.view_once

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

        # Store previews list:
        sent_message_dict['previews'] = []
        for preview in self.previews:
            sent_message_dict['previews'].append(preview.__to_dict__())

        # Return Resulting dict:
        return sent_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_dict__.__name__)
        super().__from_dict__(from_dict)
        # Load Body:
        self.body = from_dict['body']

        # Load attachments:
        self.attachments = None
        if from_dict['attachments'] is not None:
            self.attachments = []
            for attachment_dict in from_dict['attachments']:
                attachment = SignalAttachment(config_path=self._config_path,
                                              from_dict=attachment_dict)
                self.attachments.append(attachment)

        # Load mentions:
        # self.mentions = None
        # if from_dict['mentions'] is not None:
        self.mentions = SignalMentions(contacts=self._contacts, from_dict=from_dict['mentions'])

        # Load reactions:
        self.reactions = SignalReactions(command_socket=self._command_socket,
                                         account_id=self._account_id,
                                         config_path=self._config_path, contacts=self._contacts,
                                         groups=self._groups, devices=self._devices,
                                         this_device=self._this_device,
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
            self.quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                     groups=self._groups, from_dict=from_dict['quote'])

        # Load expiration:
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])

        # Load expiration timestamp:
        self.expiration_timestamp = None
        if from_dict['expirationTimestamp'] is not None:
            self.expiration_timestamp = SignalTimestamp(from_dict=from_dict['expirationTimestamp'])

        # # Load is expired:
        # self.is_expired = from_dict['isExpired']

        # Load view once:
        self.view_once = from_dict['viewOnce']

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
        for receipt_dict in from_dict['deliveryReceipts']:
            receipt = SignalReceipt(command_socket=self._command_socket,
                                    account_id=self._account_id,
                                    config_path=self._config_path, contacts=self._contacts,
                                    groups=self._groups, devices=self._devices,
                                    this_device=self._this_device, from_dict=receipt_dict)
            self.delivery_receipts.append(receipt)

        # Load read_receipts:
        self.read_receipts = []
        for receipt_dict in from_dict['readReceipts']:
            receipt = SignalReceipt(command_socket=self._command_socket,
                                    account_id=self._account_id,
                                    config_path=self._config_path, contacts=self._contacts,
                                    groups=self._groups, devices=self._devices,
                                    this_device=self._this_device, from_dict=receipt_dict)
            self.read_receipts.append(receipt)

        # Load viewed_receipts:
        self.viewed_receipts = []
        for receipt_dict in from_dict['viewedReceipts']:
            receipt = SignalReceipt(command_socket=self._command_socket,
                                    account_id=self._account_id, config_path=self._config_path,
                                    contacts=self._contacts, groups=self._groups,
                                    devices=self._devices, this_device=self._this_device,
                                    from_dict=receipt_dict)
            self.viewed_receipts.append(receipt)

        # Load previews:
        self.previews = []
        for preview_dict in from_dict['previews']:
            preview = SignalPreview(self._config_path, from_dict=preview_dict)
            self.previews.append(preview)

    ###########################
    # Helpers:
    ###########################
    def __parse_receipt__(self, receipt: SignalReceipt) -> None:
        """
        Parse a receipt message, storing it in the right list, and acting on it.
        :param receipt: SignalReceipt: The receipt to parse.
        :return: None
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
            if not self.is_delivered:
                self.mark_delivered(receipt.when)
        elif receipt.receipt_type == ReceiptTypes.VIEWED:
            self.mark_viewed(receipt.when)
            self.viewed_receipts.append(receipt)
            if not self.is_delivered:
                self.mark_delivered(receipt.when)
        else:
            error_message: str = f"invalid receipt type, cannot parse: {receipt.receipt_type}"
            logger.critical("Raising RuntimeError(%s)", error_message)
            raise RuntimeError(error_message)

    def __set_expiry__(self, time_opened: Optional[SignalTimestamp]) -> None:
        """
        Set the expiration_timestamp property according to when it was opened.
        :param time_opened: Optional[SignalTimestamp]: The timestamp of when opened; If None,
            NOW is used.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__set_expiry__.__name__)
        if time_opened is None:
            time_opened = SignalTimestamp(now=True)
        if self.expiration is not None and self.expiration_timestamp is None:
            expiry_datetime = time_opened.datetime_obj + self.expiration
            logger.debug("expiration is: %s", str(self.expiration))
            logger.debug("Setting expiry to: %s", expiry_datetime)
            self.expiration_timestamp = SignalTimestamp(datetime_obj=expiry_datetime)
        else:
            self.expiration_timestamp = None

    def __check_expiry_update__(self) -> bool:
        """
        Check if this an expiry update message, if it is, it's a message with no 'body',
            no sticker, etc, and a different expiration time than the current recipient has.
        :return: bool: True if this an expiration update.
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' +
        #                                            self.__check_expiry_update__.__name__)
        if self.body is None and len(self.mentions) == 0:
            if self.sticker is None and self.quote is None:
                if self.attachments is None or len(self.attachments) == 0:
                    if len(self.previews) == 0:
                        if self.expiration != self.recipient.expiration:
                            return True
        return False

    ##############################################
    # External overrides:
    ##############################################
    def mark_read(self, when: Optional[SignalTimestamp] = None) -> None:
        super().mark_read(when)
        self.__set_expiry__(when)

    def mark_viewed(self, when: Optional[SignalTimestamp] = None) -> None:
        super().mark_viewed(when)
        self.__set_expiry__(when)

    ##############################################
    # External methods:
    ##############################################
    def get_quote(self) -> SignalQuote:
        """
        Get a quote object for this message.
        :return: SignalQuote: This message as a SignalQuote object.
        """
        quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                            groups=self._groups, timestamp=self.timestamp, author=self.sender,
                            mentions=self.mentions, conversation=self.recipient)
        return quote

    def parse_mentions(self) -> str:
        """
        Parse mentions in this message.
        :return: str: The body with mentions parsed; If 'mentions' is None, the original
            body is returned.
        """
        if self.mentions is None:
            return self.body
        return self.mentions.__parse_mentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, SignalReaction | str]:
        """
        Send a reaction to this message.
        :param emoji: str: The emoji to react with.
        :return: tuple[bool, SignalReaction | str]: The first element is a bool which is either
            True or False on success or failure. The second element is either the SignalReaction
            object on success, or a string with an error message on failure.
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
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Create reaction
        if self.recipient_type == RecipientTypes.CONTACT:
            reaction = SignalReaction(command_socket=self._command_socket,
                                      account_id=self._account_id, config_path=self._config_path,
                                      contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      recipient=self.sender, emoji=emoji, target_author=self.sender,
                                      target_timestamp=self.timestamp)
        elif self.recipient_type == RecipientTypes.GROUP:
            reaction = SignalReaction(command_socket=self._command_socket,
                                      account_id=self._account_id, config_path=self._config_path,
                                      contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._this_device,
                                      recipient=self.recipient, emoji=emoji,
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
            logger.critical("Raising RuntimeError(%s).", error_message)

        # Return success:
        return True, reaction

    def reply(self,
              body: Optional[str] = None,
              attachments: Optional[Iterable[SignalAttachment | str] | SignalAttachment |
                                    str] = None,
              mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention] = None,
              sticker: Optional[SignalSticker] = None,
              preview: Optional[SignalPreview] = None,
              ) -> tuple[tuple[bool, SignalContact | SignalGroup, str | Self], ...]:
        """
        Send a reply to this message.
        :param body: str: The body to reply with.
        :param attachments: Optional[Iterable[SignalAttachment | str] | SignalAttachment | str]:
            Any attachments to the message.
        :param mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention]: Any
            mentions in this message.
        :param sticker: Optional[SignalSticker]: The sticker to send as a message.
        :param preview: Optional[SignalPreview]: Any URL preview for this message.
        :return: tuple[tuple[bool, SignalContact | SignalGroup, str | SentMessage], ...]: A tuple
            of tuples. One inner tuple per recipient of the message. The first element of the inner
            tuple is a bool which is True or False on success or failure. The second element of the
            inner tuple is the SignalContact or SignalGroup that this message was sent to. The
            third element of the inner tuple is either the SentMessage object on success or an
            error message on failure.
        """
        raise NotImplementedError()

#########################################
# Properties:
#########################################
    @property
    def is_expired(self) -> bool:
        """
        Is this message expired?
        :return: bool: True the message is expired, False it is not.
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + "is_expired.getter")
        if self.expiration_timestamp is not None:
            now = pytz.utc.localize(datetime.utcnow())
            if self.expiration_timestamp.datetime_obj <= now:
                # logger.debug("exp_ts = %s" % str(self.expiration_timestamp.datetime_obj))
                # logger.debug("now = %s" % str(now))
                # logger.debug("RETURNING TRUE!")
                return True
        return False
