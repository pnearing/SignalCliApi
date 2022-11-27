#!/usr/bin/env python3

from typing import Callable, Optional
import sys
import socket
import threading
import json

from signalAccount import Account
from signalCommon import __socketCreate__, __socketConnect__, __socketClose__, __socketReceive__, __socketSend__
from signalGroupUpdate import GroupUpdate
from signalMessage import Message
from signalReaction import Reaction
from signalReceipt import Receipt
from signalReceivedMessage import ReceivedMessage
from signalSticker import StickerPacks
from signalStoryMessage import StoryMessage
from signalSyncMessage import SyncMessage
from signalTypingMessage import TypingMessage
from signalTimestamp import Timestamp

global DEBUG
DEBUG: bool = True

class ReceiveThread(threading.Thread):
    def __init__(self,
                    serverAddress: tuple[str, int] | str,
                    commandSocket: socket.socket,
                    configPath:str,
                    stickerPacks: StickerPacks,
                    account: Account,
                    allMessagesCallback: Optional[Callable] = None,
                    receivedMessageCallback: Optional[Callable] = None,
                    receiptMessageCallback: Optional[Callable] = None,
                    syncMessageCallback: Optional[Callable] = None,
                    typingMessageCallback: Optional[Callable] = None,
                    storyMessageCallback: Optional[Callable] = None,
                    paymentMessageCallback: Optional[Callable] = None,
                    reactionMessageCallback: Optional[Callable] = None,
                    callMessageCallback: Optional[Callable] = None,
                ) -> None:    # Create the receive process:
        
        super().__init__(None)
        self._commandSocket: socket.socket = commandSocket
        self._configPath: str = configPath
        self._account: Account = account
        self._stickerPacks: StickerPacks = stickerPacks
        self._allMsgCb: Optional[Callable] = allMessagesCallback
        self._recvMsgCb: Optional[Callable] = receivedMessageCallback
        self._rcptMsgCb: Optional[Callable] = receiptMessageCallback
        self._syncMsgCb: Optional[Callable] = syncMessageCallback
        self._typeMsgCb: Optional[Callable] = typingMessageCallback
        self._stryMsgCb: Optional[Callable] = storyMessageCallback
        self._pymtMsgCb: Optional[Callable] = paymentMessageCallback
        self._ractMsgCb: Optional[Callable] = reactionMessageCallback
        self._callMsgCb: Optional[Callable] = callMessageCallback
        self._subscriptionId : Optional[int]
        self._receiveSocket: socket.socket = __socketCreate__(serverAddress)
        __socketConnect__(self._receiveSocket, serverAddress)
        return

    def run(self):
    # Do send sync request if we're not the primary device.
        if (self._account.deviceId != 1):
        # Create sync request object and json command string:
            syncRequestCommandObj = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "sendSyncRequest",
                "params": {
                    "account": self._account.number,
                }
            }
            jsonCommandStr = json.dumps(syncRequestCommandObj) + '\n'
        # Send the request to signal:
            __socketSend__(self._receiveSocket, jsonCommandStr)
            responseStr = __socketReceive__(self._receiveSocket)
        # Parse response:
            messageObj:dict[str, object] = json.loads(responseStr)
            # print(responseObj)
        # Check for error:
            if ('error' in messageObj.keys()):
                if (DEBUG == True):
                    errorMessage = "WARNING:Signal Error while sending sync request. Code: %i, Message: %s" % (messageObj['error']['code'],
                                                                                                messageObj['error']['message'])
                    print(errorMessage, file=sys.stderr)

    # Create receive object and json command string:
        startReceiveCommandObject = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribeReceive",
            "params": {
                "account": self._account.number,
            }
        }
        jsonCommandStr = json.dumps(startReceiveCommandObject) + '\n'
    # Communicate start recieve with signal:
        __socketSend__(self._receiveSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._receiveSocket)
    # Parse response:
        responseObj: dict = json.loads(responseStr)
        self._subscriptionId = responseObj['result']
    ########### START RECEIVE LOOP ##################
        while(self._subscriptionId != None):
        # Blocks unil message received:
            try:
                messageStr = __socketReceive__(self._receiveSocket)
            except:
                break
        # Delay processing until messages are finished sending:
            if ( self._account.messages._sending == True):
                if (DEBUG == True):
                    infoMessage = "INFO: Sending a message, delaying processing until complete."
                    print(infoMessage, file=sys.stderr)
            while (self._account.messages._sending == True):
                pass
        # Parse incoming message:
            messageObj:dict = json.loads(messageStr)
            if ('method' in messageObj.keys() and messageObj['method'] == 'receive'):
                envelopeDict:dict = messageObj['params']['envelope']
            #### Data Message #####
                if ('dataMessage' in envelopeDict.keys()):
                    dataMessage:dict[str, object] = envelopeDict['dataMessage']
            ############### REACTIONS ##########################
                # Create reaction Message:
                    if('reaction' in dataMessage.keys()):
                        message = Reaction(
                                            commandSocket=self._commandSocket, accountId=self._account.number,
                                            configPath=self._configPath, contacts=self._account.contacts,
                                            groups=self._account.groups, devices=self._account.devices,
                                            thisDevice=self._account.device, rawMessage=envelopeDict
                                        )
                    # Parse reaction and call the reaction callback:
                        if (DEBUG == True):
                            print("Parsing Reaction...", file=sys.stderr)
                        self._account.messages.__parseReaction__(message)
                        # self._account.messages.append(message)
                        if (self._ractMsgCb != None): self._ractMsgCb(self._account, message)
            ################### GROUP UPDATES ###########################
                    else:
                        isGroupUpdate: bool
                        try:
                            if (dataMessage['groupInfo']['type'] == 'UPDATE'):
                                isGroupUpdate = True
                            else:
                                isGroupUpdate = False
                        except KeyError:
                            isGroupUpdate = False
                        if (isGroupUpdate == True):
                            message = GroupUpdate(
                                                    commandSocket=self._commandSocket, accountId=self._account.number,
                                                    configPath=self._configPath, contacts=self._account.contacts,
                                                    groups=self._account.groups, devices=self._account.devices,
                                                    thisDevice=self._account.device, rawMessage=envelopeDict
                                                )
                            if (DEBUG == True):
                                print("Parsing group update.", file=sys.stderr)
                            message.recipient.__sync__()
                            self._account.messages.append(message)
                            if (self._syncMsgCb != None): self._syncMsgCb(self._account, message)
########################### Recieved Message ###################
                        else:
                    # Create Received message:
                            message = ReceivedMessage(
                                                        commandSocket=self._commandSocket, accountId=self._account.number,
                                                        configPath=self._configPath, contacts=self._account.contacts,
                                                        groups=self._account.groups, devices=self._account.devices, 
                                                        thisDevice=self._account.device, stickerPacks=self._stickerPacks,
                                                        rawMessage=envelopeDict,
                                                    )
                        # Sender is no longer typing:
                            message.sender.isTyping = False
                        # Append the message and call the data message callback:
                            self._account.messages.append(message)
                            if (self._recvMsgCb != None): self._recvMsgCb(self._account, message)
            #### Receipt Message ####
                elif ('receiptMessage' in envelopeDict.keys()):
                    message = Receipt(
                                        commandSocket=self._commandSocket, accountId=self._account.number,
                                        configPath=self._configPath, contacts=self._account.contacts,
                                        groups=self._account.groups, devices=self._account.devices,
                                        thisDevice=self._account.device, rawMessage=envelopeDict
                                    )
                # Parse receipt:
                    if (DEBUG == True):
                        print("Parsing receipt...", file=sys.stderr)
                    self._account.messages.__parseReceipt__(message)
                # Call receipt callback:
                    if (self._rcptMsgCb != None): self._rcptMsgCb(self._account, message)
            #### Sync Message #####
                elif ('syncMessage' in envelopeDict.keys()):
                    if (envelopeDict['syncMessage'] == {}):
                        if (DEBUG == True):
                            infoMessage = "INFO: Got empty sync message, doing nothing."
                            print(infoMessage, file=sys.stderr)
                            continue
                    print(envelopeDict)
                    message = SyncMessage(
                                        commandSocket=self._commandSocket, accountId=self._account.number,
                                        configPath=self._configPath, contacts=self._account.contacts,
                                        groups=self._account.groups, devices=self._account.devices,
                                        thisDevice=self._account.device, stickerPacks=self._stickerPacks,
                                        rawMessage=envelopeDict
                                    )
                # Parse the sync message based on sync type:
                    if (DEBUG == True):
                        print("Parsing sync message...", file=sys.stderr)
                    if (message.syncType == SyncMessage.TYPE_READ_MESSAGE_SYNC or 
                                                                message.syncType == SyncMessage.TYPE_SENT_MESSAGE_SYNC):
                        self._account.messages.__parseSyncMessage__(message)
                    elif (message.syncType == SyncMessage.TYPE_CONTACT_SYNC):
                        self._account.contacts.__sync__()
                    elif (message.syncType == SyncMessage.TYPE_GROUPS_SYNC):
                        self._account.groups.__sync__()
                    elif (message.syncType == SyncMessage.TYPE_BLOCKED_SYNC):
                        self._account.contacts.__parseSyncMessage__(message)
                        self._account.groups.__parseSyncMessage__(message)
                # Append the message to messages:
                    self._account.messages.append(message)
                # Call sync message callback:
                    if (self._syncMsgCb != None): self._syncMsgCb(self._account, message)
            #### Typing Message ####
                elif ('typingMessage' in envelopeDict.keys()):
                    message = TypingMessage(
                                            commandSocket=self._commandSocket, accountId=self._account.number,
                                            configPath=self._configPath, contacts=self._account.contacts,
                                            groups=self._account.groups, devices=self._account.devices,
                                            thisDevice=self._account.devices.getAccountDevice(), rawMessage=envelopeDict
                                        )
                # Parse typing message:
                    if (DEBUG == True):
                        print("DEBUG: parsing typing message...", file=sys.stderr)
                    if (message.action == "STARTED"):
                        message.sender.isTyping = True
                    elif (message.action == "STOPPED"):
                        message.sender.isTyping = False
                    else:
                        raise ValueError("invalid typing action: %s" % message.action)
                # Append the typing message and call the typing call back:
                    self._account.messages.append(message)
                    if (self._typeMsgCb != None): self._typeMsgCb(self._account, message)
            #### Story Message ####
                elif ('storyMessage' in envelopeDict.keys()):
                    message = StoryMessage(
                                            commandSocket=self._commandSocket, accountId=self._account.number,
                                            contacts=self._account.contacts, groups=self._account.groups,
                                            devices=self._account.devices, thisDevice=self._account.device,
                                            rawMessage=envelopeDict
                                        )
                    # print("DEBUG: ", envelopeDict)
                    self._account.messages.append(message)
                    if (self._stryMsgCb != None): self._stryMsgCb(self._account, message)
            #### Call message ####
                elif ('callMessage' in envelopeDict.keys()):
                    message = None
                    if (self._callMsgCb != None): self._callMsgCb(self._account, message)
            #### Unrecognized message ####
                else:
                    if (DEBUG == True):
                        errorMessage = "DEBUG: Unrecognized envelope, perhaps a payment message."
                        print(errorMessage, file=sys.stderr)
                        print("DEBUG: ", envelopeDict.keys(), file=sys.stderr)
                        print("DEBUG: ", envelopeDict, file=sys.stderr)
                        continue
                # if (message != None):
                #     self._account.messages.append(message)
    #### Call all messages callback:
                if (self._allMsgCb != None): self._allMsgCb(self._account, message)
            else:
                if (DEBUG == True):
                    infoMessage = "DEBUG: Incoming data that's not a message.\nDEBUG: DATA =\n%s" % messageStr
                    print(infoMessage, file=sys.stderr)

        return
    
    def stop(self):
    # build stop recieve command Obj and json command string:
        # stopReceiveCommandObj = {
        #     "jsonrpc": "2.0",
        #     "id": 0,
        #     "method": "unsubscribeReceive",
        #     "params": {
        #         "subscriptionId": self._subscriptionId,
        #     }
        # }
        # jsonCommandStr = json.dumps(stopReceiveCommandObj) + '\n'
        # __socketSend__(self._socket, jsonCommandStr)
        self._subscriptionId = None
        __socketClose__(self._receiveSocket)
        return
    
    # def __del__(self):
    #     try:
    #         self._process.terminate()
    #     except:
    #         pass
    #     return