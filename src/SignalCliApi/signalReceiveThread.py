#!/usr/bin/env python3
"""
File: signalReceiveThread.py
Handle receiving messages from signal.
"""
import logging
from typing import Callable, Optional, Any
import socket
import threading
import json

from .signalAccount import Account
from .signalCallMessage import CallMessage
from .signalCommon import __socket_create__, __socket_connect__, __socket_close__, __socket_receive__, \
    __socket_send__, __type_error__, SyncTypes, CallbackIdx, __parse_signal_response__, __check_response_for_error__, \
    TypingStates
from .signalGroupUpdate import GroupUpdate
from .signalMessage import Message
from .signalReaction import Reaction
from .signalReceipt import Receipt
from .signalReceivedMessage import ReceivedMessage
from .signalSticker import StickerPacks
from .signalStoryMessage import StoryMessage
from .signalSyncMessage import SyncMessage
from .signalTypingMessage import TypingMessage
from .signalExceptions import CommunicationsError


def __type_check_callback__(callback: Optional[tuple[Callable, Optional[list[Any]]]]) -> bool:
    """
    Type check a call back.
    :param callback: The call back to type check.
    :return: bool: True or False on success or failure.
    """
    if callback is not None:
        if not isinstance(callback, tuple):
            return False
        elif len(callback) != 2:
            return False
        elif not callable(callback[CallbackIdx.CALLABLE]):
            return False
        elif callback[CallbackIdx.PARAMS] is not None and not isinstance(callback[CallbackIdx.PARAMS], list):
            return False
    return True


class ReceiveThread(threading.Thread):
    """
    The reception thread.
    """
    def __init__(self,
                 server_address: tuple[str, int] | str,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: StickerPacks,
                 account: Account,
                 all_messages_callback: Optional[tuple[Callable, Optional[list[Any, ...]]]] = None,
                 received_message_callback: Optional[tuple[Callable, Optional[list[Any, ...]]]] = None,
                 receipt_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 sync_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 typing_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 story_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 payment_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 reaction_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 call_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 do_expunge: bool = True,
                 ) -> None:
        """
        Create the reception thread.
        Callbacks must have the signature of:
            callback(account: Account, message: Message, *additional_params) where the first element passed is the
            Account object for the message received, and the second element is the message that was received.
        The return value of callback can be True, False, or None. If the all_messages_callback returns a boolean, it is
            returned, if the all_messages_callback returns None, then the return value of the specific callback is
            returned.  If True is returned, Reception is stopped. If False, or None are returned, reception continues.
            All other values are assumed to be False.
        :param server_address: tuple[str, int] | str: The server address to connect the reception socket to.
        :param command_socket: socket.socket: The socket to run commands through.
        :param config_path: str: The full path to the signal-cli config directory.
        :param sticker_packs: StickerPacks: The loaded StickerPacks object.
        :param account: Account: The account to receive for.
        :param all_messages_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for ALL messages.
        :param received_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for received
            messages.
        :param receipt_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback for message receipts.
        :param sync_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for sync messages.
        :param typing_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for typing change
            messages.
        :param story_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback for story messages.
        :param payment_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for payment messages.
        :param reaction_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for reaction
            messages.
        :param call_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback for call messages.
        :param do_expunge: bool: True we should automatically expunge expired messages.
        """
        # Run super init:
        super().__init__(None)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(server_address, tuple) and not isinstance(server_address, str):
            logger.critical("Raising TypeError:")
            __type_error__("server_address", "tuple | str", server_address)
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(sticker_packs, StickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(account, Account):
            logger.critical("Raising TypeError:")
            __type_error__("account", "Account", account)
        if not __type_check_callback__(all_messages_callback):
            logger.critical("Raising TypeError:")
            __type_error__("all_messages_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           all_messages_callback)
        if not __type_check_callback__(received_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("received_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           received_message_callback)
        if not __type_check_callback__(receipt_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("receipt_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           receipt_message_callback)
        if not __type_check_callback__(sync_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("sync_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           sync_message_callback)
        if not __type_check_callback__(typing_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("typing_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           typing_message_callback)
        if not __type_check_callback__(story_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("story_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           story_message_callback)
        if not __type_check_callback__(payment_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("payment_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           payment_message_callback)
        if not __type_check_callback__(reaction_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("reaction_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           reaction_message_callback)
        if not __type_check_callback__(call_message_callback):
            logger.critical("Raising TypeError:")
            __type_error__("call_message_callback", "Optional[tuple[Callable, Optional[list[Any]]]]",
                           call_message_callback)
        if not isinstance(do_expunge, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_expunge", "bool", do_expunge)

        # Set internal variables:
        self._command_socket: socket.socket = command_socket
        """The socket to run command operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account: Account = account
        """The account we're receiving for."""
        self._sticker_packs: StickerPacks = sticker_packs
        """The loaded sticker packs object."""
        self._all_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = all_messages_callback
        """Call back to call on receipt of ALL messages."""
        self._recv_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = received_message_callback
        """Call back to call on receipt of a ReceivedMessage."""
        self._rcpt_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = receipt_message_callback
        """Call back to call on receipt of a receipt message."""
        self._sync_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = sync_message_callback
        """Call back to call on receipt of a sync message."""
        self._type_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = typing_message_callback
        """Call back to call on receipt of a typing message."""
        self._stry_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = story_message_callback
        """Call back to call on receipt of a story message."""
        self._pymt_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = payment_message_callback
        """Call back to call on receipt of a payment message."""
        self._ract_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = reaction_message_callback
        """Call back to call on receipt of a reaction message."""
        self._call_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = call_message_callback
        """Call back to call on receipt of a call message."""
        self._do_expunge: bool = do_expunge
        """Should we expunge on update?"""

        # Set internal properties:
        self._subscription_id: Optional[int] = None
        """The subscription ID provided by Signal."""
        # Create and connect the socket.
        self._receive_socket: socket.socket = __socket_create__(server_address)
        __socket_connect__(self._receive_socket, server_address)
        return

    def __call_callback__(self,
                          callback: Optional[tuple[Callable, Optional[list[Any]]]],
                          account: Account,
                          message: Message,
                          ) -> Optional[bool]:
        """
        Execute a callback and return True for stopping reception, False for do not stop reception; The order of
        priority of return values is all messages callback, specified callback. So if all messages returns None, then
        the return value of the specified callback is returned.
        :param callback: Optional[tuple[Callable, Optional[list[Any]]]]: The callback to call, and any parameters to
            pass to it, if None the callback is not executed.
        :param account: Account: The account we're receiving for.
        :param message: Message: The message we've received.
        :return: Optional[bool]: If True is returned the callback stops the reception thread, If False or None are
            returned then reception continues.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__call_callback__.__name__)

        # Return if callback is None:
        cb_return_value: Optional[bool] = None
        # Call specified call back:
        try:
            logger.debug("Calling callback: '%s'" % callback[CallbackIdx.CALLABLE].__name__)
            if callback[CallbackIdx.PARAMS] is not None:
                cb_return_value = callback[CallbackIdx.CALLABLE](account, message, *callback[CallbackIdx.PARAMS])
            else:
                cb_return_value = callback[CallbackIdx.CALLABLE](account, message)
        except Exception as e:
            error_message: str = "Callback '%s', caused an Exception '%s', with arguments: '%s'" \
                                 % (callback[CallbackIdx.CALLABLE].__name__, str(type(e)), str(e.args))
            logger.critical(error_message)

        # Call all messages callback:
        all_return_value: Optional[bool] = None
        try:
            logger.debug("Calling callback: '%s'." % self._all_msg_cb[CallbackIdx.CALLABLE].__name__)
            if self._all_msg_cb[CallbackIdx.PARAMS] is not None:
                all_return_value = self._all_msg_cb[CallbackIdx.CALLABLE](account, message,
                                                                          *self._all_msg_cb[CallbackIdx.PARAMS])
            else:
                all_return_value = self._all_msg_cb[CallbackIdx.CALLABLE](account, message)
        except Exception as e:
            error_message: str = "Callback '%s', caused an Exception '%s', with arguments: '%s'" \
                                 % (callback[CallbackIdx.CALLABLE].__name__, str(type(e)), str(e.args))
            logger.critical(error_message)

        # Determine return value:
        if all_return_value is not None:
            return all_return_value
        return cb_return_value

    def __parse_data_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse a dataMessage incoming message.
        :param envelope_dict: dict[str, Any]: The dict provided by signal.
        :return: Optional[bool]: The return value of the callbacks.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_data_message__.__name__)

        # Fetch data message:
        data_message: dict[str, Any] = envelope_dict['dataMessage']

        #######################
        # REACTIONS:
        #######################
        if 'reaction' in data_message.keys():
            # Create reaction Message:
            message = Reaction(
                command_socket=self._command_socket, account_id=self._account.number,
                config_path=self._config_path, contacts=self._account.contacts,
                groups=self._account.groups, devices=self._account.devices,
                this_device=self._account.device, raw_message=envelope_dict
            )
            # Parse reaction and call the reaction callback:
            logger.debug("Got reaction message, parsing and calling reaction callback.")
            self._account.messages.__parse_reaction__(message)
            message.sender.seen(message.timestamp)
            return self.__call_callback__(self._ract_msg_cb, self._account, message)
        ######################
        # GROUP UPDATES:
        ######################
        else:
            # TODO: See if there is a better way to do this, this feels and reads pretty hacky.
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
                logger.debug("Got a group update message, syncing groups and calling sync callback.")
                message.recipient.__sync__()
                self._account.messages.append(message)
                message.sender.seen(message.timestamp)
                return self.__call_callback__(self._sync_msg_cb, self._account, message)
            ##################################
            # Received Message:
            ##################################
            else:
                # Create a Received message:
                message = ReceivedMessage(
                    command_socket=self._command_socket, account_id=self._account.number,
                    config_path=self._config_path, contacts=self._account.contacts,
                    groups=self._account.groups, devices=self._account.devices,
                    this_device=self._account.device, sticker_packs=self._sticker_packs,
                    raw_message=envelope_dict,
                )
                logger.debug("Got a received message, storing and calling received callback.")
                # Sender is no longer typing:
                if message.sender.is_typing:
                    # Create a typing stopped message:
                    stop_typing_message = TypingMessage(command_socket=self._command_socket,
                                                        account_id=self._account.get_id(), config_path=self._config_path,
                                                        contacts=self._account.contacts, groups=self._account.groups,
                                                        devices=self._account.devices, this_device=self._account.device,
                                                        sender=message.sender, recipient=message.recipient,
                                                        device=message.device, timestamp=message.timestamp,
                                                        action=TypingStates.STOPPED, time_changed=message.timestamp)
                    # Send the typing message to the sending for parsing:
                    message.sender.__parse_typing_message__(stop_typing_message)
                    # Store the typing message.
                    self._account.messages.append(stop_typing_message)
                # Store the received message:
                self._account.messages.append(message)
                # Mark the sender as seen:
                message.sender.seen(message.timestamp)
                return self.__call_callback__(self._recv_msg_cb, self._account, message)

    def __parse_receipt_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse a receipt message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The return value of the callbacks.
        """
        message = Receipt(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, raw_message=envelope_dict
        )
        # Parse receipt:
        self._account.messages.__parse_receipt__(message)
        # Call receipt callback:
        return self.__call_callback__(self._rcpt_msg_cb, self._account, message)

    def __parse_sync_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse a sync message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The return value of the callback.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__parse_sync_message__.__name__)

        # Check to see if this is an empty sync message:
        if envelope_dict['sync_message'] == {}:
            logger.warning("Got empty sync message, skipping.")
            return None
        # Create the SyncMessage object:
        message = SyncMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, sticker_packs=self._sticker_packs,
            raw_message=envelope_dict
        )
        if message.sync_type == SyncTypes.READ_MESSAGES or message.sync_type == SyncTypes.SENT_MESSAGES:
            self._account.messages.__parse_sync_message__(message)
        elif message.sync_type == SyncTypes.CONTACTS:
            self._account.contacts.__sync__()
        elif message.sync_type == SyncTypes.GROUPS:
            self._account.groups.__sync__()
        elif message.sync_type == SyncTypes.BLOCKS:
            self._account.contacts.__parse_sync_message__(message)
            self._account.groups.__parse_sync_message__(message)
        elif message.sync_type == SyncTypes.SENT_MESSAGES:
            self._account.messages.__parse_sync_message__(message)
        else:
            error_message: str = "Unhandled sync type: %s" % str(message.sync_type)
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)
        # Append the message to messages:
        self._account.messages.append(message)
        # Call sync message callback:
        return self.__call_callback__(self._sync_msg_cb, self._account, message)

    def __parse_typing_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse an incoming typing message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The return value of the callbacks.
        """
        message = TypingMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, raw_message=envelope_dict
        )
        # Parse typing message:
        message.sender.__parse_typing_message__(message)
        # Append the typing message and call the typing call back:
        self._account.messages.append(message)

        return self.__call_callback__(self._type_msg_cb, self._account, message)

    def __parse_story_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse an incoming story message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The return value of the callbacks.
        """
        message = StoryMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, raw_message=envelope_dict
        )
        self._account.messages.append(message)
        return self.__call_callback__(self._stry_msg_cb, self._account, message)

    def __parse_call_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse an incoming call message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The callbacks return value.
        """
        message = CallMessage(command_socket=self._command_socket, account_id=self._account.number,
                              config_path=self._config_path, contacts=self._account.contacts,
                              groups=self._account.groups, devices=self._account.devices,
                              this_device=self._account.device, raw_message=envelope_dict)
        return self.__call_callback__(self._call_msg_cb, self._account, message)

    def run(self) -> None:
        """
        Thread override.
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.run.__name__)

        # Do send sync request if we're not the primary device.
        if self._account.device_id != 1:
            # Create sync request object and json command string:
            sync_request_command_obj: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "sendSyncRequest",
                "params": {
                    "account": self._account.number,
                }
            }
            json_command_str: str = json.dumps(sync_request_command_obj) + '\n'

            # Communicate with Signal:
            __socket_send__(self._receive_socket, json_command_str)
            response_str = __socket_receive__(self._receive_socket)
            response_obj: dict[str, Any] = __parse_signal_response__(response_str)

            error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])
            if error_occurred:
                error_message: str = "signal error while sending sync request. Code %i, Message: %s" \
                                     % (signal_code, signal_message)
                logger.warning(error_message)

        # Create receive object and json command string:
        start_receive_command_object = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribeReceive",
            "params": {
                "account": self._account.number,
            }
        }
        json_command_str: str = json.dumps(start_receive_command_object) + '\n'

        # Communicate start receive with signal:
        __socket_send__(self._receive_socket, json_command_str)
        response_str = __socket_receive__(self._receive_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])
        if error_occurred:
            error_message: str = "Signal error while trying to start receiving. Code %i, Message: %s" \
                                 % (signal_code, signal_message)
            logger.critical("Raising RuntimeError(%s)." % error_message)
            raise RuntimeError(error_message)

        # Set subscription ID.
        self._subscription_id = response_obj['result']

        # START RECEIVE LOOP:
        while self._subscription_id is not None:
            # Blocks until a message received:
            try:
                response_str: str = __socket_receive__(self._receive_socket)
            except CommunicationsError as e:
                logger.critical("Failed to receive, got CommunicationsError(%s)." % str(e.args))
                break
            # Delay processing until messages are finished sending:
            if self._account.messages.sending:
                logger.debug("Message received while sending a message, delaying processing until complete.")
            while self._account.messages.sending:
                pass

            # Parse incoming message:
            message_obj: dict[str, Any] = __parse_signal_response__(response_str)
            if 'method' in message_obj.keys() and message_obj['method'] == 'receive':
                envelope_dict: dict = message_obj['params']['envelope']
                return_value: Optional[bool] = None
                ##########################
                # Data Message:
                ##########################
                if 'dataMessage' in envelope_dict.keys():
                    return_value = self.__parse_data_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                ##########################
                # Receipt Message:
                ##########################
                elif 'receiptMessage' in envelope_dict.keys():
                    return_value = self.__parse_receipt_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                #############################
                # Sync Message:
                #############################
                elif 'sync_message' in envelope_dict.keys():
                    return_value = self.__parse_sync_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                ###############################
                # Typing Message:
                ###############################
                elif 'typingMessage' in envelope_dict.keys():
                    return_value = self.__parse_typing_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                ###############################
                # Story Message:
                ###############################
                elif 'storyMessage' in envelope_dict.keys():
                    return_value = self.__parse_story_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                ##############################
                # Call message:
                ##############################
                elif 'callMessage' in envelope_dict.keys():
                    return_value = self.__parse_call_message__(envelope_dict)
                    if return_value is True:
                        break  # Stop receiving.
                ##############################
                # Unrecognized message:
                ##############################
                else:
                    logger.warning("Unrecognized incoming envelope. Perhaps a payment message.")
                    logger.debug("envelope_dict.keys() = %s" % str(envelope_dict.keys()))
                    logger.debug("envelope_dict = %s" % str(envelope_dict))
                    continue
            else:
                error_message: str = "Incoming data that's not a message. DATA = %s" % response_str
                logger.critical("Raising NotImplemented(%s)." % error_message)
                raise NotImplemented(error_message)
            ###############################
            # Check for expired messages:
            ###############################
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
