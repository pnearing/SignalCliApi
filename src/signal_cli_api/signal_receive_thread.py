#!/usr/bin/env python3
"""
File: signal_receive_thread.py
Handle receiving messages from signal.
"""
# pylint: disable=R0902, R0912, R0913, R0914, R0915, W0511
import logging
from typing import Callable, Optional, Any
import socket
import threading
import json

from .signal_account import SignalAccount
from .signal_call_message import SignalCallMessage
from .signal_common import (__socket_create__, __socket_connect__, __socket_close__,
                            __socket_receive_blocking__, __socket_send__, __type_error__,
                            SyncTypes, __parse_signal_response__, __check_response_for_error__,
                            TypingStates, __socket_receive_non_blocking__, RecipientTypes)
from . import run_callback
from .run_callback import __run_callback__, __type_check_callback__
from .signal_group_update import SignalGroupUpdate
from .signal_message import SignalMessage
from .signal_reaction import SignalReaction
from .signal_receipt import SignalReceipt
from .signal_received_message import SignalReceivedMessage
from .signal_sticker import SignalStickerPacks
from .signal_story_message import SignalStoryMessage
from .signal_sync_message import SignalSyncMessage
from .signal_typing_message import SignalTypingMessage
from .signal_exceptions import CommunicationsError


class SignalReceiveThread(threading.Thread):
    """
    The reception thread.
    """

    def __init__(self,
                 server_address: tuple[str, int] | str,
                 command_socket: socket.socket,
                 config_path: str,
                 sticker_packs: SignalStickerPacks,
                 account: SignalAccount,
                 all_messages_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 received_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 receipt_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 sync_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 typing_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 story_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 payment_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 reaction_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 call_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 suppress_callback_error: bool = False,
                 do_expunge: bool = True,
                 ) -> None:
        """
        Create the reception thread.
        Callbacks must have the signature of:
            callback(account: SignalAccount, message: SignalMessage, *additional_params) where the
            first element passed is the SignalAccount object for the message received, and the
            second element is the message that was received.
            The return value of callback can be True, False, or None. If the specific callback
            returns a boolean, it is returned; If the specific callback returns None, then the
            return value of the all messages callback is returned.  If True is returned,
            Reception is stopped. If anything else is returned, then reception continues.
        :param server_address: tuple[str, int] | str: The server address to connect the
            reception socket to.
        :param command_socket: socket.socket: The socket to run commands through.
        :param config_path: str: The full path to the signal-cli config directory.
        :param sticker_packs: SignalStickerPacks: The loaded SignalStickerPacks object.
        :param account: SignalAccount: The account to receive for.
        :param all_messages_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for
            ALL messages.
        :param received_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback
            for received messages.
        :param receipt_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback
            for message receipts.
        :param sync_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback for
            sync messages.
        :param typing_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback
            for typing change messages.
        :param story_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback for
            story messages.
        :param payment_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback
            for payment messages.
        :param reaction_message_callback: Optional[tuple[Callable, Optional[list[Any]]]]: Callback
            for reaction messages.
        :param call_message_callback:Optional[tuple[Callable, Optional[list[Any]]]]: Callback for
            call messages.
        :param suppress_callback_error: bool: Should we supress callback errors? Defaults to False.
        :param do_expunge: bool: True, we should automatically expunge expired messages.
        """
        # Run super init:
        super().__init__(None)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(server_address, tuple) and not isinstance(server_address, str):
            logger.critical("Raising TypeError:")
            __type_error__("server_address", "tuple[str, int] | str", server_address)
        if not isinstance(command_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("command_socket", "socket.socket", command_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(sticker_packs, SignalStickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "SignalStickerPacks", sticker_packs)
        if not isinstance(account, SignalAccount):
            logger.critical("Raising TypeError:")
            __type_error__("account", "SignalAccount", account)
        if not __type_check_callback__(all_messages_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("all_messages_callback", "Optional[tuple[Callable, "
                                                    "Optional[list[Any]]]]",
                           all_messages_callback)
        if not __type_check_callback__(received_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("received_message_callback", "Optional[tuple[Callable, "
                                                        "Optional[list[Any]]]]",
                           received_message_callback)
        if not __type_check_callback__(receipt_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("receipt_message_callback", "Optional[tuple[Callable, "
                                                       "Optional[list[Any]]]]",
                           receipt_message_callback)
        if not __type_check_callback__(sync_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("sync_message_callback", "Optional[tuple[Callable, "
                                                    "Optional[list[Any]]]]",
                           sync_message_callback)
        if not __type_check_callback__(typing_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("typing_message_callback", "Optional[tuple[Callable, "
                                                      "Optional[list[Any]]]]",
                           typing_message_callback)
        if not __type_check_callback__(story_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("story_message_callback", "Optional[tuple[Callable, "
                                                     "Optional[list[Any]]]]",
                           story_message_callback)
        if not __type_check_callback__(payment_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("payment_message_callback", "Optional[tuple[Callable, "
                                                       "Optional[list[Any]]]]",
                           payment_message_callback)
        if not __type_check_callback__(reaction_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("reaction_message_callback", "Optional[tuple[Callable, "
                                                        "Optional[list[Any]]]]",
                           reaction_message_callback)
        if not __type_check_callback__(call_message_callback)[0]:
            logger.critical("Raising TypeError:")
            __type_error__("call_message_callback", "Optional[tuple[Callable, "
                                                    "Optional[list[Any]]]]",
                           call_message_callback)
        if not isinstance(suppress_callback_error, bool):
            logger.critical("Raising TypeError:")
            __type_error__('suppress_callback_error', 'bool', suppress_callback_error)
        if not isinstance(do_expunge, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_expunge", "bool", do_expunge)

        # Set suppress callback error.
        run_callback.set_suppress_error(suppress_callback_error)

        # Set internal variables:
        self._command_socket: socket.socket = command_socket
        """The socket to run command operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account: SignalAccount = account
        """The account we're receiving for."""
        self._sticker_packs: SignalStickerPacks = sticker_packs
        """The loaded sticker packs object."""

        # Set callbacks:
        self._all_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = all_messages_callback
        """Call back to call on receipt of ALL messages."""
        self._recv_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = \
            received_message_callback
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
        self._ract_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = \
            reaction_message_callback
        """Call back to call on receipt of a reaction message."""
        self._call_msg_cb: Optional[tuple[Callable, Optional[list[Any]]]] = call_message_callback
        """Call back to call on receipt of a call message."""

        # Set other internal properties:
        self._do_expunge: bool = do_expunge
        """Should we expunge on update?"""
        self._receiving: bool = False
        """Are we receiving?"""
        self._subscription_id: Optional[int] = None
        """The subscription ID provided by Signal."""
        # Create and connect the socket.
        self._receive_socket: socket.socket = __socket_create__(server_address)
        __socket_connect__(self._receive_socket, server_address)

    def __call_callback__(self,
                          callback: Optional[tuple[Callable, Optional[list[Any]]]],
                          account: SignalAccount,
                          message: SignalMessage,
                          ) -> Optional[bool]:
        """
        Execute a callback and return True for stopping reception, False for do not stop reception;
        The order of priority of return values is all messages callback, specified callback. So if
        all messages returns None, then the return value of the specified callback is returned.
        :param callback: Optional[tuple[Callable, Optional[list[Any]]]]: The callback to call,
            and any parameters to pass to it, if None the callback is not executed.
        :param account: SignalAccount: The account we're receiving for.
        :param message: SignalMessage: The message we've received.
        :return: Optional[bool]: If True is returned, the callback stops the reception thread, If
            False or None are  returned, then reception continues.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__call_callback__.__name__)
        # Call specified call back:
        logger.debug("Calling specific callback for: %s", str(type(message)))
        cb_return_value: Optional[bool] = __run_callback__(callback, account, message)
        # Call all messages callback:
        logger.debug("Calling all message callback.")
        all_return_value: Optional[bool] = __run_callback__(self._all_msg_cb, account, message)
        # Determine return value:
        if cb_return_value is None:
            logger.debug("Returning all message callback return value.")
            return all_return_value
        logger.debug("Returning specific message callback return value.")
        return cb_return_value

    def __parse_data_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse a dataMessage incoming message.
        :param envelope_dict: dict[str, Any]: The dict provided by signal.
        :return: Optional[bool]: The return value of the callbacks.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__parse_data_message__.__name__)

        # Fetch data message:
        data_message: dict[str, Any] = envelope_dict['dataMessage']

        #######################
        # REACTIONS:
        #######################
        if 'reaction' in data_message.keys():
            # Create reaction Message:
            reaction = SignalReaction(
                command_socket=self._command_socket, account_id=self._account.number,
                config_path=self._config_path, contacts=self._account.contacts,
                groups=self._account.groups, devices=self._account.devices,
                this_device=self._account.device, raw_message=envelope_dict
            )
            # Parse reaction and call the reaction callback:
            logger.debug("Got reaction message, parsing and calling reaction callback.")
            self._account.messages.__parse_reaction__(reaction)
            reaction.sender.__seen__(reaction.timestamp)
            return self.__call_callback__(self._ract_msg_cb, self._account, reaction)
        ######################
        # GROUP UPDATES:
        ######################
        # TODO: See if there is a better way to do this, this feels and reads pretty hacky.
        is_group_update: bool
        try:
            is_group_update = data_message['groupInfo']['type'] == 'UPDATE'
        except KeyError:
            is_group_update = False
        if is_group_update:
            message = SignalGroupUpdate(
                command_socket=self._command_socket, account_id=self._account.number,
                config_path=self._config_path, contacts=self._account.contacts,
                groups=self._account.groups, devices=self._account.devices,
                this_device=self._account.device, raw_message=envelope_dict
            )
            logger.debug("Got a group update message, syncing groups and calling "
                         "sync callback.")
            message.recipient.__sync__()
            self._account.messages.append(message)
            message.sender.__seen__(message.timestamp)
            return self.__call_callback__(self._sync_msg_cb, self._account, message)
        ##################################
        # Received Message:
        ##################################
        # Create a Received message:
        message = SignalReceivedMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, sticker_packs=self._sticker_packs,
            raw_message=envelope_dict,
        )
        logger.debug("Got a received message, storing and calling received callback.")
        # Store the received message:
        self._account.messages.append(message)
        # Sender is no longer typing:
        if message.sender.is_typing:
            # Create a typing stopped message:
            stop_typing_message = SignalTypingMessage(command_socket=self._command_socket,
                                                      account_id=self._account.get_id(),
                                                      config_path=self._config_path,
                                                      contacts=self._account.contacts,
                                                      groups=self._account.groups,
                                                      devices=self._account.devices,
                                                      this_device=self._account.device,
                                                      sender=message.sender,
                                                      recipient=message.recipient,
                                                      device=message.device,
                                                      timestamp=message.timestamp,
                                                      action=TypingStates.STOPPED,
                                                      time_changed=message.timestamp)
            # Send the typing message to the sending for parsing:
            message.sender.__parse_typing_message__(stop_typing_message)
            # Store the typing message.
            self._account.messages.append(stop_typing_message)
        # Mark the sender as seen:
        message.sender.__seen__(message.timestamp)
        message.device.__seen__(message.timestamp)
        message.recipient.__seen__(message.timestamp)
        return self.__call_callback__(self._recv_msg_cb, self._account, message)

    def __parse_receipt_message__(self, envelope_dict: dict[str, Any]) -> Optional[bool]:
        """
        Parse a receipt message.
        :param envelope_dict: dict[str, Any]: The incoming message.
        :return: Optional[bool]: The return value of the callbacks.
        """
        message = SignalReceipt(
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
        logger: logging.Logger = logging.getLogger(__name__ + '.'
                                                   + self.__parse_sync_message__.__name__)

        # Check to see if this is an empty sync message:
        if envelope_dict['syncMessage'] == {}:
            logger.warning("Got empty sync message, skipping.")
            return None
        # Create the SignalSyncMessage object:
        message = SignalSyncMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, sticker_packs=self._sticker_packs,
            raw_message=envelope_dict
        )
        if message.sync_type in (SyncTypes.READ_MESSAGES, SyncTypes.SENT_MESSAGES,
                                 SyncTypes.SENT_REACTION):
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
            error_message: str = f"Unhandled sync type: {message.sync_type}"
            logger.critical("Raising RuntimeError(%s).", error_message)
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
        message = SignalTypingMessage(
            command_socket=self._command_socket, account_id=self._account.number,
            config_path=self._config_path, contacts=self._account.contacts,
            groups=self._account.groups, devices=self._account.devices,
            this_device=self._account.device, raw_message=envelope_dict
        )
        # Parse typing message:
        if message.recipient.recipient_type == RecipientTypes.GROUP:
            message.recipient.__parse_typing_message__(message)
        else:
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
        message = SignalStoryMessage(
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
        message = SignalCallMessage(command_socket=self._command_socket,
                                    account_id=self._account.number, config_path=self._config_path,
                                    contacts=self._account.contacts, groups=self._account.groups,
                                    devices=self._account.devices, this_device=self._account.device,
                                    raw_message=envelope_dict)
        return self.__call_callback__(self._call_msg_cb, self._account, message)

    #############################
    # Run:
    #############################
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
            response_str = __socket_receive_blocking__(self._receive_socket)
            response_obj: dict[str, Any] = __parse_signal_response__(response_str)
            # There are no non fatal errors during reception:
            __check_response_for_error__(response_obj, [])

        # Create receive object and json command string:
        start_receive_command_object: dict[str, Any] = {
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
        response_str = __socket_receive_blocking__(self._receive_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj, [])
        if error_occurred:
            error_message: str = (f"Signal error while trying to start receiving. "
                                  f"Code {signal_code}, Message: {signal_message}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)

        # Set subscription ID, and start receiving:
        self._subscription_id = response_obj['result']
        self._receiving = True
        # START RECEIVE LOOP:
        while self._receiving:
            try:
                response_str: Optional[str] = __socket_receive_non_blocking__(self._receive_socket,
                                                                              0.01)
            except CommunicationsError as e:
                if self._receiving is False:
                    break
                raise e
            if response_str is None:
                continue
            # Delay processing until messages are finished sending:
            if self._account.messages.sending:
                logger.debug("Message received while sending a message, delaying processing "
                             "until complete.")
            while self._account.messages.sending:
                pass

            # Create msg object, and check the incoming message for an error,
            # NOTE: There are no non-fatal errors during reception:
            message_obj: dict[str, Any] = __parse_signal_response__(response_str)
            __check_response_for_error__(response_obj, [])

            # Make sure there is a method in the response:
            if 'method' not in message_obj.keys():
                logger.warning("Message received with no method.")
                logger.debug("message_obj = %s", str(message_obj))
                continue

            # Make sure that method is 'receive':
            if message_obj['method'] != 'receive':
                logger.warning("Message received with method other than 'receive': method = %s",
                               message_obj['method'])
                logger.debug('message_obj = %s', str(message_obj))
                continue

            # Make sure there are 'params' in the response:
            if 'params' not in message_obj.keys():
                logger.warning("Message has no 'params'.")
                logger.debug("message_obj = %s", str(message_obj))
                continue

            # Make sure there are 'result' in the 'params':
            if 'result' not in message_obj['params'].keys():
                logger.warning("Message doesn't have a result.")
                logger.debug("message_obj = %s", str(message_obj))
                continue

            # Make sure there is an 'envelope' in the message 'result':
            if 'envelope' not in message_obj['params']['result'].keys():
                logger.warning("Message with no envelope received.")
                logger.debug("message_obj = %s", str(message_obj))
                continue

            # Grab the envelope dict and type return_value:
            envelope_dict: dict = message_obj['params']['result']['envelope']
            return_value: Optional[bool]
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
            elif 'syncMessage' in envelope_dict.keys():
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
                logger.debug("envelope_dict.keys() = %s", str(envelope_dict.keys()))
                logger.debug("envelope_dict = %s", str(envelope_dict))
                continue

            ###############################
            # Check for expired messages:
            ###############################
            # self._account.messages.__check_expiries__()
            if self._do_expunge:
                self._account.messages.do_expunge()
        # #####################################
        # # Reception halted:
        # #####################################
        # stop_receive_command_object: dict[str, Any] = {
        #     "jsonrpc": '2.0',
        #     "id": 2,
        #     "method": "unsubscribeReceive",
        #     "params": {
        #         "subscription": self._subscription_id,
        #     }
        # }
        #
        # json_command_str: str = json.dumps(stop_receive_command_object) + '\n'
        # __socket_send__(self._receive_socket, json_command_str)
        # response_str: str = __socket_receive_blocking__(self._receive_socket)
        # response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        # __check_response_for_error__(response_obj, [])
        #
        # self._subscription_id = None
        # __socket_close__(self._receive_socket)
        # return

    def stop(self) -> None:
        """
        Stops the reception.
        :returns: None
        """
        self._receiving = False
        __socket_close__(self._receive_socket)

    @property
    def subscription_id(self) -> Optional[int]:
        """
        The subscription ID.
        :returns: int
        """
        return self._subscription_id
