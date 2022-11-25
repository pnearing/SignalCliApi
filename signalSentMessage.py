#!/usr/bin/env python3

from typing import TypeVar, Optional, Iterable
import socket
from datetime import timedelta
import json

from signalAttachment import Attachment
from signalCommon import __typeError__, __socketReceive__, __socketSend__
from signalContacts import Contacts
from signalContact import Contact
from signalDevices import Devices
from signalDevice import Device
from signalGroups import Groups
from signalGroup import Group
from signalMention import Mention
from signalMentions import Mentions
from signalMessage import Message
from signalPreview import Preview
from signalQuote import Quote
from signalReaction import Reaction
from signalReactions import Reactions
from signalReceipt import Receipt
from signalSticker import Sticker, StickerPacks
from signalTimestamp import Timestamp

Self = TypeVar("Self", bound="SentMessage")

class SentMessage(Message):
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId: str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    stickerPacks: StickerPacks,
                    fromDict: Optional[dict] = None,
                    rawMessage: Optional[dict] = None,
                    recipient: Optional[Contact | Group] = None,
                    timestamp: Optional[Timestamp] = None,
                    # isDelivered: bool = False,
                    # timeDelivered: Optional[Timestamp] = None,
                    # isRead: bool = False,
                    # timeRead: Optional[Timestamp] = None,
                    # isViewed: bool = False,
                    # timeViewed: Optional[Timestamp] = None,
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
    # Check stickerPacks:
        if (isinstance(stickerPacks, StickerPacks) == False):
            __typeError__("stickerPacks", "StickerPacks", stickerPacks)
    # Check Body:   
        if (body != None and isinstance(body, str) == False):
            __typeError__("body", "Optional[str]", body)
    # Check attachments:    
        attachmentList: list[Attachment] = []
        if (attachments != None):
            if (isinstance(attachments, Attachment) == True):
                attachmentList.append(attachments)
            elif (isinstance(attachments, Iterable) == True):
                i = 0
                for attachment in attachments:
                    if (isinstance(attachment, Attachment) == False):
                        __typeError__("attachments[%i]" % i, "Attachment", attachment)
                    attachmentList.append(attachment)
                    i = i + 1
            else:
                __typeError__("attachments", "Optional[Iterable[Attachment] | Attachment", attachments)
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
                        __typeError__("mentions[%i]" % i, "Mention", mention)
                    mentionsList.append(mention)
                    i = i + 1
            else:
                __typeError__("mentions", "Optional[Iterable[Mention] | Mentions | Mention]", mentions)
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
                        __typeError__('reactions[%i]' % i, "Reaction", reaction)
                    reactionList.append(reaction)
                    i = i + 1
            else:
                __typeError__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction", reactions)
    # Check sticker:    
        if (sticker != None and isinstance(sticker, Sticker) == False):
            __typeError__("sticker", "Sticker", sticker)
    # Check quote:
        if (quote != None and isinstance(quote, Quote) == False):
                __typeError__("quote", "Quote", quote)
    # Check expiry:
        if (expiration != None):
            if (isinstance(expiration, timedelta) == False):
                __typeError__("expiry", "timedelta", expiration)
        if (expirationTimestamp != None):
            if (isinstance(expirationTimestamp, Timestamp) == False):
                __typeError__("expirationTimestamp", "Timestamp", expirationTimestamp)
        if (isinstance(isExpired, bool) == False):
            __typeError__("isExpired", "bool", isExpired)
    # Check isSent:
        if (isinstance(isSent, bool) == False):
            __typeError__("isSent", "bool", isSent)
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
                        __typeError__("sentTo[%i]" % i, "Contact", contact)
                    sentToList.append(contact)
                    i = i + 1
            else:
                __typeError__("sentTo", "Iterable[Contact] | Contact", sentTo)
    # Check previews:
        if (preview != None and isinstance(preview, Preview) == False):
            __typeError__("preview", "Preview", preview)
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
            self.reactions = Reactions(commandSocket=commandSocket, accountId=accountId, contacts=contacts,
                                        groups=groups, devices=devices, thisDevice=thisDevice)
        else:
            self.reactions = Reactions(commandSocket=commandSocket, accountId=accountId, contacts=contacts,
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
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict, rawMessage,
                            contacts.getSelf(), recipient, thisDevice, timestamp, Message.TYPE_SENT_MESSAGE)
        return
##########################
# Init:
##########################
    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        print("SentMessage.__fromRawMessage__")
        print(rawMessage)
        return
###########################
# To / From Dict:
###########################
    def __toDict__(self) -> dict:
        sentMessageDict = super().__toDict__()
    # Set body:
        sentMessageDict['body'] = self.body
    # Set attachments:
        sentMessageDict['attachments'] = None
        if (self.attachments != None):
            sentMessageDict["attachments"] = []
            for attacment in self.attachments:
                sentMessageDict["attachments"].append(attacment.__toDict__())
    # Set Mentions:
        sentMessageDict['mentions'] = None
        if (self.mentions != None):
            sentMessageDict['mentions'] = self.mentions.__toDict__()
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
            sentMessageDict['sentTo'].append(contact.getId())
    # Set deliveryReceipts list:
        sentMessageDict['deliveryReceipts'] = []
        for receipt in self.deliveryReceipts:
            sentMessageDict['deliveryReceipts'].append(receipt.__toDict__())
    # Set readReceipts list:
        sentMessageDict['readReceipts'] = []
        for receipt in self.readReceipts:
            sentMessageDict['readReceipts'].append(receipt.__toDict__())
    # Set viewedReceipts list:
        sentMessageDict['viewedReceipts'] = []
        for receipt in self.viewedReceipts:
            sentMessageDict['viewedReceipts'].append(receipt.__toDict__())
        return sentMessageDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        super().__fromDict__(fromDict)
    # Load Body:
        self.body = fromDict['body']
    # Load attachments:
        self.attachments = None
        if (fromDict['attachments'] != None):
            self.attachments = []
            for attachmentDict in fromDict['attachments']:
                attachment = Attachment(configPath=self._configPath, fromDict=attachmentDict)
                self.attachments.append(attachment)
    # Load mentions:
        self.mentions = None
        if (fromDict['mentions'] != None):
            self.mentions = Mentions(contacts=self._contacts, fromDict=fromDict['mentions'])
    # Load reactions:        
        self.reactions = None
        if (fromDict['reactions'] != None):
            self.reactions = Reactions(commandSocket=self._commandSocket, accountId=self._accountId,
                                        contacts=self._contacts, groups=self._groups, devices=self._devices,
                                        fromDict=fromDict['reactions'])
    # Load sticker
        self.sticker = None
        if (fromDict['sticker'] != None):
            self.sticker = self._stickerPacks.getSticker(
                                                    packId=fromDict['sticker']['packId'],
                                                    stickerId=fromDict['sticker']['stickerId']
                                                )
    # Load Quote:
        self.quote == None
        if (fromDict['quote'] != None):
            self.quote = Quote( fromDict=fromDict['quote'] )
    # Load expiration:
        self.expiration = None
        if (fromDict['expiration'] != None):
            self.expiration = timedelta(seconds=fromDict['expiration'])
        self.expirationTimestamp = None
        if (fromDict['expirationTimestamp'] != None):
            self.expirationTimestamp = Timestamp(fromDict=fromDict['expirationTimestamp'])
        self.isExpired = fromDict['isExpired']
    # Load isSent:
        self.isSent = fromDict['isSent']
    # Load sentTo:
        self.sentTo = []
        if (fromDict['sentTo'] != None):
            for contactId in fromDict['sentTo']:
                added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>", contactId)
                self.sentTo.append(contact)
    # Load deliveryReceipts:
        self.deliveryReceipts = []
        for receiptDict in fromDict['deliveryReceipts']:
            receipt = Receipt(commandSocket=self._commandSocket, accountId=self._accountId, configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, fromDict=receiptDict)
            self.deliveryReceipts.append(receipt)
    # Load readReceipts:
        self.readReceipts = []
        for receiptDict in fromDict['readReceipts']:
            receipt = Receipt(commandSocket=self._commandSocket, accountId=self._accountId, configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, fromDict=receiptDict)
            self.readReceipts.append(receipt)
    # Load viewedReceipts:
        self.viewedReceipts = []
        for receiptDict in fromDict['viewedReceipts']:
            receipt = Receipt(commandSocket=self._commandSocket, accountId=self._accountId, configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, fromDict=receiptDict)

        return
###########################
# Helpers:
###########################
    def __parseReceipt__(self, receipt:Receipt) -> None:
        if (receipt.receiptType == Receipt.TYPE_DELIVERY):
            self.markDelivered(receipt.when)
            self.deliveryReceipts.append(receipt)
        elif( receipt.receiptType == Receipt.TYPE_READ):
            self.markRead(receipt.when)
            self.readReceipts.append(receipt)
        elif (receipt.receiptType == Receipt.TYPE_VIEWED):
            self.markViewed(receipt.when)
            self.viewedReceipts.append(receipt)
        else:
            errorMessage = "FATAL: Invalid receipt type, cannot parse. SentMessage.__parseReceipt__"
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
    def markDelivered(self, when: Timestamp) -> None:
        return super().markDelivered(when)
    
    def markRead(self, when: Timestamp) -> None:
        return super().markRead(when)
    
    def markViewed(self, when: Timestamp) -> None:
        return super().markViewed(when)

    def getQuote(self) -> Quote:
        quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                        timestamp=self.timestamp, author=self.sender, mentions=self.mentions, 
                        conversation=self.recipient)
        return quote
    
    def parseMentions(self) -> str:
        return self.mentions.__parseMentions__(self.body)