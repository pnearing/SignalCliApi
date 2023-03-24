#!/usr/bin/env python3

import json
import os
import re
import socket
from subprocess import Popen, PIPE, CalledProcessError, check_output, check_call
from time import sleep
from typing import Optional, Callable, Tuple, List

from signalAccount import Account
from .signalAccount import Account
from .signalAccounts import Accounts
from .signalCommon import __type_error__, find_signal, find_qrencode, parse_signal_return_code, __socket_create__, \
    __socket_connect__, __socket_close__, __socket_receive__, __socket_send__, phone_number_regex
from .signalReceiveThread import ReceiveThread
from .signalSticker import StickerPacks

DEBUG: bool = True


class SignalCli(object):
    def __init__(self,
                 signal_config_path: Optional[str] = None,
                 signal_exec_path: Optional[str] = None,
                 server_address: Optional[list[str, int] | tuple[str, int] | str] = None,
                 log_file_path: Optional[str] = None,
                 start_signal: bool = True,
                 ) -> None:
        # Argument checks:
        # Check signal config path:
        if signal_config_path is not None:
            if not isinstance(signal_config_path, str):
                __type_error__("signal_config_path", "str", signal_config_path)
            elif not os.path.exists(signal_config_path) and not start_signal:
                error_message = "FATAL: signal_config_path '%s' doesn't exist." % signal_config_path
                raise FileNotFoundError(error_message)
        # Check signal exec path:
        if signal_exec_path is not None:
            if not isinstance(signal_exec_path, str):
                __type_error__("signal_exec_path", "str", signal_exec_path)
            elif not os.path.exists(signal_exec_path) and start_signal:
                error_message = "FATAL: signal_exec_path '%s' does not exist." % signal_exec_path
                raise FileNotFoundError(error_message)
        # Check server address:
        if server_address is not None:
            if isinstance(server_address, list) or isinstance(server_address, tuple):
                if not isinstance(server_address[0], str):
                    __type_error__("server_address[0]", "str", server_address[0])
                elif not isinstance(server_address[1], int):
                    __type_error__("server_address[1]", "int", server_address[1])
            elif isinstance(server_address, str):
                if os.path.exists(server_address) and start_signal:
                    error_message = "socket path '%s' already exists. Perhaps signal is already running." % server_address
                    raise FileExistsError(error_message)
        # Check log file path:
        if log_file_path is not None:
            if not isinstance(log_file_path, str):
                __type_error__("log_file_path", "str", log_file_path)
        # Check start signal:
        if not isinstance(start_signal, bool):
            __type_error__("start_signal", "bool", start_signal)

        # Set internal vars:
        # Set config path:
        self.configPath: str
        if signal_config_path is not None:
            self.config_path = signal_config_path
        else:
            home_path = os.environ.get('HOME')
            self.config_path = os.path.join(home_path, '.local', 'share', 'signal-cli')
        # Set signal exec path:
        self._signalExecPath: Optional[str]
        if signal_exec_path is not None:
            self._signal_exec_path = signal_exec_path
        elif start_signal:
            self._signal_exec_path = find_signal()
        else:
            self._signal_exec_path = None
        # Set server address:
        self._serverAddress: tuple[str, int] | str
        if server_address is not None:
            self._server_address = server_address
        else:
            self._server_address = os.path.join(self.config_path, 'socket')
        # Check to see if we're starting signal, if the socket exists, throw an error.
        if isinstance(self._server_address, str) and start_signal:
            if os.path.exists(self._server_address):
                error_message = "socket path '%s' already exists. Perhaps signal is already running." % self._server_address
                raise FileExistsError(error_message)

        # set var to hold main signal process
        self._process: Optional[Popen] = None
        # Set sync socket:
        self._sync_socket: socket.socket = None
        # Set command socket:
        self._command_socket: socket.socket = None
        # Set var to hold link process:
        self._link_process: Optional[Popen] = None
        # Set qrencode exec path:
        self._qrencode_exec_path: Optional[str] = find_qrencode()
        # Set external properties and objects:
        # Set accounts:
        self.accounts: Accounts = None
        # Set sticker packs:
        self.sticker_packs: StickerPacks = None

        # Start signal-cli if requested:
        if start_signal:
            # Build signal-cli command line:
            signal_command_line = [self._signal_exec_path]
            if log_file_path is not None:
                signal_command_line.extend(['--verbose', '--log-file', log_file_path])
            signal_command_line.extend(['--config', self.config_path, 'daemon'])
            if isinstance(self._server_address, str):
                signal_command_line.extend(['--socket', self._server_address])
            else:
                address = "%s:%i" % (self._server_address[0], self._server_address[1])
                signal_command_line.extend(['--tcp', address])
            signal_command_line.extend(['--no-receive-stdout', '--receive-mode', 'manual'])
            # Run signal-cli in daemon mode:
            try:
                if DEBUG:
                    self._process = Popen(signal_command_line, text=True, stdout=PIPE)
                else:
                    self._process = Popen(signal_command_line, text=True, stdout=PIPE, stderr=PIPE)
            except CalledProcessError as e:
                parse_signal_return_code(e.returncode, signal_command_line, e.output)
        # Give signal 5 seconds to start
        sleep(5)
        # Wait for socket to appear:
        if isinstance(self._server_address, str):
            if start_signal:
                while not os.path.exists(self._server_address):
                    if DEBUG:
                        print("Waiting for socket to appear at: %s" % self._server_address)
                        sleep(0.5)
                sleep(1)
            else:
                if not os.path.exists(self._server_address):
                    error_message = "Failed to to locate socket at '%s'" % self._server_address
                    raise RuntimeError(error_message)
        # Create sockets and connect to them:
        self._sync_socket = __socket_create__(self._server_address)
        __socket_connect__(self._sync_socket, self._server_address)
        self._command_socket = __socket_create__(self._server_address)
        __socket_connect__(self._command_socket, self._server_address)
        # Load stickers:
        self.sticker_packs = StickerPacks(configPath=self.config_path)
        # Load accounts:
        self.accounts = Accounts(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                 config_path=self.config_path, sticker_packs=self.sticker_packs, do_load=True)
        # Create dict to hold processes:
        self._receive_threads: dict[str, ReceiveThread] = {}
        return

    #################################
    # Overrides:
    #################################
    def __del__(self):
        try:
            if self._process is not None:
                if isinstance(self._server_address, str):
                    os.remove(self._server_address)
        except Exception:
            pass
        return

    #################################
    # Methods:
    #################################
    def stop_signal(self):
        try:
            __socket_close__(self._sync_socket)
            __socket_close__(self._command_socket)
        except:
            pass
        try:
            self._process.terminate()
            self._link_process.terminate()
        except Exception:
            pass
        try:
            if isinstance(self._server_address, str):
                os.remove(self._server_address)
        except Exception:
            pass
        return

    def register_account(self, number: str, captcha: str, voice: bool = False) -> tuple[bool, Account | str]:
        # Check arguments:
        number_match = phone_number_regex.match(number)
        if number_match is None:
            return False, "number must be in format +nnnnnnnn...."
        if captcha[:16] == 'signalcaptcha://':
            captcha = captcha[16:]
        if captcha[:17] != 'signal-recaptcha-' and captcha[:15] != 'signal-hcaptcha':
            return False, "invalid captcha"
        # Check if account exists, and isn't registered.
        account = self.accounts.get_by_number(number)
        if account is not None:
            if account.registered:
                return False, "Account already registered."
        # Create register account command object and json command string:
        register_account_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 0,
            "method": "register",
            "params": {
                "account": number,
                "captcha": captcha,
                "voice": voice,
            }
        }
        json_command_str = json.dumps(register_account_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "ERROR: signal error, code: %i, message: %s" % (
                response_obj['error']['code'], response_obj['error']['message'])
            # Delete local account data, since signal-cli creates data for the account.
            delete_local_data_command_obj = {
                "jsonrpc": "2.0",
                "contact_id": 1,
                "method": "deleteLocalAccountData",
                "params": {
                    "account": number
                }
            }
            json_command_str = json.dumps(delete_local_data_command_obj) + '\n'
            # Communicate with signal:
            __socket_send__(self._sync_socket, json_command_str)
            response_str = __socket_receive__(self._sync_socket)
            # print(responseStr)
            return False, error_message
        # No error found, get the new account:
        new_account = self.accounts.__sync__()
        if new_account is None:
            new_account = self.accounts.get_by_number(number)
        return True, new_account

    def start_link_account(self, name: Optional[str] = None) -> tuple[str, str, str]:
        # Check for running process:
        if self._link_process is not None:
            raise RuntimeError("link already in process.")
        # create signal link command line:
        link_command_line = [self._signal_exec_path, '--config', self.config_path, 'link']
        if name is not None:
            link_command_line.extend(('--name', name))
        # Run signal link process:
        try:
            self._link_process = Popen(link_command_line, text=True, stdout=PIPE, stderr=PIPE)
        except CalledProcessError as e:
            parse_signal_return_code(e.returncode, link_command_line, e.output)
            # :NO RETURN :
        # Gather link from stdout
        signal_link = self._link_process.stdout.readline()
        signal_link = signal_link.rstrip()
        # Generate text qrcode:
        try:
            text_qr_code = check_output([self._qrencode_exec_path, '-o', '-', '--type=UTF8', signal_link]).decode('UTF8')
        except CalledProcessError:
            text_qr_code = ''
        # Generate png qrcode:
        png_qr_code_file_name = "link-qrcode.png"
        png_qr_code_path: str = os.path.join(self.config_path, png_qr_code_file_name)
        try:
            check_call([self._qrencode_exec_path, '-o', png_qr_code_path, signal_link])
        except CalledProcessError:
            png_qr_code_path = ''
        return signal_link, text_qr_code, png_qr_code_path

    def finsh_link(self) -> tuple[bool, Account | None | list[Account]]:
        # Check for process:
        if self._link_process is None:
            error_message = "link not started"
            return False, error_message
        # Wait for process:
        return_code = self._link_process.wait()
        # Parse return_code:
        if return_code == 0:
            new_account = self.accounts.__sync__()
            response_line = self._link_process.stdout.readline()
            print(response_line)
            if new_account is None:
                regex = r'^Associated with: (?P<number>.*)$'
                match = re.match(regex, response_line)
                new_account = self.accounts.get_by_number(match['number'])
            return True, new_account
        elif return_code == 1:
            response_string = self._link_process.stderr.read()
            regex = r'The user (?P<number>\+\d+) already exists'
            match = re.match(regex, response_string)
            if match is not None:
                error_message = "Account '%s' already exists." % match["number"]
                return False, error_message
        elif return_code == 3:
            response_string = self._link_process.stderr.read()
            regex = r'Link request error: Connection closed!'
            match = re.match(regex, response_string)
            if match is not None:
                error_message = "Link request timeout."
                return False, error_message
        response_string = self._link_process.stderr.read()
        return False, response_string

    def start_receive(self,
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
                      ) -> None:
        thread_id = account.number
        thread = ReceiveThread(serverAddress=self._server_address,
                               commandSocket=self._command_socket,
                               configPath=self.config_path,
                               account=account,
                               stickerPacks=self.sticker_packs,
                               allMessagesCallback=all_messages_callback,
                               receivedMessageCallback=received_message_callback,
                               receiptMessageCallback=receipt_message_callback,
                               syncMessageCallback=sync_message_callback,
                               typingMessageCallback=typing_message_callback,
                               storyMessageCallback=story_message_callback,
                               paymentMessageCallback=payment_message_callback,
                               reactionMessageCallback=reaction_message_callback,
                               callMessageCallback=call_message_callback,
                               )
        thread.start()
        self._recieve_threads[thread_id] = thread
        return

    def stopReceive(self, account: Account):
        threadId = account.number
        thread = self._recieveThreads[threadId]
        self._recieveThreads[threadId] = None
        thread.stop()
        return
