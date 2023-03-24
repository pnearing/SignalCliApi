#!/usr/bin/env python3
from typing import TypeVar, Optional, Iterable
import socket
import json
import sys
from datetime import timedelta

from .signalAttachment import Attachment
from .signalCommon import __typeError__, __socketReceive__, __socketSend__
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
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 isDelivered: bool = False,
                 timeDelivered: Optional[Timestamp] = None,
                 isRead: bool = False,
                 timeRead: Optional[Timestamp] = None,
                 isViewed: bool = False,
                 timeViewed: Optional[Timestamp] = None,
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
            __typeError__("sticker_packs", "StickerPacks", stickerPacks)
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
        mentionsList: list[Mention] = []
        if (mentions != None):
            if (isinstance(mentions, Mention) == True):
                mentionsList.append(mentions)
            elif (isinstance(mentions, Iterable) == True):
                i = 0
                for mention in mentions:
                    if (isinstance(mention, Mention) == False):
                        __typeError__("mentions[%i]" % i, "Mention", mention)
                    mentionsList.append(mention)
                    i = i + 1
            else:
                __typeError__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
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
                        __typeError__('reactions[%i]' % i, "Reaction", reaction)
                    reactionList.append(reaction)
                    i = i + 1
            else:
                __typeError__("reactions", "Optional[Iterable[Reaction] | Reactions | Reaction]", reactions)
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
        # Check preview:
        previewList: list[Preview] = []
        if (previews != None):
            if (isinstance(previews, Preview) == True):
                previewList.append(previews)
            elif (isinstance(previews, Iterable) == True):
                i = 0
                for preview in previews:
                    if (isinstance(preview, Preview) == False):
                        __typeError__("previews[%i]" % i, "Preview", preview)
                    previewList.append(preview)
                    i = i + 1
            else:
                __typeError__("previews", "Iterable[Preview] | Preview", previews)

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
            self.reactions = Reactions(commandSocket=commandSocket, accountId=accountId, contacts=contacts,
                                       groups=groups, devices=devices, thisDevice=thisDevice)
        else:
            self.reactions = Reactions(commandSocket=commandSocket, accountId=accountId, contacts=contacts,
                                       groups=groups, devices=devices, thisDevice=thisDevice,
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
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                         rawMessage, sender, recipient, device, timestamp, Message.TYPE_RECEIVED_MESSAGE, isDelivered,
                         timeDelivered, isRead, timeRead, isViewed, timeViewed)
        # Mark this as delivered:
        if (self.timestamp != None):
            self.markDelivered(self.timestamp)
        return

    ######################
    # Init:
    ######################
    def __fromRawMessage__(self, rawMessage: dict) -> None:
        super().__fromRawMessage__(rawMessage)
        # print("RecievedMessage.__fromRawMessage__")
        # print(rawMessage)
        dataMessage: dict[str, object] = rawMessage['dataMessage']
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
                attachment = Attachment(configPath=self._configPath, rawAttachment=rawAttachment)
                self.attachments.append(attachment)
        # Parse mentions:
        if ('mentions' in dataMessage.keys()):
            self.mentions = Mentions(contacts=self._contacts, rawMentions=dataMessage['mentions'])
        # Parse sticker:
        if ('sticker' in dataMessage.keys()):
            stickerDict: dict[str, object] = dataMessage['sticker']
            self._stickerPacks.__update__()  # Update in case this is a new sticker.
            self.sticker = self._stickerPacks.getSticker(packId=stickerDict['packId'],
                                                         stickerId=stickerDict['stickerId'])
        # Parse Quote
        if ('quote' in dataMessage.keys()):
            if (self.recipientType == 'group'):
                self.quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                   rawQuote=dataMessage['quote'], conversation=self.recipient)
            elif (self.recipientType == 'contact'):
                self.quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                   rawQuote=dataMessage['quote'], conversation=self.sender)
        # Parse preview:
        self.previews = []
        if ('previews' in dataMessage.keys()):
            for rawPreview in dataMessage['previews']:
                preview = Preview(configPath=self._configPath, rawPreview=rawPreview)
                self.previews.append(preview)

        return

    #####################
    # To / From Dict:
    #####################
    def __toDict__(self) -> dict:
        receivedMessageDict = super().__toDict__()
        # Set body:
        receivedMessageDict['body'] = self.body
        # Set attachments
        receivedMessageDict['attachments'] = None
        if (self.attachments != None):
            receivedMessageDict["attachments"] = []
            for attachment in self.attachments:
                receivedMessageDict["attachments"].append(attachment.__toDict__())
        # Set mentions:
        receivedMessageDict['mentions'] = self.mentions.__toDict__()
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
            receivedMessageDict['previews'].append(preview.__toDict__())
        return receivedMessageDict

    def __fromDict__(self, fromDict: dict) -> None:
        super().__fromDict__(fromDict)
        # Load body:
        self.body = fromDict['body']
        # Load attachments:
        self.attachments = None
        if (fromDict['attachments'] != None):
            self.attachments = []
            for attachmentDict in fromDict['attachments']:
                attachment = Attachment(configPath=self._configPath, fromDict=attachmentDict)
                self.attachments.append(attachment)
        # Load mentions:
        self.mentions = Mentions(contacts=self._contacts, fromDict=fromDict['mentions'])
        # Load reactions:
        # self.reactions = None
        # if (from_dict['reactions'] != None):
        self.reactions = Reactions(commandSocket=self._commandSocket, accountId=self._accountId,
                                   contacts=self._contacts, groups=self._groups, devices=self._devices,
                                   fromDict=fromDict['reactions'])
        # Load sticker:
        self.sticker = None
        if (fromDict['sticker'] != None):
            self.sticker = self._stickerPacks.getSticker(
                packId=fromDict['sticker']['packId'],
                stickerId=fromDict['sticker']['stickerId']
            )
        # Load quote
        self.quote = None
        if (fromDict['quote'] != None):
            self.quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                               fromDict=fromDict['quote'])
        # Load expiration:
        self.isExpired = fromDict['isExpired']
        self.expiration = None
        if (fromDict['expiration'] != None):
            self.expiration = timedelta(seconds=fromDict['expiration'])
        self.expirationTimestamp = None
        if (fromDict['expirationTimestamp'] != None):
            self.expirationTimestamp = Timestamp(fromDict=fromDict['expirationTimestamp'])
        # Load previews:
        self.previews = []
        for previewDict in fromDict['previews']:
            self.previews.append(Preview(configPath=self._configPath, fromDict=previewDict))
        return

    #####################
    # Helpers:
    #####################
    def __sendReceipt__(self, receiptType: str) -> Timestamp:
        # Create send receipt command object and json command string.
        sendReceiptCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "sendReceipt",
            "params": {
                "account": self._accountId,
                "recipient": self.sender.getId(),
                "type": receiptType,
                "targetTimestamp": self.timestamp.timestamp,
            }
        }
        jsonCommandStr = json.dumps(sendReceiptCommandObj) + '\n'
        # Communicate with signal:
        __socketSend__(self._commandSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._commandSocket)
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
                    added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>",
                                                                 result['recipientAddress']['number'])
                else:
                    added, contact = self._contacts.__getOrAdd__("<UNKNOWN-CONTACT>",
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
    def markDelivered(self, when: Timestamp) -> None:
        return super().markDelivered(when)

    def markRead(self, when: Timestamp = None, sendReceipt: bool = True) -> None:
        if (sendReceipt == True):
            when = self.__sendReceipt__('read')
        elif (when == None):
            when = Timestamp(now=True)
        self.__setExpiry__(when)
        return super().markRead(when)

    def markViewed(self, when: Timestamp = None, sendReceipt: bool = True) -> None:
        if (sendReceipt == True):
            when = self.__sendReceipt__('viewed')
        elif (when == None):
            when = Timestamp(now=True)
        self.__setExpiry__(when)
        return super().markViewed(when)

    def getQuote(self) -> Quote:
        quote: Quote
        if (self.recipientType == 'contact'):
            quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.sender)
        elif (self.recipientType == 'group'):
            quote = Quote(configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                          timestamp=self.timestamp, author=self.sender, text=self.body, mentions=self.mentions,
                          conversation=self.recipient)
        else:
            raise ValueError("invalid recipientType in RecievedMessage.getQuote")
        return quote

    def parseMentions(self) -> str:
        return self.mentions.__parseMentions__(self.body)

    def react(self, emoji: str) -> tuple[bool, Reaction | str]:
        # Argument check:
        if (isinstance(emoji, str) == False):
            __typeError__('emoji', "str, len = 1|2", emoji)
        if (len(emoji) != 1 and len(emoji) != 2):
            errorMessage = "emoji must be str of len 1|2"
            raise ValueError(errorMessage)
        # Create reaction
        if (self.recipientType == 'contact'):
            reaction = Reaction(commandSocket=self._commandSocket, accountId=self._accountId,
                                configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, recipient=self.sender, emoji=emoji,
                                targetAuthor=self.sender,
                                targetTimestamp=self.timestamp)
        elif (self.recipientType == 'group'):
            reaction = Reaction(commandSocket=self._commandSocket, accountId=self._accountId,
                                configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, recipient=self.recipient, emoji=emoji,
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
