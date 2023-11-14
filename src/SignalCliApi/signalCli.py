#!/usr/bin/env python3
import logging
import json
import os
import re
import socket
from warnings import warn
from subprocess import Popen, PIPE, CalledProcessError, check_output, check_call
from time import sleep
from typing import Optional, Callable, Any

from .signalAccount import Account
from .signalAccounts import Accounts
from .signalCommon import __type_error__, find_signal, find_qrencode, parse_signal_return_code, __socket_create__, \
    __socket_connect__, __socket_close__, __socket_receive__, __socket_send__, phone_number_regex, CB_CALLABLE, \
    CB_PARAMS, __type_err_msg__
from .signalReceiveThread import ReceiveThread
from .signalSticker import StickerPacks

DEBUG: bool = False


class SignalCli(object):
    """Signal cli object."""

    def __init__(self,
                 signal_config_path: Optional[str] = None,
                 signal_exec_path: Optional[str] = None,
                 server_address: Optional[list[str, int] | tuple[str, int] | str] = None,
                 log_file_path: Optional[str] = None,
                 start_signal: bool = True,
                 callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 debug: bool = False
                 ) -> None:
        """
        Initialize signal-cli, starting the process if required.
        :param signal_config_path: Optional[str]: The path to the directory signal-cli should use.
        :param signal_exec_path: Optional[str]: The path to the signal-cli executable.
        :param server_address: Optional[list[str , int] | tuple[str, int] | str]: If signal-cli is already started,
            the address of the server, if a unix socket, use a str, otherwise use a tuple/list[hostname:str,port:int]
        :param log_file_path: Optional[str]: The path to the signal log file, if None, no logging is preformed.
        :param start_signal: Bool: True = start a signal-cli process, False = signal-cli is already running.
        :param callback: Optional[tuple[Callable, Optional[list[Any]]]]: The call back as a tuple, the first element
            being the callable, and the second element; If not None, is a list of any parameters to provide to the
            callback.  The callback signature is: (status: str, *params)
        :param debug: Bool: Produce debug output on stdout.
        :raises TypeError: If a parameter is of invalid type.
        :raises FileNotFoundError: If a file / directory doesn't exist when it should.
        :raises FileExistsError: If a socket file exists when it shouldn't.
        :raises RuntimeError: If an error occurs while loading signal data, more information in the error message.
        """
        # Setup logging.
        self.logger: logging.Logger = logging.getLogger(self.__name__)
        self.logger.info("Initialize.")
        # Argument checks:
        # Check signal config path:
        if signal_config_path is not None:
            self.logger.debug("Verify signal config path: %s" % signal_config_path)
            if not isinstance(signal_config_path, str):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('signal_config_path', 'str', signal_config_path))
                __type_error__("signal_config_path", "str", signal_config_path)
            elif not os.path.exists(signal_config_path) and not start_signal:
                error_message = "FATAL: signal_config_path '%s' doesn't exist." % signal_config_path
                self.logger.critical("FileNotFoundError: %s" % error_message)
                raise FileNotFoundError(error_message)

        # Check signal exec path:
        if signal_exec_path is not None:
            self.logger.debug("Verify signal_exec_path: %s" % signal_exec_path)
            if not isinstance(signal_exec_path, str):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('signal_exec_path', 'str', signal_config_path))
                __type_error__("signal_exec_path", "str", signal_exec_path)
            elif not os.path.exists(signal_exec_path) and start_signal:
                error_message = "FATAL: signal_exec_path '%s' does not exist." % signal_exec_path
                self.logger.critical("FileNotFoundError: %s" % error_message)
                raise FileNotFoundError(error_message)

        # Check the server address:
        if server_address is not None:
            self.logger.debug("Verify server_address.")
            if isinstance(server_address, list) or isinstance(server_address, tuple):
                self.logger.debug("server_address is a list | tuple, verifying elements.")
                if not isinstance(server_address[0], str):
                    self.logger.critical("TypeError:")
                    self.logger.critical(__type_err_msg__('server_address[0]', 'str', server_address[0]))
                    __type_error__("server_address[0]", "str", server_address[0])
                elif not isinstance(server_address[1], int):
                    self.logger.critical("TypeError:")
                    self.logger.critical(__type_err_msg__('server_address[1]', 'str', server_address[1]))
                    __type_error__("server_address[1]", "int", server_address[1])
            elif isinstance(server_address, str):
                self.logger.debug('server_address is a str.')
                if os.path.exists(server_address) and start_signal:
                    error_message = "socket path '%s' already exists. Perhaps signal is already running." \
                                    % server_address
                    self.logger.critical("FileExistsError: %s" % error_message)
                    raise FileExistsError(error_message)
            else:
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('server_address',
                                                      'list[str, int] | tuple[str, int] | str', server_address))
                __type_error__('server_address', 'list[str, int] | tuple[str, int] | str', server_address)

        # Check the log file path:
        if log_file_path is not None:
            self.logger.debug("Checking log_file_path.")
            if not isinstance(log_file_path, str):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('log_file_path', 'str', log_file_path))
                __type_error__("log_file_path", "str", log_file_path)

        # Check start signal:
        self.logger.debug("Verify start_signal.")
        if not isinstance(start_signal, bool):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('start_signal', 'bool', start_signal))
            __type_error__("start_signal", "bool", start_signal)

        # Check callback:
        if callback is not None:
            self.logger.debug("Verify callback.")
            if not isinstance(callback, tuple):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('callback',
                                                      'Optional[tuple[Callable, Optional[list[Any]]]]', callback))
                __type_error__('callback', 'Optional[tuple[Callable, Optional[list[Any]]]]', callback)
            elif len(callback) != 2:
                error_message: str = "callback must be 2 elements long."
                self.logger.critical("ValueError: %s" % error_message)
                raise ValueError(error_message)
            elif not callable(callback[CB_CALLABLE]):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('callback[0]', 'Callable', callback[CB_CALLABLE]))
                __type_error__('callback[0]', 'Callable', callback[CB_CALLABLE])
            elif callback[CB_PARAMS] is not None and not isinstance(callback[CB_PARAMS], list):
                self.logger.critical("TypeError:")
                self.logger.critical(__type_err_msg__('callback[1]', "Optional[list[Any]]", callback[CB_PARAMS]))
                __type_error__('callback[1]', 'Optional[list[Any]]', callback[CB_PARAMS])

        # Chck debug:
        self.logger.debug("Verify debug.")
        if not isinstance(debug, bool):
            self.logger.critical("TypeError:")
            self.logger.critical(__type_err_msg__('debug', 'bool', debug))
            __type_error__('debug', 'bool', debug)

        # Set DEBUG:
        global DEBUG
        DEBUG = debug

        # Set internal vars:
        # Set the config path:
        self.configPath: str
        if signal_config_path is not None:
            self.config_path = signal_config_path
        else:
            home_path = os.environ.get('HOME')
            self.config_path = os.path.join(home_path, '.local', 'share', 'signal-cli')
        self.logger.debug('signal-cli config path: %s' % self.config_path)

        # Set signal exec path:
        self._signalExecPath: Optional[str]
        if signal_exec_path is not None:
            self.logger.debug("Setting signal_exec_path to passed parameter.")
            self._signal_exec_path = signal_exec_path
        elif start_signal:
            self.logger.debug("Finding signal_exec_path.")
            self._signal_exec_path = find_signal()  # Raises FileNotFoundError if signal-cli not found.
        else:
            self.logger.debug("Setting signal_exec_path to None.")
            self._signal_exec_path = None
        self.logger.debug('signal-cli exec path: %s' % self._signal_exec_path)

        # Set server address:
        self._serverAddress: tuple[str, int] | str
        if server_address is not None:
            self.logger.debug("Setting server_address from parameter.")
            self._server_address = server_address
        else:
            self.logger.debug("Building server_address.")
            self._server_address = os.path.join(self.config_path, 'socket')
        self.logger.debug("Server address: %s" % str(self._server_address))

        # Check to see if we're starting signal, if the socket exists, throw an error.
        if isinstance(self._server_address, str) and start_signal:
            self.logger.debug("We're starting signal, and server_address is a file, verify it doesn't already exist.")
            if os.path.exists(self._server_address):
                error_message = "socket path '%s' already exists. Perhaps signal is already running." \
                                % self._server_address
                self.logger.critical("FileExistsError: %s" % error_message)
                raise FileExistsError(error_message)

        # Store callback:
        self._callback: Optional[tuple[Callable, Optional[list[Any]]]] = callback
        # set var to hold the main signal process
        self._signal_process: Optional[Popen] = None
        # Set sync socket:
        self._sync_socket: Optional[socket.socket] = None
        # Set command socket:
        self._command_socket: Optional[socket.socket] = None
        # Set var to hold the link process:
        self._link_process: Optional[Popen] = None
        # Set qrencode exec path:
        self._qrencode_exec_path: Optional[str] = find_qrencode()
        # Set external properties and objects:
        # Set accounts:
        self.accounts: Optional[Accounts] = None
        # Set sticker packs:
        self.sticker_packs: Optional[StickerPacks] = None

        # Start signal-cli if requested:
        if start_signal:
            self.logger.info("Starting signal-cli.")
            self._run_callback('starting signal-cli')
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
            self.logger.debug("Signal command line: %s" % str(signal_command_line))

            # Run signal-cli in daemon mode:
            self._signal_process: Popen
            try:
                if DEBUG:
                    self._signal_process = Popen(signal_command_line, text=True, stdout=PIPE)
                else:
                    self._signal_process = Popen(signal_command_line, text=True, stdout=PIPE, stderr=PIPE)
            except CalledProcessError as e:
                self.logger.critical("Failed to start signal-cli.")
                parse_signal_return_code(e.returncode, signal_command_line, e.output)
            self.logger.info("signal-cli started.")
        self._run_callback("signal-cli started.")

        # Give signal 5 seconds to start
        self._run_callback("Waiting for signal-cli to initialize.")
        sleep(5)
        self._run_callback('signal-cli initialized.')

        # Wait for the socket to appear:
        if isinstance(self._server_address, str):
            if start_signal:
                self.logger.debug("server_address is a socket, and we're starting signal, wait for socket to appear.")
                while not os.path.exists(self._server_address):
                    self._run_callback('waiting for socket')
                    if DEBUG:
                        print("Waiting for socket to appear at: %s" % self._server_address)
                        sleep(0.5)
                sleep(1)
                self.logger.debug("socket found.")
                self._run_callback('socket found')
            else:
                self.logger.debug("server address is a socket, and we're not starting signal, check for the socket.")
                if not os.path.exists(self._server_address):
                    self._run_callback('FATAL: socket not found')
                    error_message = "Failed to to locate socket at '%s'" % self._server_address
                    self.logger.critical("FileNotFoundError: %s" % error_message)
                    raise FileNotFoundError(error_message)

        # Create sockets and connect to them:
        self.logger.info("Connecting to sockets.")
        self._run_callback('connecting to sockets')
        self._sync_socket = __socket_create__(self._server_address)
        __socket_connect__(self._sync_socket, self._server_address)
        self._command_socket = __socket_create__(self._server_address)
        __socket_connect__(self._command_socket, self._server_address)
        self.logger.info("Connected to socket.")
        self._run_callback('connected to sockets')
        # Load stickers:
        self.logger.info("Loading sticker packs.")
        self.sticker_packs = StickerPacks(config_path=self.config_path)
        # Load accounts:
        self.logger.info("Loading accounts.")
        self.accounts = Accounts(sync_socket=self._sync_socket, command_socket=self._command_socket,
                                 config_path=self.config_path, sticker_packs=self.sticker_packs, do_load=True)
        # Create dict to hold processes:
        self._receive_threads: dict[str, Optional[ReceiveThread]] = {}
        self.logger.info("Initialization complete.")
        return

    #################################
    # Internal methods:
    #################################
    def _run_callback(self, status: str) -> None:
        self.logger.debug("Running callback with status: '%s'." % status)
        try:
            if self._callback is not None and self._callback[CB_PARAMS] is not None:
                self._callback[CB_CALLABLE](status, *self._callback[CB_PARAMS])
            elif self._callback is not None and self._callback[CB_PARAMS] is None:
                self._callback[CB_CALLABLE](status)
        except TypeError as e:
            self.logger.warning("TypeError while running callback: '%s': '%s'."
                                % (self._callback[0].__name__, str(e.args)))
            warn("Callback is not callable.", RuntimeWarning)
        except Exception as e:
            self.logger.warning("'%s' Exception while running callback: '%s': '%s'"
                                % (str(type(e)), self._callback[1].__name__, str(e.args)))
            warn("Callback raised an exception: %s" % str(type(e)), RuntimeWarning)
        return

    #################################
    # Overrides:
    #################################
    def __del__(self):
        try:
            if self._signal_process is not None:
                if isinstance(self._server_address, str):
                    os.remove(self._server_address)
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        return

    #################################
    # Methods:
    #################################
    def stop_signal(self) -> None:
        """
        Stop the signal-cli process.
        :returns: None
        """
        # Close the sockets:
        self.logger.info("Closing sockets.")
        __socket_close__(self._sync_socket)
        __socket_close__(self._command_socket)
        self.logger.info("Sockets closed.")
        # Terminate processes:
        if self._signal_process is not None:
            self.logger.info("Stopping signal-cli.")
            self._signal_process.terminate()  # Kill the process (Sends SigTerm)
            _, err = self._signal_process.communicate()  # Flush the pipes.
            self._signal_process = None  # Clear the process.
            self.logger.info("signal-cli stopped.")
        if self._link_process is not None:
            self.logger.info("Stopping signal-cli link process.")
            self._link_process.terminate()
            _, err = self._link_process.communicate()
            self._link_process = None
            self.logger.info("Link process stopped.")
        # Remove socket file:
        try:
            if isinstance(self._server_address, str):
                self.logger.info("Removing old socket file.")
                if os.path.exists(self._server_address):
                    os.remove(self._server_address)
        except Exception as e:
            self.logger.warning("Failed to remove old socket file: '%s': '%s'" % (self._server_address, str(e.args)))
        return

    def register_account(self,
                         number: str,
                         captcha: str,
                         voice: bool = False
                         ) -> tuple[bool, Account | str]:
        """
                Register a new account. NOTE: Subject to rate limiting.
                :param number: str: The phone number to register.
                :param captcha: str: The captcha from 'https://signalcaptchas.org/registration/generate.html', can
                                        include the 'signalcaptcha://'.
                :param voice: bool: True = Voice call verification, False = SMS verification.
                :returns: tuple[bool, Account | str]: The first element (bool) is True for success or failure.  The
                                                        second element on success is the new Account object, which
                                                        will remain in an unregistered state until verify is called
                                                        with the verification code.  Upon failure, the second element
                                                        will contain a string with an error message.
                :raises: TypeError: If number or captcha are not strings, or if voice is not a boolean.
                """
        # Log started:
        self.logger.info("Register started.")
        # Type check arguments:
        self.logger.debug("Type checks.")
        if not isinstance(number, str):
            self.logger.critical("TypeError: number is type '%s', expected 'str'."
                                 % str(type(number)))
            __type_error__("number", "str", number)
        if not isinstance(captcha, str):
            self.logger.critical("TypeError: captcha is type '%s', expected 'str'."
                                 % str(type(captcha)))
            __type_error__("captcha", "str", captcha)
        if not isinstance(voice, bool):
            self.logger.critical("TypeError: voice is type '%s', expected 'bool'."
                                 % str(type(voice)))
            __type_error__("voice", "bool", voice)
        self.logger.debug("Type checks passed.")
        # Value Check arguments:
        self.logger.debug("Value checks.")
        number_match = phone_number_regex.match(number)
        if number_match is None:
            error_message: str = "number must be in format +nnnnnnnn...."
            self.logger.error("Returning False, ValueError: %s" % error_message)
            return False, error_message
        if captcha.startswith('signalcaptcha://'):
            self.logger.debug("Stripping signalcaptcha:// from captcha.")
            captcha = captcha[16:]
        if not captcha.startswith('signal-recaptcha-') and not captcha.startswith('signal-hcaptcha'):
            error_message: str = "Invalid captcha."
            self.logger.error("Returning False, ValueError: %s" % error_message)
            return False, error_message
        # Check if the account exists, and isn't registered.
        account = self.accounts.get_by_number(number)
        if account is not None:
            if account.registered:
                error_message: str = "Account already registered."
                self.logger.error("Returning False, %s" % error_message)
                return False, error_message
        # Create register account command object and json command string:
        register_account_command_obj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "register",
            "params": {
                "account": number,
                "captcha": captcha,
                "voice": voice,
            }
        }
        json_command_str = json.dumps(register_account_command_obj) + '\n'
        # Communicate with signal:
        self.logger.info("Sending registration request.")
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict = json.loads(response_str)
        self.logger.info("Received registration response.")
        self.logger.debug("registration response_obj = '%s'" % str(response_obj))
        # Check for error:
        if 'error' in response_obj.keys():
            error_message = "ERROR: signal error, code: %i, message: %s" % (
                response_obj['error']['code'], response_obj['error']['message'])
            self.logger.error("Signal returned error: Code: %i, Message: %s"
                              % (response_obj['error']['code'], response_obj['error']['message']))

            # Delete local account data, since signal-cli creates data for the account.
            self.logger.info("Deleting incomplete account.")
            delete_local_data_command_obj = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "deleteLocalAccountData",
                "params": {
                    "account": number
                }
            }
            json_command_str = json.dumps(delete_local_data_command_obj) + '\n'
            # Communicate with signal:
            self.logger.debug("Sending delete command.")
            __socket_send__(self._sync_socket, json_command_str)
            response_str = __socket_receive__(self._sync_socket)  # output unused, we don't care if it failed.
            self.logger.debug("Delete request response: %s" % str(response_str))
            self.logger.error("Returning False: %s" % error_message)
            return False, error_message

        # No error found, get the new account:
        self.logger.info("Registration successful, getting new account..")
        new_accounts = self.accounts.__sync__()
        if len(new_accounts) == 0:
            new_account = None
        else:
            new_account = new_accounts[0]
        if new_account is None:
            self.logger.debug("Accounts.__sync__() didn't return any accounts, looking up by number.")
            new_account = self.accounts.get_by_number(number)
        self.logger.info("Returning True.")
        return True, new_account

    def start_link_account(self, device_name: Optional[str] = None) -> tuple[str, str, str]:
        """
        Start the link process for linking an existing account.
        :param device_name: Optional[str]: The name for this device.
        :returns: tuple[str, str, str]: The first element is the link url generated by signal, the second element is a
                                            text QR code string, or an empty string if qrencode is not installed.  The
                                            third element is a path to a generated png qrencode, or an empty string if
                                            qrencode is not installed. qrencode can be installed on debian based
                                            systems using sudo apt-get install qrencode.
        :raises: TypeError: If name is not a string or None.
        :raises: RuntimeError: If a link is already in progress when start_link_account is called a second time and
                                finish_link has not been called.
        """
        self.logger.info("Staring link account.")
        # Type check name:
        self.logger.debug("Type checks.")
        if device_name is not None and not isinstance(device_name, str):
            self.logger.critical("TypeError: device_name is type '%s', expected 'str'."
                                 % str(type(device_name)))
            __type_error__("name", "Optional[str]", device_name)
        # Check for a running process:
        if self._link_process is not None:
            error_message: str = "link already in progress."
            self.logger.critical("RuntimeError: %s" % error_message)
            raise RuntimeError(error_message)
        # create signal link command line:
        link_command_line = [self._signal_exec_path, '--config', self.config_path, 'link']
        if device_name is not None:
            link_command_line.extend(('--name', device_name))
        # Run the signal link process:
        try:
            self._link_process = Popen(link_command_line, text=True, stdout=PIPE, stderr=PIPE)
        except CalledProcessError as e:
            parse_signal_return_code(e.returncode, link_command_line, e.output)
            # :NO RETURN :
        # Gather the link from stdout
        signal_link = self._link_process.stdout.readline()
        signal_link = signal_link.rstrip()
        # Generate text qrcode:
        try:
            text_qr_code = check_output([self._qrencode_exec_path, '-o', '-', '--type=UTF8', signal_link])
            text_qr_code = text_qr_code.decode('UTF8')
        except CalledProcessError:
            text_qr_code = ''
        # Generate png qrcode:
        png_qr_code_file_name = "link-%s-qrcode.png" % str(device_name)
        png_qr_code_path: str = os.path.join(self.config_path, png_qr_code_file_name)
        try:
            check_call([self._qrencode_exec_path, '-o', png_qr_code_path, signal_link])
        except CalledProcessError:
            png_qr_code_path = ''
        return signal_link, text_qr_code, png_qr_code_path

    def finish_link(self) -> tuple[bool, Account | str]:
        """
        Finish the linking process after confirming the link on the primary device.
        :returns: tuple[bool, Account | str]: The first element is a bool representing success or failure; The second
                                                element on success will be the new Account object, or on failure will be
                                                a string containing an error message.
        :raises: RuntimeError: In the event that signal-cli success response changes.
        """
        # Check for a link process:
        if self._link_process is None:
            error_message = "link not started"
            return False, error_message
        # Wait for the process:
        return_code = self._link_process.wait()
        # Parse return_code:
        if return_code == 0:
            new_accounts = self.accounts.__sync__()
            if len(new_accounts) != 0:
                new_account = new_accounts[0]
            else:
                new_account = None
            response_line = self._link_process.stdout.readline()
            if DEBUG:
                print(response_line)
            if new_account is None:
                regex = r'^Associated with: (?P<number>.*)$'
                match = re.match(regex, response_line)
                if match is not None:
                    new_account = self.accounts.get_by_number(match['number'])
                    return True, new_account
                else:
                    # Shouldn't get here, return code is 0 (success).
                    raise RuntimeError("success response from signal must have changed.")
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
        """
        Start receiving messages for the given account.
        NOTE: Callback signature is (account: Account, message: Message)
        :param account: Account: The account to receive messages for.
        :param all_messages_callback: Optional[Callable]: Callback for all messages received.
        :param received_message_callback: Optional[Callable]: Callback for received messages. (regular message)
        :param receipt_message_callback: Optional[Callable]: Callback for receipt messages.
        :param sync_message_callback: Optional[Callable]: Callback for sync messages.
        :param typing_message_callback: Optional[Callable]: Callback for typing messages.
        :param story_message_callback: Optional[Callable]: Callback for story messages.
        :param payment_message_callback: Optional[Callable]: Callback for payment messages.
        :param reaction_message_callback: Optional[Callable]: Callback for reaction messages.
        :param call_message_callback: Optional[Callable]: Callback for incoming call messages.
        :returns: None
        :raises: TypeError: If the account is not an Account object, or if a callback is defined, but not callable.
        """
        # Argument checks NOTE: ReceiveThread type checks callbacks:
        if not isinstance(account, Account):
            __type_error__("account", "Account", account)
        # Start receive:
        thread_id = account.number
        thread = ReceiveThread(server_address=self._server_address,
                               command_socket=self._command_socket,
                               config_path=self.config_path,
                               account=account,
                               sticker_packs=self.sticker_packs,
                               all_messages_callback=all_messages_callback,
                               received_message_callback=received_message_callback,
                               receipt_message_callback=receipt_message_callback,
                               sync_message_callback=sync_message_callback,
                               typing_message_callback=typing_message_callback,
                               story_message_callback=story_message_callback,
                               payment_message_callback=payment_message_callback,
                               reaction_message_callback=reaction_message_callback,
                               call_message_callback=call_message_callback,
                               )
        thread.start()
        self._receive_threads[thread_id] = thread
        return

    def stop_receive(self, account: Account) -> bool:
        """
        Stop receiving messages for the given account.
        :param account: Account: The account to stop reception for.
        :returns: bool: True reception successfully stopped, False reception wasn't started.
        :raises: TypeError: If the parameter account is not an Account object.
        """
        # Argument checks:
        if not isinstance(account, Account):
            __type_error__("account", "Account", account)
        thread_id = account.number
        try:
            thread = self._receive_threads[thread_id]
        except KeyError:
            return False
        self._receive_threads[thread_id] = None
        thread.stop()
        return True
