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

Self = TypeVar("Self", bound="SentMessage")

class SentMessage(Message):
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
                 recipient: Optional[Contact | Group] = None,
                 timestamp: Optional[Timestamp] = None,
                 body: Optional[str] = None,
                 attachments: Optional[Iterable[Attachment] | Attachment] = None,
                 mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                 reactions: Optional[Iterable[Reaction]] | Reactions | Reaction = None,
                 sticker: Optional[Sticker] = None,
                 quote: Optional[Quote] = None,
                 expiration: Optional[timedelta] = None,
                 expirationTimestamp: Optional[Timestamp] = None,
                 isExpired: bool = False,
                 isSent: bool = False,
                 sentTo: Optional[Iterable[Contact] | Contact] = None,
                 preview: Optional[Preview] = None,
                 ) -> None:
    # Check sticker_packs:
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
        mentionsList: list[Mention] | Mentions = []
        if (mentions != None):
            if (isinstance(mentions, Mentions) == True):
                mentionsList = None
            elif (isinstance(mentions, Mention) == True):
                mentionsList.append(mentions)
            elif (isinstance(mentions, Iterable) == True):
                i = 0
                for mention in mentions:
                    if (isinstance(mention, Mention) == False):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    mentionsList.append(mention)
                    i = i + 1
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mentions | Mention]", mentions)
    # Check reactions:
        reactionList: list[Reaction] = []
        if (reactions != None):
            if (isinstance(reactions, Reactions) == True):
                reactionList = None
            if ( isinstance(reactions, Reaction) == True):
                reactionList.append(reactions)
            elif (isinstance(reactions, Iterable) == True):
                i = 0
                for reaction in reactions:
                    if (isinstance(reaction, Reaction) == False):
                        __type_error__('reactions[%i]' % i, "Reaction", reaction)
                    reactionList.append(reaction)
                    i = i + 1
            else:
                __type_error__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction", reactions)
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
    # Check isSent:
        if (isinstance(isSent, bool) == False):
            __type_error__("isSent", "bool", isSent)
    # Check sentTo:
        sentToList: Optional[list[Contact]] = None
        if (sentTo != None):
            if (isinstance(sentTo, Contact) == True):
                sentToList = [ sentTo ]
            elif (isinstance(sentTo, Iterable) == True):
                sentToList = []
                i = 0
                for contact in sentToList:
                    if (isinstance(contact, Contact) == False):
                        __type_error__("sentTo[%i]" % i, "Contact", contact)
                    sentToList.append(contact)
                    i = i + 1
            else:
                __type_error__("sentTo", "Iterable[Contact] | Contact", sentTo)
    # Check previews:
        if (preview != None and isinstance(preview, Preview) == False):
            __type_error__("preview", "Preview", preview)
# Set internal vars:
        self._stickerPacks = stickerPacks
# Set external properties:
    # Set body:
        self.body: Optional[str] = body
    # Set Attachments:
        self.attachments: Optional[list[Attachment]]
        if (len(attachmentList) == 0):
            self.attachments = None
        else:
            self.attachments = attachmentList
    # Set mentions:
        self.mentions: Mentions
        if (isinstance(mentions, Mentions) == True):
            self.mentions = mentions
        elif (len(mentionsList) == 0):
            self.mentions = None
        else:
            self.mentions = Mentions(contacts=contacts, mentions=mentionsList)
    # Set reactions:
        self.reactions: Reactions
        if (isinstance(reactions, Reactions) == True):
            self.reactions = reactions
        elif (len(reactionList) == 0):
            self.reactions = Reactions(commandSocket=command_socket, accountId=account_id, contacts=contacts,
                                       groups=groups, devices=devices, thisDevice=this_device)
        else:
            self.reactions = Reactions(commandSocket=command_socket, accountId=account_id, contacts=contacts,
                                       groups=groups, devices=devices, reactions=reactionList)
    # Set sticker:
        self.sticker: Optional[Sticker] = sticker
    # Set quote:
        self.quote: Optional[Quote] = quote
    # Set expiry:
        self.expiration: Optional[timedelta] = expiration
        self.expirationTimestamp: Optional[Timestamp] = expirationTimestamp
        self.isExpired: bool = isExpired
    # Set is sent:
        self.isSent: bool = isSent
    # Set sentTo:
        self.sentTo: list[Contact]
        if (sentToList == None):
            self.sentTo = []
        else:
            self.sentTo = sentToList
    # Set deliveryReceipts, readReceipts and viewedReceipts:
        self.deliveryReceipts: list[Receipt] = []
        self.readReceipts: list[Receipt] = []
        self.viewedReceipts: list[Receipt] = []
    # Set previews:
        self.preview: Preview = preview
# Continue init:
    # Run super init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict, raw_message,
                         contacts.get_self(), recipient, this_device, timestamp, Message.TYPE_SENT_MESSAGE)
        return
##########################
# Init:
##########################
    def __from_raw_message__(self, raw_message: dict) -> None:
        # super().__from_raw_message__(raw_message)
        print("SentMessage.__from_raw_message__")
        print(raw_message)
        rawSentMessage: dict[str, object] = raw_message['sync_message']['sentMessage']
    # Load recipient and recipient type:
        if (rawSentMessage['destination'] != None):
            self.recipientType = 'contact'
            added, self.recipient = self._contacts.__get_or_add__(name="<UNKNOWN-CONTACT>",
                                                                  number=rawSentMessage['destinationNumber'],
                                                                  uuid=rawSentMessage['destinationUuid'])
        elif ('groupInfo' in rawSentMessage.keys()):
            self.recipientType = 'group'
            added, self.recipient = self._groups.__get_or_add__("<UNKNOWN-GROUP>", rawSentMessage['groupInfo']['groupId'])
    # Load timestamp:
        self.timestamp = Timestamp(timestamp=rawSentMessage['timestamp'])
    # Load Device:
        added, self.device = self._devices.__get_or_add__("<UNKNOWN-DEVICE>", raw_message['sourceDevice'])
    
    # Load body:
        self.body = rawSentMessage['message']
    # Load attachments:
        self.attachments = None
        if ('attachments' in rawSentMessage.keys()):
            self.attachments = []
            for rawAttachment in rawSentMessage['attachments']:
                self.attachments.append(Attachment(config_path=self._config_path, raw_attachment=rawAttachment))
    # Load sticker: 
        self.sticker = None
        if ('sticker' in rawSentMessage.keys()):
            self.sticker = self._stickerPacks.getSticker( packId=rawSentMessage['sticker']['packId'],
                                                            stickerId=rawSentMessage['sticker']['stickerId'])
    # Load mentions:
        self.mentions = None
        if ('mentions' in rawSentMessage.keys()):
            self.mentions = Mentions(contacts=self._contacts, raw_mentions=rawSentMessage['mentions'])
    # Load quote:
        self.quote = None
        if ('quote' in rawSentMessage.keys()):
            self.quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                               rawQuote=rawSentMessage['quote'])
    # Load expiry:
        if (rawSentMessage['expiresInSeconds'] == 0):
            self.expiration = None
            self.expirationTimestamp = None
            self.isExpired = False
        else:
            self.expiration = timedelta(seconds=rawSentMessage['expiresInSeconds'])
            self.expirationTimestamp = None
            self.isExpired = False
    # Load preview:
        self.preview = None
        if ('preview' in rawSentMessage.keys()):
            self.preview = Preview(config_path=self._config_path, raw_preview=rawSentMessage['preview'])
    # Set sent
        self.isSent = True
    # Set sent to, If group, assume sent to all current members.
        self.sentTo = []
        if (self.recipientType == 'group'):
            for contact in self.recipient.members:
                self.sentTo.append(contact)
        elif (self.recipientType == 'contact'):
            self.sentTo = [ self.recipient ]
        return
###########################
# To / From Dict:
###########################
    def __to_dict__(self) -> dict:
        sentMessageDict = super().__to_dict__()
    # Set body:
        sentMessageDict['body'] = self.body
    # Set attachments:
        sentMessageDict['attachments'] = None
        if (self.attachments != None):
            sentMessageDict["attachments"] = []
            for attacment in self.attachments:
                sentMessageDict["attachments"].append(attacment.__to_dict__())
    # Set Mentions:
        sentMessageDict['mentions'] = None
        if (self.mentions != None):
            sentMessageDict['mentions'] = self.mentions.__to_dict__()
    # Set Reactions:
        sentMessageDict['reactions'] = None
        if (self.reactions != None):
            sentMessageDict['reactions'] = self.reactions.__toDict__()
    # Set sticker:
        sentMessageDict['sticker'] = None
        if (self.sticker != None):
            sentMessageDict['sticker'] = {
                                            'packId': self.sticker._packId,
                                            'stickerId': self.sticker.id
                                        }
    # Set quote:
        sentMessageDict['quote'] = None
        if (self.quote != None):
            sentMessageDict['quote'] = self.quote.__toDict__()
    # Set expiration:
        sentMessageDict['expiration'] = None
        sentMessageDict['expirationTimestamp'] = None
        sentMessageDict['isExpired'] = self.isExpired
        if (self.expiration != None):
            sentMessageDict['expiration'] = self.expiration.seconds
        if (self.expirationTimestamp != None):
            sentMessageDict['expirationTimestamp'] = self.expirationTimestamp.__toDict__()
    # Set is sent:
        sentMessageDict['isSent'] = self.isSent
    # Set sentTo list:
        sentMessageDict['sentTo'] = []
        for contact in self.sentTo:
            sentMessageDict['sentTo'].append(contact.get_id())
    # Set deliveryReceipts list:
        sentMessageDict['deliveryReceipts'] = []
        for receipt in self.deliveryReceipts:
            sentMessageDict['deliveryReceipts'].append(receipt.__to_dict__())
    # Set readReceipts list:
        sentMessageDict['readReceipts'] = []
        for receipt in self.readReceipts:
            sentMessageDict['readReceipts'].append(receipt.__to_dict__())
    # Set viewedReceipts list:
        sentMessageDict['viewedReceipts'] = []
        for receipt in self.viewedReceipts:
            sentMessageDict['viewedReceipts'].append(receipt.__to_dict__())
        return sentMessageDict
    
    def __from_dict__(self, from_dict:dict) -> None:
        super().__from_dict__(from_dict)
    # Load Body:
        self.body = from_dict['body']
    # Load attachments:
        self.attachments = None
        if (from_dict['attachments'] != None):
            self.attachments = []
            for attachmentDict in from_dict['attachments']:
                attachment = Attachment(config_path=self._config_path, from_dict=attachmentDict)
                self.attachments.append(attachment)
    # Load mentions:
        self.mentions = None
        if (from_dict['mentions'] != None):
            self.mentions = Mentions(contacts=self._contacts, from_dict=from_dict['mentions'])
    # Load reactions:        
        self.reactions = None
        if (from_dict['reactions'] != None):
            self.reactions = Reactions(commandSocket=self._command_socket, accountId=self._account_id,
                                       contacts=self._contacts, groups=self._groups, devices=self._devices,
                                       fromDict=from_dict['reactions'])
    # Load sticker
        self.sticker = None
        if (from_dict['sticker'] != None):
            self.sticker = self._stickerPacks.getSticker(
                                                    packId=from_dict['sticker']['packId'],
                                                    stickerId=from_dict['sticker']['stickerId']
                                                )
    # Load Quote:
        self.quote == None
        if (from_dict['quote'] != None):
            self.quote = Quote(fromDict=from_dict['quote'])
    # Load expiration:
        self.expiration = None
        if (from_dict['expiration'] != None):
            self.expiration = timedelta(seconds=from_dict['expiration'])
        self.expirationTimestamp = None
        if (from_dict['expirationTimestamp'] != None):
            self.expirationTimestamp = Timestamp(fromDict=from_dict['expirationTimestamp'])
        self.isExpired = from_dict['isExpired']
    # Load isSent:
        self.isSent = from_dict['isSent']
    # Load sentTo:
        self.sentTo = []
        if (from_dict['sentTo'] != None):
            for contactId in from_dict['sentTo']:
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)
                self.sentTo.append(contact)
    # Load deliveryReceipts:
        self.deliveryReceipts = []
        for receiptDict in from_dict['deliveryReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id, config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)
            self.deliveryReceipts.append(receipt)
    # Load readReceipts:
        self.readReceipts = []
        for receiptDict in from_dict['readReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id, config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)
            self.readReceipts.append(receipt)
    # Load viewedReceipts:
        self.viewedReceipts = []
        for receiptDict in from_dict['viewedReceipts']:
            receipt = Receipt(command_socket=self._command_socket, account_id=self._account_id, config_path=self._config_path,
                              contacts=self._contacts, groups=self._groups, devices=self._devices,
                              this_device=self._this_device, from_dict=receiptDict)

        return
###########################
# Helpers:
###########################
    def __parseReceipt__(self, receipt:Receipt) -> None:
        if (receipt.receiptType == Receipt.TYPE_DELIVERY):
            self.mark_delivered(receipt.when)
            self.deliveryReceipts.append(receipt)
        elif( receipt.receiptType == Receipt.TYPE_READ):
            self.mark_read(receipt.when)
            self.readReceipts.append(receipt)
        elif (receipt.receiptType == Receipt.TYPE_VIEWED):
            self.mark_viewed(receipt.when)
            self.viewedReceipts.append(receipt)
        else:
            errorMessage = "FATAL: Invalid receipt type, cannot parse. SentMessage.__parse_receipt__"
            raise RuntimeError(errorMessage)
        return
    
    def __setExpiry__(self, timeOpened:Timestamp) -> None:
        if (self.expiration != None):
            expiryDateTime = timeOpened.datetime + self.expiration
            self.expirationTimestamp = Timestamp(dateTime=expiryDateTime)
        return
###########################
# Methods:
###########################
    def mark_delivered(self, when: Optional[Timestamp]=None) -> None:
        if (when == None):
            when = Timestamp(now=True)
        return super().mark_delivered(when)
    
    def mark_read(self, when: Optional[Timestamp]=None) -> None:
        if (when == None):
            when = Timestamp(now=True)
        return super().mark_read(when)
    
    def mark_viewed(self, when: Optional[Timestamp]=None) -> None:
        if (when == None):
            when = Timestamp(now=True)
        return super().mark_viewed(when)

    def getQuote(self) -> Quote:
        quote = Quote(configPath=self._config_path, contacts=self._contacts, groups=self._groups,
                      timestamp=self.timestamp, author=self.sender, mentions=self.mentions,
                      conversation=self.recipient)
        return quote
    
    def parseMentions(self) -> str:
        if (self.mentions == None):
            return self.body
        return self.mentions.__parse_mentions__(self.body)
    
    def react(self, emoji:str) -> tuple[bool, Reaction | str]:
    # Argument check:
        if (isinstance(emoji, str) == False):
            __type_error__('emoji', "str, len = 1 or 2", emoji)
        if (len(emoji) != 1 and len(emoji) != 2):
            errorMessage = "emoji must be str of len 1 or 2"
            raise ValueError(errorMessage)
    # Create reaction
        if (self.recipientType == 'contact'):
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id, config_path=self._config_path,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                this_device=self._this_device, recipient=self.sender, emoji=emoji, targetAuthor=self.sender,
                                targetTimestamp=self.timestamp)
        elif (self.recipientType == 'group'):
            reaction = Reaction(command_socket=self._command_socket, account_id=self._account_id, config_path=self._config_path,
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