#!/usr/bin/env python3
"""
File: signal_received_message.py
Store and handle an incoming message.
"""
# pylint: disable=R0902, R0913, R0914, W0511, E0401
import logging
from typing import TypeVar, Optional, Iterable, Any
import socket
import json
from datetime import timedelta, datetime
import pytz

from .signal_attachment import SignalAttachment
from .signal_common import (__type_error__, __socket_receive_blocking__, __socket_send__,
                            MessageTypes, RecipientTypes, ReceiptTypes, __parse_signal_response__,
                            __check_response_for_error__)
from .signal_contact import SignalContact
from .signal_contacts import SignalContacts
from .signal_device import SignalDevice
from .signal_devices import SignalDevices
from .signal_group import SignalGroup
from .signal_groups import SignalGroups
from .signal_mention import SignalMention
from .signal_mentions import SignalMentions
from .signal_message import SignalMessage
from .signal_preview import SignalPreview
from .signal_quote import SignalQuote
from .signal_reaction import SignalReaction
from .signal_reactions import SignalReactions
from .signal_sticker import SignalSticker, SignalStickerPacks
from .signal_timestamp import SignalTimestamp
from .signal_sent_message import SignalSentMessage

# Define self:
Self = TypeVar("Self", bound="SignalReceivedMessage")


class SignalReceivedMessage(SignalMessage):
    """
    Class to store a message that has been received.
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
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 ) -> None:
        """
        Initialize a ReceivedMessage object.
        :param command_socket: socket.socket: The socket to use for commands.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to signal-cli config directory.
        :param contacts: SignalContacts: This accounts' SignalContacts object.
        :param groups: SignalGroups: This accounts' SignalGroups object.
        :param devices: SignalDevices: This accounts' SignalDevices object.
        :param this_device: SignalDevice: The SignalDevice object for the device we're on.
        :param sticker_packs: SignalStickerPacks: The loaded sticker packs.
        :param from_dict: Optional[dict[str, Any]]: A dict created by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: A dict provided by signal.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Check sticker packs:
        if not isinstance(sticker_packs, SignalStickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "SignalStickerPacks", sticker_packs)

        # Set internal vars:
        self._sticker_packs: SignalStickerPacks = sticker_packs
        """The loaded sticker packs."""

        # Set external properties:
        # Set body:
        self.body: Optional[str] = None
        """The body of the message."""
        # Set Attachments:
        self.attachments: Optional[list[SignalAttachment]] = None
        """The attachments to this message.."""
        # Set mentions:
        self.mentions: SignalMentions = SignalMentions(contacts=contacts)
        """Any mentions in this message."""
        # Set reactions:
        self.reactions: SignalReactions = SignalReactions(command_socket=command_socket,
                                                          account_id=account_id,
                                                          config_path=config_path,
                                                          contacts=contacts, groups=groups,
                                                          devices=devices, this_device=this_device)
        """The reactions to this message."""
        # Set sticker:
        self.sticker: Optional[SignalSticker] = None
        """The sticker of this message."""
        # Set quote:
        self.quote: Optional[SignalQuote] = None
        """This messages quote."""
        # Set expiry:
        self.expiration: Optional[timedelta] = None
        """The expiration time as a timedelta in seconds."""
        self.expiration_timestamp: Optional[SignalTimestamp] = None
        """The SignalTimestamp for when this message expires."""
        self._is_expired: bool = False
        """Is this message expired?"""
        # View once:
        self.view_once: bool = False
        """Is this a view once message?"""

        # Set preview:
        self.previews: list[SignalPreview] = []
        """Any previews this message holds."""

        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices,
                         this_device, from_dict, raw_message, None, None, None, None,
                         MessageTypes.RECEIVED)

        # Mark this as delivered:
        if self.timestamp is not None:
            self.mark_delivered(self.timestamp)

        # Check if this is a group invite, it'll be a group message with no: body, attachment,
        # sticker, etc.
        self.is_group_invite = self.__check_invite__()
        if self.is_group_invite:
            self.body = (f"Group invite from: {self.sender.get_display_name()} to "
                         f"group: {self.recipient.get_display_name()}")
        self.is_expiration_update = self.__check_expiry_update__()
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
                self.body = "{sender} disabled disappearing messages."
            else:
                self.body = (f"{sender} set the disappearing message timer "
                             f"to: {str(self.expiration)}")

    ######################
    # Init:
    ######################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        """
        super().__from_raw_message__(raw_message)
        data_message: dict[str, Any] = raw_message['dataMessage']
        # Parse body:
        self.body = data_message['message']
        # Parse expiry
        if data_message['expiresInSeconds'] == 0:
            self.expiration = None
        else:
            self.expiration = timedelta(seconds=data_message["expiresInSeconds"])

        # Parse view once:
        self.view_once = data_message['viewOnce']

        # Parse attachments:
        if 'attachments' in data_message.keys():
            self.attachments = []
            for raw_attachment in data_message['attachments']:
                attachment = SignalAttachment(config_path=self._config_path,
                                              raw_attachment=raw_attachment)
                self.attachments.append(attachment)

        # Parse mentions:
        if 'mentions' in data_message.keys():
            self.mentions = SignalMentions(contacts=self._contacts,
                                           raw_mentions=data_message['mentions'])

        # Parse sticker:
        if 'sticker' in data_message.keys():
            self._sticker_packs.__update__()  # Update in case this is a new sticker.
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=data_message['sticker']['packId'],
                sticker_id=data_message['sticker']['stickerId'])
        # Parse Quote
        if 'quote' in data_message.keys():
            if self.recipient_type == RecipientTypes.GROUP:
                self.quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                         groups=self._groups, raw_quote=data_message['quote'],
                                         conversation=self.recipient)
            elif self.recipient_type == RecipientTypes.CONTACT:
                self.quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                         groups=self._groups, raw_quote=data_message['quote'],
                                         conversation=self.sender)
        # Parse preview:
        self.previews = []
        if 'previews' in data_message.keys():
            for raw_preview in data_message['previews']:
                preview = SignalPreview(config_path=self._config_path, raw_preview=raw_preview)
                self.previews.append(preview)

    #####################
    # To / From Dict:
    #####################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this received message.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        received_message_dict: dict[str, Any] = super().__to_dict__()
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
        received_message_dict['reactions'] = self.reactions.__to_dict__()
        # Set sticker:
        received_message_dict['sticker'] = None
        if self.sticker is not None:
            received_message_dict['sticker'] = {
                'packId': self.sticker.pack_id,
                'stickerId': self.sticker.id
            }
        # Set quote:
        received_message_dict['quote'] = None
        if self.quote is not None:
            received_message_dict['quote'] = self.quote.__to_dict__()
        # # Set is expired:
        # received_message_dict['isExpired'] = self.is_expired
        # Set expiration (timedelta)
        received_message_dict['expiration'] = None
        if self.expiration is not None:
            received_message_dict['expiration'] = self.expiration.total_seconds()
        # Set expiration timestamp:
        received_message_dict['expirationTimestamp'] = None
        if self.expiration_timestamp is not None:
            received_message_dict['expirationTimestamp'] = self.expiration_timestamp.__to_dict__()
        # Set view once:
        received_message_dict['viewOnce'] = self.view_once

        # Set previews:
        received_message_dict['previews'] = []
        for preview in self.previews:
            received_message_dict['previews'].append(preview.__to_dict__())
        return received_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        # Load body:
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
        self.mentions = SignalMentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Load reactions:
        self.reactions = SignalReactions(command_socket=self._command_socket,
                                         account_id=self._account_id,
                                         config_path=self._config_path, contacts=self._contacts,
                                         groups=self._groups, devices=self._devices,
                                         this_device=self._this_device,
                                         from_dict=from_dict['reactions'])
        # Load sticker:
        self.sticker = None
        if from_dict['sticker'] is not None:
            self.sticker = self._sticker_packs.get_sticker(
                pack_id=from_dict['sticker']['packId'],
                sticker_id=from_dict['sticker']['stickerId']
            )

        # Load quote
        self.quote = None
        if from_dict['quote'] is not None:
            self.quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                     groups=self._groups, from_dict=from_dict['quote'])
        # Load expiration:
        # self.is_expired = from_dict['isExpired']
        self.expiration = None
        if from_dict['expiration'] is not None:
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.expiration_timestamp = None
        if from_dict['expirationTimestamp'] is not None:
            self.expiration_timestamp = SignalTimestamp(from_dict=from_dict['expirationTimestamp'])

        # Load view once:
        self.view_once = from_dict['viewOnce']

        # Load previews:
        self.previews = []
        if from_dict['previews'] is not None:
            for preview_dict in from_dict['previews']:
                self.previews.append(SignalPreview(config_path=self._config_path,
                                                   from_dict=preview_dict))

    #####################
    # Helpers:
    #####################
    def __send_receipt__(self, receipt_type: ReceiptTypes) -> tuple[bool, SignalTimestamp | str]:
        """
        Send a receipt using signal.
        :param receipt_type: ReceiptTypes: The type of receipt to send; Either ReceiptTypes.READ
            or ReceiptTypes.VIEWED.
        :return: tuple[bool, str | SignalTimestamp]: The first element is True or False for
            success or failure. The second element is either the SignalTimestamp object of the
            receipts' 'when' on success, or an error message, stating what went wrong.
        :raises RuntimeError: On invalid receipt type.
        :raises CommunicationsError: On error communicating with signal.
        :raises InvalidServerResponse: On error loading signal JSON.
        :raises SignalError: On error sent by signal.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__send_receipt__.__name__)
        # Parse receipt type:
        type_string: str
        if receipt_type == ReceiptTypes.READ:
            type_string = 'read'
        elif receipt_type == ReceiptTypes.VIEWED:
            type_string = 'viewed'
        else:
            error_message: str = f"Can't send this type of receipt: {str(receipt_type)}."
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)

        # Create send receipt command object and json command string.
        send_receipt_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "sendReceipt",
            "params": {
                "account": self._account_id,
                "recipient": self.sender.get_id(),
                "type": type_string,
                "targetTimestamp": self.timestamp.timestamp,
            }
        }
        json_command_str: str = json.dumps(send_receipt_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._command_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])
        if error_occurred:
            error_message: str = (f"signal error while sending receipt. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Result is a dict:
        result_obj = response_obj['result']
        when = SignalTimestamp(timestamp=result_obj['timestamp'])
        # Parse results:
        for result in result_obj['results']:
            if result['type'] != 'SUCCESS':
                warning_message: str = (f"While sending result['type'] != 'SUCCESS'. result['type']"
                                        f"== {result['type']}")
                logger.warning(warning_message)
            else:
                recipient: dict[str, str] = result['recipientAddress']
                _, contact = self._contacts.__get_or_add__(number=recipient['number'],
                                                           uuid=recipient['uuid'])
                contact.__seen__(when)
        return True, when

    def __set_expiry__(self, time_opened: SignalTimestamp) -> None:
        """
        Set the expiration_timestamp property according to when it was opened.
        :param time_opened: Optional[SignalTimestamp]: The timestamp of when opened; If None,
        NOW is used.
        :return: None
        """
        if self.expiration is not None and self.expiration_timestamp is None:
            expiry_datetime = time_opened.datetime_obj + self.expiration
            self.expiration_timestamp = SignalTimestamp(datetime_obj=expiry_datetime)
        else:
            self.expiration_timestamp = None

    def __check_invite__(self) -> bool:
        """
        Check if this is a group invite, it's an invitation if it's a group message without a body,
            a sticker, etc.
        :returns: bool: True if this is an invitation.
        """
        if self.recipient_type == RecipientTypes.GROUP and self.body is None:
            if self.attachments is None and len(self.mentions) == 0:
                if self.sticker is None and self.quote is None:
                    if len(self.previews) == 0:
                        return True
        return False

    def __check_expiry_update__(self) -> bool:
        """
        Check if this an expiry update message, if it is, it's a message with no 'body', no sticker,
        etc., and a different expiration time than the current recipient has.
        :return: bool: True if this is an expiration update.
        """
        if self.body is None and len(self.mentions) == 0:
            if self.sticker is None and self.quote is None:
                if self.attachments is None or len(self.attachments) == 0:
                    if len(self.previews) == 0:
                        if self.expiration != self.recipient.expiration:
                            return True
        return False

    #####################
    # Methods:
    #####################
    def mark_read(self, when: SignalTimestamp = None, send_receipt: bool = True) -> None:
        """
        Mark the message as read.
        :param when: SignalTimestamp: When the message was read; If this is None, NOW is used.
        :param send_receipt: bool: Send the read receipt; If this is True, 'when' is ignored.
        :returns: None
        :raises TypeError: If when not a SignalTimestamp object, raised by super(), or if
        send_receipt is not a bool.
        :raises RuntimeError: On error sending receipt.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_read.__name__)
        # Type check send_receipt, when is type checked by super.
        if not isinstance(send_receipt, bool):
            logger.critical("Raising TypeError:")
            __type_error__("send_receipt", "bool", send_receipt)
        # Send the read receipt if requested:
        if send_receipt:
            is_success, results = self.__send_receipt__(ReceiptTypes.READ)
            if not is_success:
                error_message: str = f"failed to send read receipt: {results}"
                logger.critical("Raising RuntimeError(%s).", error_message)
                raise RuntimeError(error_message)
            time_read = results
        else:
            time_read = when
        # Set expiry and run super()
        self.__set_expiry__(time_read)
        super().mark_read(time_read)

    def mark_viewed(self, when: SignalTimestamp = None, send_receipt: bool = True) -> None:
        """
        Mark the message as viewed.
        :param when: SignalTimestamp: When the message was viewed; If this is None, NOW is used.
        :param send_receipt: bool: Send a viewed receipt; If this is True, then when is ignored.
        :returns: None
        :raises: TypeError: If when not a SignalTimestamp object, raised by super(), or if
        send_receipt is not a bool.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.mark_viewed.__name__)
        # Type check send receipt, when is type checked in super:
        if not isinstance(send_receipt, bool):
            logger.critical("Raising TypeError:")
            __type_error__("send_receipt", "bool", send_receipt)
        # If receipt requested, send the receipt:
        if send_receipt:
            is_success, results = self.__send_receipt__(ReceiptTypes.VIEWED)
            if not is_success:
                error_message: str = f"failed to send viewed receipt: {results}"
                logger.critical("Raising RuntimeError(%s).", error_message)
                raise RuntimeError(error_message)
            time_viewed = results
        else:
            time_viewed = when
        # set the expiry and run the super().
        self.__set_expiry__(time_viewed)
        super().mark_viewed(time_viewed)

    def get_quote(self) -> SignalQuote:
        """
        Get a quote object for this message.
        :returns: SignalQuote: This message as a quote.
        :raises ValueError: On invalid recipient_type.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_quote.__name__)
        quote: SignalQuote
        if self.recipient_type == RecipientTypes.CONTACT:
            quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                groups=self._groups, timestamp=self.timestamp, author=self.sender,
                                text=self.body, mentions=self.mentions, conversation=self.sender)
        elif self.recipient_type == RecipientTypes.GROUP:
            quote = SignalQuote(config_path=self._config_path, contacts=self._contacts,
                                groups=self._groups, timestamp=self.timestamp, author=self.sender,
                                text=self.body, mentions=self.mentions, conversation=self.recipient)
        else:
            error_message: str = f"invalid recipient_type: {str(self.recipient_type)}"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)
        return quote

    def parse_mentions(self) -> Optional[str]:
        """
        Parse the mentions.
        :returns: Optional[str]: The body with the mentions inserted; If 'mentions' is None,
        then the original body is returned, if body is None, then None is returned.
        """
        if self.mentions is None:
            return self.body
        return self.mentions.__parse_mentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, SignalReaction | str]:
        """
        Create and send a Reaction to this message.
        :param emoji: str: The emoji to react with.
        :returns: tuple[bool, SignalReaction | str]: The first element of the returned tuple is a
        bool, which is True or False depending on success or failure.
        The second element of the tuple will either be a SignalReaction object on success, or an
        error message stating what went wrong on failure.
        :raises: TypeError: If emoji is not a string.
        :raises: ValueError: If emoji length is not one or two characters.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.react.__name__)
        # Type check emoji:
        if not isinstance(emoji, str):
            logger.critical("Raising TypeError:")
            __type_error__('emoji', "str, len = 1->4", emoji)

        # Value check emoji:
        if 1 <= len(emoji) <= 4:
            error_message: str = "emoji must be str of len 1->4"
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

        # Create reaction
        reaction: SignalReaction
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
            error_message: str = "Invalid recipient type."
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
            raise RuntimeError(error_message)

        # Return Success:
        return True, reaction

    # TODO: Reply to this message, create a sent message with this as an attached quote.
    def reply(self,
              body: Optional[str] = None,
              attachments: Optional[Iterable[SignalAttachment | str] | SignalAttachment |
                                    str] = None,
              mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention] = None,
              sticker: Optional[SignalSticker] = None,
              preview: Optional[SignalPreview] = None,
              ) -> tuple[tuple[bool, SignalContact | SignalGroup, str | SignalSentMessage], ...]:
        """
        Send a reply to this message.
        :param body: str: The body to reply with.
        :param attachments: Optional[Iterable[SignalAttachment | str] | SignalAttachment | str]: Any
        attachments to the message.
        :param mentions: Optional[Iterable[SignalMention] | SignalMentions | SignalMention]: Any
        mentions in this message.
        :param sticker: Optional[SignalSticker]: The sticker to send as a message.
        :param preview: Optional[SignalPreview]: Any URL preview for this message.
        :return: tuple[tuple[bool, SignalContact | SignalGroup, str | SentMessage], ...]: A tuple
        of tuples.
        One inner tuple per recipient of the message.
        The first element of the inner tuple is a bool which is True or False on success or failure.
        The second element of the inner tuple is the SignalContact or SignalGroup that this message
        was sent to.
        The third element of the inner tuple is either the SentMessage object on success or an error
        message on failure.
        """
        raise NotImplementedError()

##############################
# Properties:
##############################
    @property
    def is_expired(self) -> bool:
        """
        Is this message expired?
        :return:
        """
        if self.expiration_timestamp is not None:
            if self.expiration_timestamp.datetime_obj <= pytz.utc.localize(datetime.now(pytz.UTC)):
                return True
        return False
