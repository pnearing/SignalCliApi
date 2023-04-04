#!/usr/bin/env python3

from typing import Callable, Optional
import sys
import socket
import threading
import json

from .signalAccount import Account
from .signalCallMessage import CallMessage
from .signalCommon import __socket_create__, __socket_connect__, __socket_close__, __socket_receive__, __socket_send__, __type_error__
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


# noinspection SpellCheckingInspection
class ReceiveThread(threading.Thread):
    """The reception thread."""
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
                 do_expunge: bool = True,
                 ) -> None:  # Create the reception process:

        super().__init__(None)
        # Argument checks:
        if not isinstance(server_address, tuple) and not isinstance(server_address, str):
            __type_error__("server_address", "tuple | str", server_address)
        if not isinstance(command_socket, socket.socket):
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        if not isinstance(sticker_packs, StickerPacks):
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(account, Account):
            __type_error__("account", "Account", account)
        if all_messages_callback is not None and not callable(all_messages_callback):
            __type_error__("all_messages_callback", "Optional[Callable]", all_messages_callback)
        if received_message_callback is not None and not callable(received_message_callback):
            __type_error__("received_message_callback", "Callable", received_message_callback)
        if receipt_message_callback is not None and not callable(receipt_message_callback):
            __type_error__("receipt_message_callback", "Optional[Callable]", receipt_message_callback)
        if sync_message_callback is not None and not callable(sync_message_callback):
            __type_error__("sync_message_callback", "Optional[Callable]", sync_message_callback)
        if typing_message_callback is not None and not callable(typing_message_callback):
            __type_error__("typing_message_callback", "Optional[Callable]", typing_message_callback)
        if story_message_callback is not None and not callable(story_message_callback):
            __type_error__("story_message_callback", "Optional[Callable]", story_message_callback)
        if payment_message_callback is not None and not callable(payment_message_callback):
            __type_error__("payment_message_callback", "Optional[Callable]", payment_message_callback)
        if reaction_message_callback is not None and not callable(reaction_message_callback):
            __type_error__("reaction_message_callback", "Optional[Callable]", reaction_message_callback)
        if call_message_callback is not None and not callable(call_message_callback):
            __type_error__("call_message_callback", "Optional[Callable]", call_message_callback)
        if not isinstance(do_expunge, bool):
            __type_error__("do_expunge", "bool", do_expunge)
        # Set internal variables:
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
        self._do_expunge: bool = do_expunge
        self._subscription_id: Optional[int] = None
        # Create and connect the socket.
        self._receive_socket: socket.socket = __socket_create__(server_address)
        __socket_connect__(self._receive_socket, server_address)
        return

    def run(self):
        """
        Thread override.
        """
        # Do send sync request if we're not the primary device.
        if self._account.device_id != 1:
            # Create sync request object and json command string:
            sync_request_command_obj = {
                "jsonrpc": "2.0",
                "id": 10,
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
            "id": 1,
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
            if self._account.messages.sending:
                if DEBUG:
                    info_message = "INFO: Sending a message, delaying processing until complete."
                    print(info_message, file=sys.stderr)
            while self._account.messages.sending:
                pass
            # Parse incoming message:
            message_obj: dict = json.loads(message_str)
            if 'method' in message_obj.keys() and message_obj['method'] == 'receive':
                envelope_dict: dict = message_obj['params']['envelope']
                #### Data Message #####
                if 'dataMessage' in envelope_dict.keys():
                    data_message: dict[str, object] = envelope_dict['dataMessage']
                    ############### REACTIONS ##########################
                    # Create reaction Message:
                    if 'reaction' in data_message.keys():
                        message = Reaction(
                            command_socket=self._command_socket, account_id=self._account.number,
                            config_path=self._config_path, contacts=self._account.contacts,
                            groups=self._account.groups, devices=self._account.devices,
                            this_device=self._account.device, raw_message=envelope_dict
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
                            if data_message['groupInfo']['type'] == 'UPDATE':
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
                                this_device=self._account.device, raw_message=envelope_dict
                            )
                            if DEBUG:
                                print("Parsing group update.", file=sys.stderr)
                            message.recipient.__sync__()
                            self._account.messages.append(message)
                            if self._sync_msg_cb is not None:
                                self._sync_msg_cb(self._account, message)
                        ########################### Received Message ###################
                        else:
                            # Create Received message:
                            message = ReceivedMessage(
                                command_socket=self._command_socket, account_id=self._account.number,
                                config_path=self._config_path, contacts=self._account.contacts,
                                groups=self._account.groups, devices=self._account.devices,
                                this_device=self._account.device, sticker_packs=self._sticker_packs,
                                raw_message=envelope_dict,
                            )
                            # Sender is no longer typing:
                            message.sender.is_typing = False
                            # Append the message and call the data message callback:
                            self._account.messages.append(message)
                            if self._recv_msg_cb is not None:
                                self._recv_msg_cb(self._account, message)
                #### Receipt Message ####
                elif 'receiptMessage' in envelope_dict.keys():
                    message = Receipt(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, raw_message=envelope_dict
                    )
                    # Parse receipt:
                    if DEBUG:
                        print("Parsing receipt...", file=sys.stderr)
                    self._account.messages.__parse_receipt__(message)
                    # Call receipt callback:
                    if self._rcpt_msg_cb is not None:
                        self._rcpt_msg_cb(self._account, message)
                #### Sync Message #####
                elif 'sync_message' in envelope_dict.keys():
                    if envelope_dict['sync_message'] == {}:
                        if DEBUG:
                            info_message = "INFO: Got empty sync message, skipping."
                            print(info_message, file=sys.stderr)
                            continue
                    if DEBUG:
                        print(envelope_dict)
                    message = SyncMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, sticker_packs=self._sticker_packs,
                        raw_message=envelope_dict
                    )
                    # Parse the sync message based on sync type:
                    if DEBUG:
                        print("Parsing sync message...", file=sys.stderr)
                    if (message.sync_type == SyncMessage.TYPE_READ_MESSAGE_SYNC or
                            message.sync_type == SyncMessage.TYPE_SENT_MESSAGE_SYNC):
                        if DEBUG:
                            print("Read messages.", file=sys.stderr)
                        self._account.messages.__parse_sync_message__(message)
                    elif message.sync_type == SyncMessage.TYPE_CONTACT_SYNC:
                        if DEBUG:
                            print("Contact sync", file=sys.stderr)
                        self._account.contacts.__sync__()
                    elif message.sync_type == SyncMessage.TYPE_GROUPS_SYNC:
                        if DEBUG:
                            print("Group sync", file=sys.stderr)
                        self._account.groups.__sync__()
                    elif message.sync_type == SyncMessage.TYPE_BLOCKED_SYNC:
                        if DEBUG:
                            print("Blocked sync", file=sys.stderr)
                        self._account.contacts.__parse_sync_message__(message)
                        self._account.groups.__parse_sync_message__(message)
                    elif message.sync_type == SyncMessage.TYPE_SENT_MESSAGE_SYNC:
                        if DEBUG:
                            print("Sent message sync", file=sys.stderr)
                        self._account.messages.__parse_sync_message__(message)
                    else:
                        print(envelope_dict, file=sys.stderr, flush=True)
                        print(message.sync_type, file=sys.stderr, flush=True)
                        raise RuntimeError("Unhandled sync type")
                    # Append the message to messages:
                    if message is None:
                        raise RuntimeError("Shouldn't be none")
                    self._account.messages.append(message)
                    # Call sync message callback:
                    if self._sync_msg_cb is not None:
                        self._sync_msg_cb(self._account, message)
                #### Typing Message ####
                elif 'typingMessage' in envelope_dict.keys():
                    message = TypingMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.devices.get_account_device(), raw_message=envelope_dict
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
                elif 'storyMessage' in envelope_dict.keys():
                    message = StoryMessage(
                        command_socket=self._command_socket, account_id=self._account.number,
                        config_path=self._config_path, contacts=self._account.contacts,
                        groups=self._account.groups, devices=self._account.devices,
                        this_device=self._account.device, raw_message=envelope_dict
                    )
                    # print("DEBUG: ", envelopeDict)
                    self._account.messages.append(message)
                    if self._stry_msg_cb is not None:
                        self._stry_msg_cb(self._account, message)
                #### Call message ####
                elif 'callMessage' in envelope_dict.keys():
                    print(envelope_dict)

                    message = CallMessage(command_socket=self._command_socket, account_id=self._account.number,
                                          config_path=self._config_path, contacts=self._account.contacts,
                                          groups=self._account.groups, devices=self._account.devices,
                                          this_device=self._account.device, raw_message=envelope_dict)
                    if self._call_msg_cb is not None:
                        self._call_msg_cb(self._account, message)
                #### Unrecognized message ####
                else:
                    if DEBUG:
                        errorMessage = "DEBUG: Unrecognized envelope, perhaps a payment message."
                        print(errorMessage, file=sys.stderr)
                        print("DEBUG: ", envelope_dict.keys(), file=sys.stderr)
                        print("DEBUG: ", envelope_dict, file=sys.stderr)
                        continue
                #### Call all messages callback:
                if self._all_msg_cb is not None:
                    self._all_msg_cb(self._account, message)
            else:
                info_message = "DEBUG: Incoming data that's not a message.\nDEBUG: DATA =\n%s" % message_str
                print(info_message, file=sys.stderr)
            #### Check for expired messages:
            self._account.messages.__check_expiries__()
            if self._do_expunge:
                self._account.messages.__do_expunge__()
        return

    def stop(self) -> None:
        """
        Stops the reception.
        :returns: None
        """
        self._subscription_id = None
        __socket_close__(self._receive_socket)
        return

