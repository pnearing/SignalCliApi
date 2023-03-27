#!/usr/bin/env python3

from typing import Callable, Optional
import sys
import socket
import threading
import json

from .signalAccount import Account
from .signalCommon import __socket_create__, __socket_connect__, __socket_close__, __socket_receive__, __socket_send__
from .signalGroupUpdate import GroupUpdate
from .signalMessage import Message
from .signalReaction import Reaction
from .signalReceipt import Receipt
from .signalReceivedMessage import ReceivedMessage
from .signalSticker import StickerPacks
from .signalStoryMessage import StoryMessage
from .signalSyncMessage import SyncMessage
from .signalTypingMessage import TypingMessage
from .signalTimestamp import Timestamp

DEBUG: bool = False


class ReceiveThread(threading.Thread):
    def __init__(self,
                 server_address: tuple[str, int] | str,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 account: Account,
                 all_messages_callback: Optional[Callable] = None,
                 received_message_callback: Optional[Callable] = None,
                 receipt_message_callback: Optional[Callable] = None,
                 sync_message_callback: Optional[Callable] = None,
                 typing_message_callback: Optional[Callable] = None,
                 story_message_callback: Optional[Callable] = None,
                 payment_message_callback: Optional[Callable] = None,
                 reaction_message_callback: Optional[Callable] = None,
                 call_message_callback: Optional[Callable] = None,
                 ) -> None:  # Create the reception process:

        super().__init__(None)
        self._command_socket: socket.socket = command_socket
        self._config_path: str = config_path
        self._account: Account = account
        self._sticker_packs: StickerPacks = sticker_packs
        self._all_msg_cb: Optional[Callable] = all_messages_callback
        self._recv_msg_cb: Optional[Callable] = received_message_callback
        self._rcpt_msg_cb: Optional[Callable] = receipt_message_callback
        self._sync_msg_cb: Optional[Callable] = sync_message_callback
        self._type_msg_cb: Optional[Callable] = typing_message_callback
        self._stry_msg_cb: Optional[Callable] = story_message_callback
        self._pymt_msg_cb: Optional[Callable] = payment_message_callback
        self._ract_msg_cb: Optional[Callable] = reaction_message_callback
        self._call_msg_cb: Optional[Callable] = call_message_callback
        self._subscription_id: Optional[int] = None
        self._receive_socket: socket.socket = __socket_create__(server_address)
        __socket_connect__(self._receive_socket, server_address)
        return

    def run(self):
        # Do send sync request if we're not the primary device.
        if self._account.device_id != 1:
            # Create sync request object and json command string:
            sync_request_command_obj = {
                "jsonrpc": "2.0",
                "contact_id": 10,
                "method": "sendSyncRequest",
                "params": {
                    "account": self._account.number,
                }
            }
            json_command_str = json.dumps(sync_request_command_obj) + '\n'
            # Send the request to signal:
            __socket_send__(self._receive_socket, json_command_str)
            response_str = __socket_receive__(self._receive_socket)
            # Parse response:
            message_obj: dict[str, object] = json.loads(response_str)
            # print(responseObj)
            # Check for error:
            if 'error' in message_obj.keys():
                if DEBUG:
                    errorMessage = "WARNING:Signal Error while sending sync request. Code: %i, Message: %s" % (
                        message_obj['error']['code'],
                        message_obj['error']['message'])
                    print(errorMessage, file=sys.stderr)

        # Create receive object and json command string:
        start_receive_command_object = {
            "jsonrpc": "2.0",
            "contact_id": 1,
            "method": "subscribeReceive",
            "params": {
                "account": self._account.number,
            }
        }
        json_command_str = json.dumps(start_receive_command_object) + '\n'
        # Communicate start receive with signal:
        __socket_send__(self._receive_socket, json_command_str)
        response_str = __socket_receive__(self._receive_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        self._subscription_id = response_obj['result']
        ########### START RECEIVE LOOP ##################
        while self._subscription_id is not None:
            # Blocks until message received:
            try:
                message_str = __socket_receive__(self._receive_socket)
            except:
                break
            # Delay processing until messages are finished sending:
            if self._account.messages._sending:
                if DEBUG:
                    infoMessage = "INFO: Sending a message, delaying processing until complete."
                    print(infoMessage, file=sys.stderr)
            while self._account.messages._sending:
                pass
            # Parse incoming message:
            message_obj: dict = json.loads(message_str)
            if 'method' in message_obj.keys() and message_obj['method'] == 'receive':
                envelopeDict: dict = message_obj['params']['envelope']
                #### Data Message #####
                if 'dataMessage' in envelopeDict.keys():
                    dataMessage: dict[str, object] = envelopeDict['dataMessage']
                    ############### REACTIONS ##########################
                    # Create reaction Message:
                    if 'reaction' in dataMessage.keys():
                        message = Reaction(
                            command_socket=self._command_socket, account_id=self._account.number,
                            config_path=self._config_path, contacts=self._account.contacts,
                            groups=self._account.groups, devices=self._account.devices,
                            this_device=self._account.device, raw_message=envelopeDict
                        )
                        # Parse reaction and call the reaction callback:
                        if DEBUG:
                            print("Parsing Reaction...", file=sys.stderr)
                        self._account.messages.__parse_reaction__(message)
                        # self._account.messages.append(message)
                        if self._ract_msg_cb is not None:
                            self._ract_msg_cb(self._account, message)
                    ################### GROUP UPDATES ###########################
                    else:
                        is_group_update: bool
                        try:
                            if dataMessage['groupInfo']['type'] == 'UPDATE':
                                is_group_update = True
                            else:
                                is_group_update = False
                        except KeyError:
                            is_group_update = False
                        if is_group_update:
                            message = GroupUpdate(
                                command_socket=self._command_socket, account_id=self._account.number,
                                config_path=self._config_path, contacts=self._account.contacts,
                                groups=self._account.groups, devices=self._account.devices,
                                this_device=self._account.device, raw_message=envelopeDict
                            )
                            if DEBUG:
                                print("Parsing group update.", file=sys.stderr)
                            message.recipient.__sync__()
                            self._account.messages.append(message)
                            if self._sync_msg_cb is not None:
                                self._sync_msg_cb(self._account, message)
                        ########################### Recieved Message ###################
                        else:
                            # Create Received message:
                            message = ReceivedMessage(
                                command_socket=self._command_socket, account_id=self._account.number,
                                config_path=self._config_path, contacts=self._account.contacts,
                                groups=self._account.groups, devices=self._account.devices,
                                this_device=self._account.device, sticker_packs=self._sticker_packs,
                                raw_message=envelopeDict,
                            )
                            # Sender is no longer typing:
                            message.sender.is_typing = False
                            # Append the message and call the data message callback:
                            self._account.messages.append(message)
                            if self._recv_msg_cb is not None:
                                self._recv_msg_cb(self._account, message)
                #### Receipt Message ####
                elif 'receiptMessage' in envelopeDict.keys():
                    message = Receipt(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, raw_message=envelopeDict
                    )
                    # Parse receipt:
                    if DEBUG:
                        print("Parsing receipt...", file=sys.stderr)
                    self._account.messages.__parse_receipt__(message)
                    # Call receipt callback:
                    if self._rcpt_msg_cb is not None:
                        self._rcpt_msg_cb(self._account, message)
                #### Sync Message #####
                elif 'sync_message' in envelopeDict.keys():
                    if envelopeDict['sync_message'] == {}:
                        if DEBUG:
                            infoMessage = "INFO: Got empty sync message, skipping."
                            print(infoMessage, file=sys.stderr)
                            continue
                    if DEBUG:
                        print(envelopeDict)
                    message = SyncMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, stickerPacks=self._sticker_packs,
                        raw_message=envelopeDict
                    )
                    # Parse the sync message based on sync type:
                    if DEBUG:
                        print("Parsing sync message...", file=sys.stderr)
                    if (message.syncType == SyncMessage.TYPE_READ_MESSAGE_SYNC or
                            message.syncType == SyncMessage.TYPE_SENT_MESSAGE_SYNC):
                        if DEBUG:
                            print("Read messages.", file=sys.stderr)
                        self._account.messages.__parse_sync_message__(message)
                    elif message.syncType == SyncMessage.TYPE_CONTACT_SYNC:
                        if DEBUG:
                            print("Contact sync", file=sys.stderr)
                        self._account.contacts.__sync__()
                    elif message.syncType == SyncMessage.TYPE_GROUPS_SYNC:
                        if DEBUG:
                            print("Group sync", file=sys.stderr)
                        self._account.groups.__sync__()
                    elif message.syncType == SyncMessage.TYPE_BLOCKED_SYNC:
                        if DEBUG:
                            print("Blocked sync", file=sys.stderr)
                        self._account.contacts.__parse_sync_message__(message)
                        self._account.groups.__parse_sync_message__(message)
                    elif message.syncType == SyncMessage.TYPE_SENT_MESSAGE_SYNC:
                        if DEBUG:
                            print("Sent message sync", file=sys.stderr)
                        self._account.messages.__parse_sync_message__(message)
                    else:
                        print(envelopeDict, file=sys.stderr, flush=True)
                        print(message.syncType, file=sys.stderr, flush=True)
                        raise RuntimeError("Unhandled sync type")
                    # Append the message to messages:
                    if message is None:
                        raise RuntimeError("Shouldn't be none")
                    self._account.messages.append(message)
                    # Call sync message callback:
                    if self._sync_msg_cb is not None:
                        self._sync_msg_cb(self._account, message)
                #### Typing Message ####
                elif 'typingMessage' in envelopeDict.keys():
                    message = TypingMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.devices.get_account_device(), raw_message=envelopeDict
                    )
                    # Parse typing message:
                    if DEBUG:
                        print("DEBUG: parsing typing message...", file=sys.stderr)
                    if message.action == "STARTED":
                        message.sender.is_typing = True
                    elif message.action == "STOPPED":
                        message.sender.is_typing = False
                    else:
                        raise ValueError("invalid typing action: %s" % message.action)
                    # Append the typing message and call the typing call back:
                    self._account.messages.append(message)
                    if self._type_msg_cb is not None:
                        self._type_msg_cb(self._account, message)
                #### Story Message ####
                elif 'storyMessage' in envelopeDict.keys():
                    message = StoryMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, raw_message=envelopeDict
                    )
                    # print("DEBUG: ", envelopeDict)
                    self._account.messages.append(message)
                    if self._stry_msg_cb is not None:
                        self._stry_msg_cb(self._account, message)
                #### Call message ####
                elif 'callMessage' in envelopeDict.keys():
                    # TODO: Create call message class.
                    message = None
                    if self._call_msg_cb != None:
                        self._call_msg_cb(self._account, message)
                #### Unrecognized message ####
                else:
                    if DEBUG:
                        errorMessage = "DEBUG: Unrecognized envelope, perhaps a payment message."
                        print(errorMessage, file=sys.stderr)
                        print("DEBUG: ", envelopeDict.keys(), file=sys.stderr)
                        print("DEBUG: ", envelopeDict, file=sys.stderr)
                        continue
                # if (message != None):
                #     self._account.messages.append(message)
                #### Call all messages callback:
                if self._all_msg_cb is not None:
                    self._all_msg_cb(self._account, message)
            else:
                if DEBUG:
                    infoMessage = "DEBUG: Incoming data that's not a message.\nDEBUG: DATA =\n%s" % message_str
                    print(infoMessage, file=sys.stderr)
        return

    def stop(self):
        """Stop the reception."""
        self._subscription_id = None
        __socket_close__(self._receive_socket)
        return

