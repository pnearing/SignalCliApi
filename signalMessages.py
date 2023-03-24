#!/usr/bin/env python3

from typing import Optional, Iterable
import sys
import os
import socket
import json

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

global DEBUG
DEBUG: bool = True

class Messages(object):
    def __init__(self,
                    commandSocket: socket.socket,
                    configPath: str,
                    accountId: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    accountPath: str,
                    thisDevice: Device,
                    stickerPacks: StickerPacks,
                    doLoad:bool = False,
                ) -> None:
        
    # TODO: Argument checks:
# Set internal vars:
        self._commandSocket: socket.socket = commandSocket
        self._configPath: str = configPath
        self._accountId: str = accountId
        self._contacts: Contacts = contacts
        self._groups: Groups = groups
        self._devices: Device = devices
        self._thisDevice: Device = thisDevice
        self._stickerPacks: StickerPacks = stickerPacks
        self._filePath: str = os.path.join(accountPath, "messages.json")
# Set external properties:
        self.messages : list[SentMessage|ReceivedMessage] = []
        self.sync: list[GroupUpdate|SyncMessage] = []
        self.typing: list[TypingMessage] = []
        self.story: list[StoryMessage] = []
        # self.calls: list[]
        self._sending: bool = False
    # Do load:
        if (doLoad == True):
            try:
                self.__load__()
            except:
                if (DEBUG == True):
                    errorMessage = "warning, creating empy messages: %s" % self._filePath
                    print(errorMessage, file=sys.stderr)
                self.__save__()
        return

################################
# To / From Dict:
################################
    def __toDict__(self) -> dict:
        messagesDict = {
            "messages": [],
            "syncMessages": [],
            "typingMessages": [],
            "storyMessages": [],
        }
    # Store messages: SentMessage | ReceivedMessage
        for message in self.messages:
            messagesDict["messages"].append(message.__toDict__())
    # Store sync messages: (sync and group update)
        for message in self.sync:
            if (message == None): raise RuntimeError("WTF")
            messagesDict['syncMessages'].append(message.__toDict__())
    # Store typing messages: TypingMessage
        for message in self.typing:
            messagesDict['typingMessages'].append(message.__toDict__())
    # Store story messages: StoryMessage
        for message in self.story:
            messagesDict['storyMessages'].append(message.__toDict__())
        return messagesDict
    
    def __fromDict__(self, fromDict:dict) -> None:
    # Load messages: SentMessage | ReceivedMessage
        self.messages = []
        for messageDict in fromDict['messages']:
            if (messageDict['messageType'] == Message.TYPE_SENT_MESSAGE):
                message = SentMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                        configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                        devices=self._devices, thisDevice=self._thisDevice, stickerPacks=self._stickerPacks,
                                        fromDict=messageDict)
            
            elif (messageDict['messageType'] == Message.TYPE_RECEIVED_MESSAGE):
                message = ReceivedMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                            configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                            devices=self._devices, thisDevice=self._thisDevice,
                                            stickerPacks=self._stickerPacks, fromDict=messageDict)
            else:   
                errorMessage = "FATAL: Invalid message type in messages from_dict: %s" % fromDict['messageType']
                raise RuntimeError(errorMessage)
            self.messages.append(message)
    # Load sync messages: GroupUpdate | SyncMessage
        self.sync = []
        for messageDict in fromDict['syncMessages']:
            if (messageDict['messageType'] == Message.TYPE_GROUP_UPDATE_MESSAGE):
                message = GroupUpdate(command_socket=self._commandSocket, account_id=self._accountId,
                                      config_path=self._configPath, contacts=self._contacts, groups=self._groups,
                                      devices=self._devices, this_device=self._thisDevice, from_dict=messageDict)
            elif (messageDict['messageType'] == Message.TYPE_SYNC_MESSAGE):
                message = SyncMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                        configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                        devices=self._devices, thisDevice=self._thisDevice,
                                        stickerPacks=self._stickerPacks,fromDict=messageDict)
            else:
                errorMessage = "FATAL: Invalid message type in for sync messages in Messges.__from_dict__"
                raise RuntimeError(errorMessage)
            self.sync.append(message)
    # Load typing messages:
        self.typing = []
        for messageDict in fromDict['typingMessages']:
            message = TypingMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                        configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                        devices=self._devices, thisDevice=self._thisDevice, fromDict=messageDict)
            self.typing.append(message)
    # Load Story Messages:
        self.story = []
        for messageDict in fromDict['storyMessages']:
            message = StoryMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                    configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                    devices=self._devices, thisDevice=self._thisDevice, fromDict=messageDict)
            self.story.append(message)
        return

#################################
# Load / save:
#################################
    def __load__(self) -> None:
    # Try to open the file:
        try:
            fileHandle = open(self._filePath, 'r')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open '%s' for reading: %s" % (self._filePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Try to load the json from the file:
        try:
            messagesDict: dict = json.loads(fileHandle.read())
        except json.JSONDecodeError as e:
            errorMessage = "FATAL: Couldn't load json from '%s': %s" % (self._filePath, e.msg)
            raise RuntimeError(errorMessage)
    # Load the dict:
        self.__fromDict__(messagesDict)
        return

    def __save__(self) -> None:
    # Create messages Object, and json save string:
        messagesDict = self.__toDict__()
        jsonMessagesStr = json.dumps(messagesDict, indent=4)
    # Try to open the file for writing:
        try:
            fileHandle = open(self._filePath, 'w')
        except Exception as e:
            errorMessage = "FATAL: Failed to open '%s' for writing: %s" % (self._filePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Write to the file and close it.
        fileHandle.write(jsonMessagesStr)
        fileHandle.close()
        return
##################################
# Helpers:
##################################
    def __parseReaction__(self, reaction:Reaction) -> bool:
    # Get the messages from the recipients:
        searchMessages: list[Message] = []
        if (reaction.recipientType == 'contact'):
            messages = self.getBySender(reaction.recipient)
            searchMessages.extend(messages)
        elif (reaction.recipientType == 'group'):
            messages = self.getByRecipient(reaction.recipient)
            searchMessages.extend(messages)
        else:
        # Invalid recipient type:
            errorMessage = "Invalid reaction cannot parse."
            raise RuntimeError(errorMessage)
    # Find the message that was reacted to:
        reactedMessage = None
        for message in searchMessages:
            if (message.sender == reaction.targetAuthor):
                if (message.timestamp == reaction.targetTimestamp):
                    reactedMessage = message
    # If the message isn't in history do nothing:
        if (reactedMessage == None):
            return False
    # Have the message add / change / remove the reaction:
        reactedMessage.reactions.__parse__(reaction)
        return True
    
    def __parseReceipt__(self, receipt:Receipt) -> None:
        sentMessages = [ message for message in self.messages if isinstance(message, SentMessage)]
        for message in sentMessages:
            for timestamp in receipt.timestamps:
                if (message.timestamp == timestamp):
                    message.__parseReceipt__(receipt)
                    self.__save__()
        return
    
    def __parseReadMessageSync__(self, syncMessage:SyncMessage) -> None:
        for contact, timestamp in syncMessage.readMessages:
            searchMessages = self.getBySender(contact)
            for message in searchMessages:
                if (message.timestamp == timestamp):
                    if (message.isRead == False):
                        if (isinstance(message, ReceivedMessage) == True):
                            message.markRead(when=syncMessage.timestamp, sendReceipt=False)
                        else:
                            message.markRead(when=syncMessage.timestamp)
        return
    
    def __parseSentMessageSync__(self, syncMessage:SyncMessage) -> None:
        message = SentMessage(commandSocket=self._commandSocket, accountId=self._accountId, configPath=self._configPath,
                                contacts=self._contacts, groups=self._groups, devices=self._devices,
                                thisDevice=self._thisDevice, stickerPacks=self._stickerPacks,
                                rawMessage=syncMessage.rawSentMessage)
        self.append(message)
        return
    
    def __parseSyncMessage__(self, syncMessage:SyncMessage) -> None:
        if (syncMessage.syncType == SyncMessage.TYPE_READ_MESSAGE_SYNC):
            self.__parseReadMessageSync__(syncMessage)
        elif (syncMessage.syncType == SyncMessage.TYPE_SENT_MESSAGE_SYNC):
            self.__parseSentMessageSync__(syncMessage)
        else:
            errorMessage = "Can only parse SyncMessage.TYPE_READ_MESSAGE_SYNC and SyncMessage.TYPE_SENT_MESSAGE_SYNC not: %i" % syncMessage.syncType
            raise TypeError(errorMessage)
        self.__save__()
        return
##################################
# Getters:
##################################
    def getByTimestamp(self, timestamp:Timestamp) -> list[Message]:
        if (isinstance(timestamp, Timestamp) == False):
            __type_error__("timestamp", "Timestamp", timestamp)
        messages = [message for message in self.messages if message.timestamp == timestamp]
        return messages
    
    def getByRecipient(self, recipient:Group|Contact) -> list[Message]:
        if (isinstance(recipient, Contact) == False and isinstance(recipient, Group) == False):
            __type_error__("recipient", "Contact | Group", recipient)
        messages = [ message for message in self.messages if message.recipient == recipient ]
        return messages
    
    def getBySender(self, sender:Contact) -> list[Message]:
        if (isinstance(sender, Contact) == False):
            __type_error__("sender", "Contact", sender)
        messages = [message for message in self.messages if message.sender == sender]
        return messages
    
    def getConversation(self, target:Contact|Group) -> list[Message]:
        returnMessages = []
        if (isinstance(target, Contact) == True):
            selfContact = self._contacts.get_self()
            for message in self.messages:
                if (message.sender == selfContact and message.recipient == target):
                    returnMessages.append(message)
                elif(message.sender == target and message.recipient == selfContact):
                    returnMessages.append(message)
        elif (isinstance(target, Group) == True):
            for message in self.messages:
                if (message.recipient == target):
                    returnMessages.append(message)
        else:
            __type_error__("target", "Contact | Group", target)
        return returnMessages

    def find(self, author:Contact, timestamp:Timestamp, conversation:Contact | Group) -> Message | None:
    # Validate  author:
        targetAuthor: Contact
        if (isinstance(author, Contact) == True):
            targetAuthor = author
        else:
            __type_error__("author", "Contact", author)
    # Validate recipient:
        targetConversation: Contact | Group
        if (isinstance(conversation, Contact) == True):
            targetConversation = conversation
        elif (isinstance(conversation, Group) == True):
            targetConversation = conversation
        else:
            __type_error__("recpipient", "Contact | Group", conversation)
    # Validate timestamp:
        targetTimestamp: Timestamp
        if (isinstance(timestamp, Timestamp) == True):
            targetTimestamp = timestamp
        else:
            __type_error__("timestamp", "Timestamp", timestamp)
    # Find Message:
        searchMessages = self.getConversation(targetConversation)
        for message in searchMessages:
            if (message.sender == targetAuthor and message.timestamp == targetTimestamp):
                return message
        return None
    
    def getQuoted(self, quote:Quote) -> Optional[SentMessage | ReceivedMessage]:
        if (isinstance(quote, Quote) == False):
            __type_error__("quote", "Quote", quote)
        searchMessages = self.getConversation(quote.conversation)
        for message in searchMessages:
            if (message.sender == quote.author):
                if (message.timestamp == quote.timestamp):
                    return message
        return None
    
    def getSent(self) -> list[SentMessage]:
        return [message for message in self.messages if isinstance(message, SentMessage)]
##################################
# Methods:
##################################
    def append(self, message:Message) -> None:
        if (message == None):
            if (DEBUG == True):
                print("ATTEMPTING TO APPEND NONE TYPE to messages", file=sys.stderr)
            raise RuntimeError()
            return
        if (isinstance(message, SentMessage) == True or isinstance(message, ReceivedMessage) == True):
            self.messages.append(message)
        elif (isinstance(message, GroupUpdate) == True or isinstance(message, SyncMessage) == True):
            self.sync.append(message)
        elif (isinstance(message, TypingMessage) == True):
            self.typing.append(message)
        
        self.__save__()
        return
    
    def sendMessage(self,
                        recipients: Iterable[Contact | Group] | Contact | Group,
                        body: Optional[str] = None,
                        attachments: Optional[Iterable[Attachment | str]| Attachment | str] = None,
                        mentions: Optional[Iterable[Mention] | Mentions | Mention] = None,
                        quote: Optional[Quote] = None,
                        sticker: Optional[Sticker] = None,
                        preview: Optional[Preview] = None,
                    ) -> tuple[tuple[bool, Contact, SentMessage | str]]:
    # Validate recipients:
        recipientType: str
        targetRecipients: list[Contact|Group]
        if (isinstance(recipients, Contact) == True):
            recipientType = 'contact'
            targetRecipients = [recipients]
        elif (isinstance(recipients, Group) == True):
            recipientType = 'group'
            targetRecipients = [ recipients ]
        elif (isinstance(recipients, Iterable) == True):
            targetRecipients = []
            i = 0
            checkType = None
            for recipient in recipients:
                if (isinstance(recipient, Contact) == False and isinstance(recipient, Group) == False):
                    __type_error__("recipients[%i]" % i, "Contact | Group", recipient)
                if (i == 0):
                    checkType = type(recipient)
                    if (isinstance(recipient, Contact) == True):
                        recipientType = 'contact'
                    else:
                        recipientType = 'group'
                elif (isinstance(recipient, checkType) == False):
                    __type_error__("recipients[%i]", str(type(checkType)), recipient)
                i = i + 1
                targetRecipients.append(recipient)
        else:
            __type_error__("recipients", "Iterable[Contact | Group] | Contact | Group", recipients)
        if (len(targetRecipients) == 0):
            raise ValueError("recipients cannot be of zero length")
    # Validate body Type and value:
        if (body != None and isinstance(body, str) == False):
            __type_error__("body", "str | None", body)
        # elif (body != None and len(body) == 0):
            # raise ValueError("body cannot be empty string")
    # Validate attachments:
        targetAttachments: Optional[list[Attachment]] = None
        if (attachments != None):
            if (isinstance(attachments, Attachment) == True):
                targetAttachments = [ attachments ]
            elif (isinstance(attachments, str) == True):
                targetAttachments = [ Attachment(configPath=self._configPath, localPath=attachments) ]
            elif (isinstance(attachments, Iterable) == True):
                targetAttachments = []
                i = 0
                for attachment in attachments:
                    if (isinstance(attachment, Attachment) == False and isinstance(attachment, str) == False):
                        __type_error__("attachments[%i]" % i, "Attachment | str", attachment)
                    if (isinstance(attachment, Attachment) == True):
                        targetAttachments.append(attachment)
                    else:
                        targetAttachments.append(Attachment(configPath=self._configPath, localPath=attachment))
            else:
                __type_error__("attachments", "Iterable[Attachment | str] | Attachment | str", attachments)
        if (targetAttachments != None and len(targetAttachments) == 0):
            raise ValueError("attachments cannot be empty")
    # Validate mentions:
        targetMentions: Optional[list[Mention] | Mentions] = None
        if (mentions != None):
            if (isinstance(mentions, Mentions)):
                targetMentions = mentions
            elif (isinstance(mentions, Mention) == True):
                targetMentions = [ mentions ]
            elif (isinstance(mentions, Iterable) == True):
                targetMentions = []
                i = 0
                for mention in mentions:
                    if (isinstance(mention, Mention) == False):
                        __type_error__("mentions[%i]" % i, "Mention", mention)
                    targetMentions.append( mention )
            else:
                __type_error__("mentions", "Optional[Iterable[Mention] | Mention]", mentions)
        if (targetMentions != None and len(targetMentions) ==0):
            raise ValueError("mentions cannot be empty")
    # Validate quote:
        if (quote != None and isinstance(quote, Quote) == False):
            __type_error__("quote", "SentMessage | RecieivedMessage", quote)
    # Validate sticker:
        if (sticker != None):
            if (isinstance(sticker, Sticker) == False):
                raise __type_error__("sticker", "Sticker", sticker)
    # Validate preview:
        if (preview != None):
            if (isinstance(preview, Preview) == False):
                __type_error__("preview", "Preview", preview)
            if (body.find(preview.url) == -1):
                errorMessage = "FATAL: error while sending message. preview URL must appear in body of message."
                raise ValueError(errorMessage)
    # Validate conflicting options:
        if (sticker != None):
            if (body != None or attachments != None):
                errorMessage = "If body or attachments are defined, sticker must be None."
                raise ValueError(errorMessage)
            if (mentions != None):
                errorMessage = "If sticker is defined, mentions must be None"
                raise ValueError(errorMessage)
            if (quote != None):
                errorMessage = "If sticker is defined, quote must be None"
                raise ValueError(errorMessage)
    # Create send message command object:
        sendCommandObj = {
            "jsonrpc": "2.0",
            "contact_id": 2,
            "method": "send",
            "params": {
                "account": self._accountId,
            }
        }
    # Add recipients:
        if (recipientType == 'group'):
            sendCommandObj['params']['groupId'] = []
            for group in targetRecipients:
                sendCommandObj['params']['groupId'].append(group.get_id())
        elif (recipientType == 'contact'):
            sendCommandObj['params']['recipient'] = []
            for contact in targetRecipients:
                sendCommandObj['params']['recipient'].append(contact.get_id())
        else:
            raise ValueError("recipientType must be either 'contact' or 'group'")
    # Add body:
        if (body != None):
            sendCommandObj['params']['message'] = body
    # Add attachments:
        if (targetAttachments != None):
            sendCommandObj['params']['attachments'] = []
            for attachment in targetAttachments:
                sendCommandObj['params']['attachments'].append(attachment.localPath)
    # Add mentions:
        if (targetMentions != None):
            sendCommandObj['params']['mention'] = []
            for mention in targetMentions:
                sendCommandObj['params']['mention'].append(str(mention))
    # Add quote:
        if (quote != None):
            sendCommandObj['params']['quoteTimestamp'] = quote.timestamp.timestamp
            sendCommandObj['params']['quoteAuthor'] = quote.author.get_id()
            sendCommandObj['params']['quoteMessage'] = quote.text
            if (quote.mentions != None):
                sendCommandObj['params']['quoteMention'] = []
                for mention in quote.mentions:
                    sendCommandObj['params']['quoteMention'].append(str(mention))
    # Add sticker:
        if (sticker != None):
            sendCommandObj['params']['sticker'] = str(sticker)
    # Add preview:
        if (preview != None):
            sendCommandObj['params']['previewUrl'] = preview.url
            sendCommandObj['params']['previewTitle'] = preview.title
            sendCommandObj['params']['previewDescription'] = preview.description
            if (preview.image != None):
                sendCommandObj['params']['previewImage'] = preview.image.localPath
    # Create json command string:
        jsonCommandStr = json.dumps(sendCommandObj) + '\n'
    # Mark system as sending:
        self._sending = True
    # Communicate with signal:
        __socket_send__(self._commandSocket, jsonCommandStr)
        responseStr = __socket_receive__(self._commandSocket)
    # Parse response:
        responseObj: dict[str, object] = json.loads(responseStr)
        # print(responseObj)
    # Check for error:
        if ('error' in responseObj.keys()):
            errorMessage = "ERROR: failed to send message, signal error. Code: %i Message: %s" % ( responseObj['error']['code'],
                                                                                                responseObj['error']['message'])
            if (DEBUG == True):
                print(errorMessage, file=sys.stderr)
                self._sending = False
                returnValue = []
                for recipient in targetRecipients:
                    if (recipientType == 'group'):
                        for member in group.members:
                            returnValue.append( (False, member, errorMessage) )
                    else:
                        returnValue.append( (False, recipient, errorMessage) )
                return tuple(returnValue)
    # Some messages sent, some may have failed.
        resultsList: list[dict[str, object]] = responseObj['result']['results']
    # Gather timestamp:
        timestamp = Timestamp(timestamp=responseObj['result']['timestamp'])
    # Parse results:
        returnValue = []
        if (recipientType == 'group'):
            sentMessages: list[SentMessage] = []
            for recipient in targetRecipients:
                sentMessage = SentMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                            configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                            devices=self._devices, thisDevice=self._thisDevice,
                                            stickerPacks=self._stickerPacks, recipient=recipient,
                                            timestamp=timestamp, body=body, attachments=targetAttachments,
                                            mentions=targetMentions, quote=quote, sticker=sticker, isSent=True)
                self.append(sentMessage)
                sentMessages.append(sentMessage)
            for result in resultsList:
            # Gather group and contact:
                groupId = result['groupId']
                added, group = self._groups.__get_or_add__("<UNKNOWN-GROUP>", groupId)
                contactId = result['recipientAddress']['number']
                if (contactId == None):
                    contactId = result['recipientAddress']['uuid']
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)
            # Message sent successfully
                if (result['type'] == "SUCCESS"):
                    for message in sentMessages:
                        if (message.recipient == group):
                            message.sentTo.append(contact)
                            returnValue.append( (True, contact, message) )
            # Message failed to sent:
                else:
                    returnValue.append( (False, contact, result['type']) )
            self._sending = False
            return tuple(returnValue)
        else:
            for result in resultsList:
            # Gather contact:
                contactId = result['recipientAddress']['number']
                if (contactId == None):
                    contactId = result['recipientAddress']['uuid']
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contactId)

            # Message Sent successfully:
                if (result['type'] == 'SUCCESS'):
                # Create sent message
                    sentMessage = SentMessage(commandSocket=self._commandSocket, accountId=self._accountId,
                                                configPath=self._configPath, contacts=self._contacts, groups=self._groups,
                                                devices=self._devices, thisDevice=self._thisDevice,
                                                stickerPacks=self._stickerPacks, recipient=contact,
                                                timestamp=timestamp, body=body, attachments=targetAttachments,
                                                mentions=targetMentions, quote=quote, sticker=sticker, isSent=True,
                                                sentTo=targetRecipients)
                    returnValue.append((True, contact, sentMessage))
                    self.append(sentMessage)
                    self.__save__()
            # Message failed to send:
                else:
                    returnValue.append((False, contact, result['type']))
    # Mark sending finished.
            self._sending = False
            return tuple(returnValue)
        
