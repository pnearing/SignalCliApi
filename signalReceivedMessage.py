#!/usr/bin/env python3
from typing import TypeVar, Optional, Iterable
import socket
import json
import sys
from datetime import timedelta

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

global DEBUG
DEBUG: bool = True

Self = TypeVar("Self", bound="ReceivedMessage")


class ReceivedMessage(Message):
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 stickerPacks: StickerPacks,
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
                 expirationTimestamp: Optional[Timestamp] = None,
                 isExpired: bool = False,
                 previews: Optional[Iterable[Preview] | Preview] = None,
                 ) -> None:
        # Check sticker packs:
        if (isinstance(stickerPacks, StickerPacks) == False):
            __type_error__("sticker_packs", "StickerPacks", stickerPacks)
        # Check Body:
        if (body != None and isinstance(body, str) == False):
            __type_error__("body", "Optional[str]", body)
        # Check attachments:
        attachmentList: list[Attachment] = []
        if (attachments != None):
            if (isinstance(attachments, Attachment) == True):
                attachmentList.append(attachments)
            elif (isinstance(attachments, Iterable) == True):
                i = 0
                for attachment in attachments:
                    if (isinstance(attachment, Attachment) == False):
                        __type_error__("attachments[%i]" % i, "Attachment", attachment)
                    attachmentList.append(attachment)
                    i = i + 1
            else:
                __type_error__("attachments", "Optional[Iterable[Attachment] | Attachment", attachments)
        # Check mentions:
        mentionsList: list[Mention] = []
        if (mentions != None):
            if (isinstance(mentions, Mention) == True):
                mentionsList.append(mentions)
            elif (isinstance(mentions, Iterable) == True):
                i = 0
                for mention in mentions:
                    if (isinstance(mention, Mention) == False):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentionsList.append(mention)
                    i = i + 1
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
        # Check reactions:
        reactionList: list[Reaction] = []
        if (reactions != None):
            if (isinstance(reactions, Reactions) == True):
                pass
            elif (isinstance(reactions, Reaction) == True):
                reactionList.append(reactions)
            elif (isinstance(reactions, Iterable) == True):
                i = 0
                for reaction in reactions:
                    if (isinstance(reaction, Reaction) == False):
                        __type_error__('reactions[%i]' % i, "Reaction", reaction)
                    reactionList.append(reaction)
                    i = i + 1
            else:
                __type_error__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction]", reactions)
        # Check sticker:
        if (sticker != None and isinstance(sticker, Sticker) == False):
            __type_error__("sticker", "Sticker", sticker)
        # Check quote:
        if (quote != None and isinstance(quote, Quote) == False):
            __type_error__("quote", "Quote", quote)
        # Check expiry:
        if (expiration != None):
            if (isinstance(expiration, timedelta) == False):
                __type_error__("expiry", "timedelta", expiration)
        if (expirationTimestamp != None):
            if (isinstance(expirationTimestamp, Timestamp) == False):
                __type_error__("expirationTimestamp", "Timestamp", expirationTimestamp)
        if (isinstance(isExpired, bool) == False):
            __type_error__("isExpired", "bool", isExpired)
        # Check preview:
        previewList: list[Preview] = []
        if (previews != None):
            if (isinstance(previews, Preview) == True):
                previewList.append(previews)
            elif (isinstance(previews, Iterable) == True):
                i = 0
                for preview in previews:
                    if (isinstance(preview, Preview) == False):
                        __type_error__("previews[%i]" % i, "Preview", preview)
                    previewList.append(preview)
                    i = i + 1
            else:
                __type_error__("previews", "Iterable[Preview] | Preview", previews)

        # Set internal vars:
        self._stickerPacks: StickerPacks = stickerPacks
        # Set external properties:
        # Set body:
        self.body: Optional[str] = body
        # Set Attachments:
        self.attachments: Optional[list[Attachment]]
        if len(attachmentList) == 0:
            self.attachments = None
        else:
            self.attachments = attachmentList
        # Set mentions:
        self.mentions: Mentions
        if len(mentionsList) == 0:
            self.mentions = Mentions(contacts=contacts)
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentionsList)
        # Set reactions:
        self.reactions: Reaction
        if isinstance(reactions, Reactions):
            self.reactions = reactions
        if len(reactionList) == 0:
            self.reactions = Reactions(commandSocket=command_socket, accountId=account_id, contacts=contacts,
                                       groups=groups, devices=devices, thisDevice=this_device)
        else:
            self.reactions = Reactions(commandSocket=command_socket, accountId=account_id, contacts=contacts,
                                       groups=groups, devices=devices, thisDevice=this_device,
                                       reactions=reactionList)
        # Set sticker:
        self.sticker: Optional[Sticker] = sticker
        # Set quote:
        self.quote: Optional[Quote] = quote
        # Set expiry:
        self.expiration: Optional[timedelta] = expiration
        self.expirationTimestamp: Optional[Timestamp] = expirationTimestamp
        self.isExpired: bool = isExpired
        # Set preview:
        self.previews: Optional[list[Preview]] = previewList
        # Continue Init:
        # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_RECEIVED_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
        # Mark this as delivered:
        if (self.timestamp != None):
            self.mark_delivered(self.timestamp)
        return

    ######################
    # Init:
    ######################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        # print("RecievedMessage.__from_raw_message__")
        # print(raw_message)
        dataMessage: dict[str, object] = raw_message['dataMessage']
        # Parse body:
        self.body = dataMessage['message']
        # Parse expiry
        if (dataMessage['expiresInSeconds'] == 0):
            self.expiration = None
        else:
            self.expiration = timedelta(seconds=dataMessage["expiresInSeconds"])
        # Parse attachments:
        if ('attachments' in dataMessage.keys()):
            print("DEBUG: %s: Started attachment decoding." % __name__)
            self.attachments = []
            for rawAttachment in dataMessage['attachments']:
                attachment = Attachment(config_path=self._config_path, raw_attachment=rawAttachment)
                self.attachments.append(attachment)
        # Parse mentions:
        if ('mentions' in dataMessage.keys()):
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=dataMessage['mentions'])
        # Parse sticker:
        if ('sticker' in dataMessage.keys()):
            stickerDict: dict[str, object] = dataMessage['sticker']
            self._stickerPacks.__update__()  # Update in case this is a new sticker.
            self.sticker = self._stickerPacks.getSticker(packId=stickerDict['packId'],
                                                         stickerId=stickerDict['stickerId'])
        # Parse Quote
        if ('quote' in dataMessage.keys()):
            if (self.recipient_type == 'group'):
                self.quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                                   rawQuote=dataMessage['quote'], conversation=self.recipient)
            elif (self.recipient_type == 'contact'):
                self.quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                                   rawQuote=dataMessage['quote'], conversation=self.sender)
        # Parse preview:
        self.previews = []
        if ('previews' in dataMessage.keys()):
            for rawPreview in dataMessage['previews']:
                preview = Preview(config_path=self._config_path, raw_preview=rawPreview)
                self.previews.append(preview)

        return

    #####################
    # To / From Dict:
    #####################
    def __to_dict__(self) -> dict:
        receivedMessageDict = super().__to_dict__()
        # Set body:
        receivedMessageDict['body'] = self.body
        # Set attachments
        receivedMessageDict['attachments'] = None
        if (self.attachments != None):
            receivedMessageDict["attachments"] = []
            for attachment in self.attachments:
                receivedMessageDict["attachments"].append(attachment.__to_dict__())
        # Set mentions:
        receivedMessageDict['mentions'] = self.mentions.__to_dict__()
        # Set reactions:
        # receivedMessageDict['reactions'] = None
        # if (self.reactions != None):
        receivedMessageDict['reactions'] = self.reactions.__toDict__()
        # Set sticker:
        receivedMessageDict['sticker'] = None
        if (self.sticker != None):
            receivedMessageDict['sticker'] = {
                'packId': self.sticker._packId,
                'stickerId': self.sticker.id
            }
        # Set quote:
        receivedMessageDict['quote'] = None
        if (self.quote != None):
            receivedMessageDict['quote'] = self.quote.__toDict__()
        # Set expiration:
        receivedMessageDict['isExpired'] = self.isExpired
        receivedMessageDict['expiration'] = None
        receivedMessageDict['expirationTimestamp'] = None
        if (self.expiration != None):
            receivedMessageDict['expiration'] = self.expiration.seconds
        if (self.expirationTimestamp != None):
            receivedMessageDict['expirationTimestamp'] = self.expirationTimestamp.__toDict__()
        # Set previews:
        receivedMessageDict['previews'] = []
        for preview in self.previews:
            receivedMessageDict['previews'].append(preview.__to_dict__())
        return receivedMessageDict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Load body:
        self.body = from_dict['body']
        # Load attachments:
        self.attachments = None
        if (from_dict['attachments'] != None):
            self.attachments = []
            for attachmentDict in from_dict['attachments']:
                attachment = Attachment(config_path=self._config_path, from_dict=attachmentDict)
                self.attachments.append(attachment)
        # Load mentions:
        self.mentions = Mentions(contacts=self._contacts, from_dict=from_dict['mentions'])
        # Load reactions:
        # self.reactions = None
        # if (from_dict['reactions'] != None):
        self.reactions = Reactions(commandSocket=self._command_socket, accountId=self._account_id,
                                   contacts=self._contacts, groups=self._groups, devices=self._devices,
                                   fromDict=from_dict['reactions'])
        # Load sticker:
        self.sticker = None
        if (from_dict['sticker'] != None):
            self.sticker = self._stickerPacks.getSticker(
                packId=from_dict['sticker']['packId'],
                stickerId=from_dict['sticker']['stickerId']
            )
        # Load quote
        self.quote = None
        if (from_dict['quote'] != None):
            self.quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                               fromDict=from_dict['quote'])
        # Load expiration:
        self.isExpired = from_dict['isExpired']
        self.expiration = None
        if (from_dict['expiration'] != None):
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.expirationTimestamp = None
        if (from_dict['expirationTimestamp'] != None):
            self.expirationTimestamp = Timestamp(fromDict=from_dict['expirationTimestamp'])
        # Load previews:
        self.previews = []
        for previewDict in from_dict['previews']:
            self.previews.append(Preview(config_path=self._config_path, from_dict=previewDict))
        return

    #####################
    # Helpers:
    #####################
    def __sendReceipt__(self, receiptType: str) -> Timestamp:
        # Create send receipt command object and json command string.
        sendReceiptCommandObj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "sendReceipt",
            "params": {
                "account": self._account_id,
                "recipient": self.sender.get_id(),
                "type": receiptType,
                "targetTimestamp": self.timestamp.timestamp,
            }
        }
        jsonCommandStr = json.dumps(sendReceiptCommandObj) + '\n'
        # Communicate with signal:
        __socket_send__(self._command_socket, jsonCommandStr)
        responseStr = __socket_receive__(self._command_socket)
        # Parse Response:
        responseObj: dict = json.loads(responseStr)
        # Check for error:
        if ('error' in responseObj.keys()):
            errorMessage = "signal error while sending reciept. Code: %i Message: %s" % (responseObj['error']['code'],
                                                                                         responseObj["error"][
                                                                                             'message'])
            raise RuntimeError(errorMessage)
        # Result is a dict:
        # print(responseObj)
        when = Timestamp(timestamp=responseObj['result']['timestamp'])
        # Parse results:
        for result in responseObj['result']['results']:
            if (result['type'] != 'SUCCESS'):
                if (DEBUG == True):
                    errorMessage = "in send receipt, result type not SUCCESS: %s" % result['type']
                    print(errorMessage, file=sys.stderr)
            else:
                if (result['recipientAddress']['number'] != None):
                    added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                   result['recipientAddress']['number'])
                else:
                    added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>",
                                                                   result['recipientAddress']['uuid'])
                contact.seen(when)
        return when

    def __setExpiry__(self, timeOpened: Timestamp):
        if (self.expiration != None):
            expiryDateTime = timeOpened.datetime + self.expiration
            self.expirationTimestamp = Timestamp(dateTime=expiryDateTime)
        return

    #####################
    # Methods:
    #####################
    def mark_delivered(self, when: Timestamp) -> None:
        return super().mark_delivered(when)

    def mark_read(self, when: Timestamp = None, sendReceipt: bool = True) -> None:
        if (sendReceipt == True):
            when = self.__sendReceipt__('read')
        elif (when == None):
            when = Timestamp(now=True)
        self.__setExpiry__(when)
        return super().mark_read(when)

    def mark_viewed(self, when: Timestamp = None, sendReceipt: bool = True) -> None:
        if (sendReceipt == True):
            when = self.__sendReceipt__('viewed')
        elif (when == None):
            when = Timestamp(now=True)
        self.__setExpiry__(when)
        return super().mark_viewed(when)

    def getQuote(self) -> Quote:
        quote: Quote
        if (self.recipient_type == 'contact'):
            quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.sender)
        elif (self.recipient_type == 'group'):
            quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.recipient)
        else:
            raise ValueError("invalid recipient_type in RecievedMessage.getQuote")
        return quote

    def parseMentions(self) -> str:
        return self.mentions.__parse_mentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, Reaction | str]:
        # Argument check:
        if (isinstance(emoji, str) == False):
            __type_error__('emoji', "str, len = 1|2", emoji)
        if (len(emoji) != 1 and len(emoji) != 2):
            errorMessage = "emoji must be str of len 1|2"
            raise ValueError(errorMessage)
        # Create reaction
        if (self.recipient_type == 'contact'):
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.sender, emoji=emoji,
                                targetAuthor=self.sender,
                                targetTimestamp=self.timestamp)
        elif (self.recipient_type == 'group'):
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id,
                                config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.recipient, emoji=emoji,
                                targetAuthor=self.sender, targetTimestamp=self.timestamp)
        else:
            errorMessage = "Invalid recipient type."
            return (False, errorMessage)
        # Send reaction:
        sent, message = reaction.send()
        if (sent == False):
            return (False, message)
        # Parse reaction:
        self.reactions.__parse__(reaction)
        return (True, reaction)
