#!/usr/bin/env python3
"""The primary signal cli interface."""
# pylint: disable= R0902, R0912, R0913, R0915, R1732, W0511, W0718
import logging
import json
import os
import socket
from subprocess import Popen, PIPE, CalledProcessError, check_output, check_call
from time import sleep
from typing import Optional, Callable, Any, NoReturn

from .signal_account import SignalAccount
from .signal_accounts import SignalAccounts
from . import signal_common
from .signal_common import (__type_error__, __find_signal__, __find_qrencode__,
                            __parse_signal_return_code__, __socket_create__,
                            __socket_connect__, __socket_close__, __socket_receive_blocking__,
                            __socket_send__, PHONE_NUMBER_REGEX, __type_err_msg__,
                            __parse_signal_response__, __check_response_for_error__)
from .run_callback import __run_callback__, __type_check_callback__
from .run_callback import set_suppress_error as set_callback_suppress_error
from .run_callback import type_string as callback_type_string
from .signal_link_thread import SignalLinkThread
from .signal_receive_thread import SignalReceiveThread
from .signal_sticker import SignalStickerPacks
from .signal_exceptions import (LinkNotStarted, LinkInProgress, SignalError,
                                SignalAlreadyRunningError)
from .signal_errors import LinkError


class SignalCli:
    """Signal cli object."""

    def __init__(self,
                 signal_config_path: Optional[str] = None,
                 signal_exec_path: Optional[str] = None,
                 server_address: Optional[list[str, int] | tuple[str, int] | str] = None,
                 log_file_path: Optional[str] = None,
                 start_signal: bool = True,
                 callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                 callback_raises_error: bool = True,
                 debug: bool = False,
                 ) -> None:
        """
        Initialize signal-cli, starting the process if required.
        :param signal_config_path: Optional[str]: The path to the directory signal-cli should use.
        :param signal_exec_path: Optional[str]: The path to the signal-cli executable.
        :param server_address: Optional[list[str , int] | tuple[str, int] | str]: If signal-cli is
        already started, the address of the server, if a unix socket, use a str, otherwise use a
        tuple/list[hostname:str,port:int]
        :param log_file_path: Optional[str]: The path to the signal log file, if None, no logging
        is preformed.
        :param start_signal: Bool: True = start a signal-cli process, False = signal-cli is already
        running.
        :param callback: Optional[tuple[Callable, Optional[list[Any]]]]: The call back as a tuple,
        the first element being the callable, and the second element; If not None, is a list of any
        parameters to provide to the callback.  The callback signature is: (status: str, *params)
        :param callback_raises_error: bool: Should we suppress exceptions caused by callbacks? True,
         callback exceptions will only be logged to the logging facility. False, the exception
         CallbackCausedError is raised with the information and Exception object of what went wrong.
        :param debug: Bool: Produce debug output on stdout.
        :raises TypeError: If a parameter is of invalid type.
        :raises FileNotFoundError: If a file / directory doesn't exist when it should.
        :raises FileExistsError: If a socket file exists when it shouldn't.
        :raises RuntimeError: If an error occurs while loading signal data, more information in
        the error message.
        """
        # Setup logging.
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        logger.info("Initialize.")
        # Argument checks:

        # Check signal config path:
        if signal_config_path is not None:
            if not isinstance(signal_config_path, str):
                logger.critical("Raising TypeError:")
                __type_error__("signal_config_path", "str",
                               signal_config_path)
            elif not os.path.exists(signal_config_path) and not start_signal:
                error_message = f"signal_config_path '{signal_config_path}' doesn't exist."
                logger.critical("Raising FileNotFoundError: %s", error_message)
                raise FileNotFoundError(error_message)

        # Check signal exec path:
        if signal_exec_path is not None:
            if not isinstance(signal_exec_path, str):
                logger.critical("Raising TypeError:")
                __type_error__("signal_exec_path", "str", signal_exec_path)
            elif not os.path.exists(signal_exec_path) and start_signal:
                error_message = f"signal_exec_path '{signal_exec_path}' does not exist."
                logger.critical("Raising FileNotFoundError: %s", error_message)
                raise FileNotFoundError(error_message)

        # Check start signal:
        if not isinstance(start_signal, bool):
            logger.critical("Raising TypeError:")
            __type_error__("start_signal", "bool", start_signal)

        # Check the server address:
        if server_address is not None:
            if isinstance(server_address, (list, tuple)):
                if len(server_address) != 2:
                    error_message: str = "server_address must have a length of 2."
                    logger.critical("Raising ValueError(%s)", error_message)
                    raise ValueError(error_message)
                if not isinstance(server_address[0], str):
                    logger.critical("Raising TypeError:")
                    __type_error__("server_address[0]", "str",
                                   server_address[0])
                if not isinstance(server_address[1], int):
                    logger.critical("Raising TypeError:")
                    __type_error__("server_address[1]", "int",
                                   server_address[1])
            elif isinstance(server_address, str):
                if os.path.exists(server_address) and start_signal:
                    error_message: str = (f"socket path '{server_address}' already exists. Perhaps"
                                          f"signal is already running.")
                    logger.critical("Raising FileExistsError(%s)", error_message)
                    raise FileExistsError(error_message)
                if not os.path.exists(server_address) and not start_signal:
                    error_message: str = (f"Socket path '{server_address}' does not exist. Perhaps"
                                          f"signal isn't running.")
                    logger.critical("Raising FileNotFoundError(%s).", error_message)
                    raise FileNotFoundError(error_message)
            else:
                logger.critical("Raising TypeError:")
                __type_error__('server_address', 'list[str, int] | tuple[str, int] | str',
                               server_address)

        # Check the log file path:
        if log_file_path is not None:
            if not isinstance(log_file_path, str):
                logger.critical("Raising TypeError:")
                __type_error__("log_file_path", "str", log_file_path)

        # Check callback:
        if not __type_check_callback__(callback):
            logger.critical("Raising TypeError:")
            __type_error__('callback', callback_type_string(), callback)

        # Check suppress_cb_error:
        if not isinstance(callback_raises_error, bool):
            logger.critical("Raising TypeError:")
            __type_error__("suppress_cb_error", "bool", callback_raises_error)

        # Check debug:
        if not isinstance(debug, bool):
            logger.critical("Raising TypeError:")
            __type_error__('debug', 'bool', debug)

        # Set internal vars:
        # Set _CALLBACK_RAISES_ERROR value:
        signal_common.CALLBACK_RAISES_ERROR = callback_raises_error
        if callback_raises_error:
            set_callback_suppress_error(False)
        else:
            set_callback_suppress_error(True)

        # Set the config path:
        self.config_path: str
        """The full path to the signal config directory."""
        if signal_config_path is not None:
            self.config_path = signal_config_path
        else:
            home_path = os.environ.get('HOME')
            self.config_path = os.path.join(home_path, '.local', 'share', 'signal-cli')
        logger.debug('signal-cli config path: %s', self.config_path)

        # Set signal exec path:
        self._signal_exec_path: str
        """The full path to the signal-cli executable."""
        if signal_exec_path is not None:
            logger.debug("Setting signal_exec_path to passed parameter.")
            self._signal_exec_path = signal_exec_path
        elif start_signal:
            logger.debug("Finding signal_exec_path.")
            self._signal_exec_path = __find_signal__()  # Raises FileNotFoundError if not found.
        else:
            logger.debug("Setting signal_exec_path to None.")
            self._signal_exec_path = None
        logger.debug('signal-cli exec path: %s', self._signal_exec_path)

        # Set server address:
        self._server_address: list[str, int] | tuple[str, int] | str
        """"The server address of the signal-cli socket."""
        if server_address is not None:
            logger.debug("Setting server_address from parameter.")
            self._server_address = server_address
        else:
            logger.debug("Building server_address, selecting UNIX socket.")
            self._server_address = os.path.join(self.config_path, 'socket')
        logger.debug("Server address: %s", str(self._server_address))
        signal_common.SERVER_ADDRESS = self._server_address

        # Store debug:
        signal_common.DEBUG = debug
        """True if we should produce debugging output."""
        # Store log file path:
        self._log_file_path: Optional[str] = log_file_path
        """The path to the signal-cli log file."""
        # Store callback:
        self._callback: Optional[tuple[Callable, Optional[list[Any]]]] = callback
        """The start up call back."""
        self._suppress_cb_error: bool = callback_raises_error
        """Should we suppress callback errors?"""
        # set var to hold the main signal process
        self._signal_process: Optional[Popen] = None
        """The main signal-cli process."""
        # Set sync socket:
        self._sync_socket: Optional[socket.socket] = None
        """The socket to preform sync operations with."""
        # Set command socket:
        self._command_socket: Optional[socket.socket] = None
        """The socket to preform command operations with."""
        # Set var to hold the link request:
        self._link_uri: Optional[str] = None
        """The signal-cli request for linking a new account."""
        # Set qrencode exec path:
        self._qrencode_exec_path: Optional[str] = __find_qrencode__()
        """The full path to the qrencode executable."""
        # Set external properties and objects:
        # Set accounts:
        self.accounts: Optional[SignalAccounts] = None
        """The SignalAccounts object."""
        # Set sticker packs:
        self.sticker_packs: Optional[SignalStickerPacks] = None
        """The known SignalStickerPacks object."""
        # Start signal-cli if requested:
        if start_signal:
            logger.info("Starting signal-cli.")
            __run_callback__(self._callback, 'starting signal-cli')
            signal_command_line: list[str] = self.__build_signal_command_line__()
            response: bool | CalledProcessError = self.__start_signal__(signal_command_line)
            if response is not True:
                __parse_signal_return_code__(response.returncode, signal_command_line,
                                             response.output)  # NoReturn
            logger.info("signal-cli started.")
            __run_callback__(self._callback, "signal-cli started")

        # Wait for the socket to appear:
        if isinstance(self._server_address, str):
            if start_signal:
                logger.debug("server_address is a socket, and we're starting signal, wait for"
                             "socket to appear.")
                __run_callback__(self._callback, "start waiting for socket")
                self.__wait_for_signal_socket_file__(self._server_address)
                logger.debug("socket found.")
                __run_callback__(self._callback, 'socket found')

        # Create sockets and connect to them:
        logger.info("Connecting to sockets.")
        __run_callback__(self._callback, 'connecting to sockets')
        self.__connect_to_sockets__()
        logger.info("Connected to sockets.")
        __run_callback__(self._callback, 'connected to sockets')

        # Load stickers:
        logger.info("Loading sticker packs.")
        self.sticker_packs = SignalStickerPacks(config_path=self.config_path)
        """Known SignalStickerPacks object."""

        # Load accounts:
        logger.info("Loading accounts.")
        self.accounts = SignalAccounts(sync_socket=self._sync_socket,
                                       command_socket=self._command_socket,
                                       config_path=self.config_path,
                                       sticker_packs=self.sticker_packs, do_load=True)
        """The SignalAccounts object."""

        # Create dict to hold processes:
        self._receive_threads: dict[str, Optional[SignalReceiveThread]] = {}
        """The dict to store the receive threads."""

        self._link_thread: Optional[SignalLinkThread] = None
        """The link thread that's running."""
        logger.info("Initialization complete.")

    def __connect_to_sockets__(self) -> None | NoReturn:
        """
        Connect to and store the sockets.
        :return: None | NoReturn.
        :raises CommunicationsError: On error creating or connecting to a socket.
        """
        logger: logging.Logger = logging.getLogger(
            __name__ + '.' + self.__connect_to_sockets__.__name__)
        logger.debug("Creating and connecting to command socket.")
        self._command_socket = __socket_create__(self._server_address)  # Raises CommunicationsError
        __socket_connect__(self._command_socket, self._server_address)  # Raises CommunicationsError
        logger.debug("Connected to command socket.")
        logger.debug("Creating and connecting to sync socket.")
        self._sync_socket = __socket_create__(self._server_address)  # Raises CommunicationsError
        __socket_connect__(self._sync_socket, self._server_address)  # Raises CommunicationsError
        logger.debug("Connected to sync socket.")

    def __close_sockets__(self) -> None | NoReturn:
        """
        Close and clear sockets.
        :return: None | NoReturn: None if all closed, NoReturn on error closing socket.
        :raises CommunicationError: On error closing socket.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__close_sockets__.__name__)
        if self._sync_socket is not None:
            logger.debug("Closing sync socket.")
            __socket_close__(self._sync_socket)  # Raises CommunicationsError
            self._sync_socket = None
            logger.debug("Sync socket closed.")
        if self._command_socket is not None:
            logger.debug("Closing command socket.")
            __socket_close__(self._command_socket)  # Raises CommunicationsError
            self._command_socket = None
            logger.debug("Command socket closed.")

    def __wait_for_signal_socket_file__(self, socket_file_path: str, timeout: float = 10.0) -> None:
        """
        Wait for the signal socket file to appear.
        :param socket_file_path: str: The full path to the socket file.
        :param timeout: float: The timeout in .5 second increments.
        :return: None
        :raises TimeoutError on timeout.
        """
        logger: logging.Logger = logging.getLogger(
            __name__ + '.' + self.__wait_for_signal_socket_file__.__name__)
        current_time: float = 0.0
        while not os.path.exists(socket_file_path):
            std_err = self._signal_process.stderr.readline()
            if std_err.find('Config file is in use by another instance') != -1:
                logger.critical("Another signal-cli process is running. Please either connect to"
                                "that instance or stop it from running before continuing.")
                raise SignalAlreadyRunningError()
            logger.debug("Waiting for socket...")
            __run_callback__(self._callback, 'waiting for socket')
            sleep(0.5)
            current_time += 0.5
            if current_time >= timeout:
                error_message: str = "timeout while waiting for signal to create socket."
                logger.critical("Raising TimeoutError(%s).", error_message)
                raise TimeoutError(error_message)
        sleep(1)  # Give it a second to stabilize

    def __build_signal_command_line__(self) -> list[str]:
        # Build signal-cli command line:
        logger: logging.Logger = logging.getLogger(
            __name__ + '.' + self.__build_signal_command_line__.__name__)
        signal_command_line = [self._signal_exec_path]
        if self._log_file_path is not None:
            signal_command_line.extend(['--verbose', '--log-file', self._log_file_path])
        signal_command_line.extend(['--config', self.config_path, 'daemon'])
        if isinstance(self._server_address, str):
            signal_command_line.extend(['--socket', self._server_address])
        else:
            address = f"{self._server_address[0]}:{self._server_address[1]}"
            signal_command_line.extend(['--tcp', address])
        signal_command_line.extend(['--no-receive-stdout', '--receive-mode', 'manual'])
        logger.debug("Signal command line: %s", str(signal_command_line))
        return signal_command_line

    def __start_signal__(self, signal_command_line: list[str]) -> bool | CalledProcessError:
        """
        Start and store the signal-cli process.
        :param signal_command_line: list[str]: The command line to run.
        :return: True | CalledProcessError: True if started, Called process error on exit-code > 0.
        """
        # Log start:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__start_signal__.__name__)
        logger.info("Starting signal-cli.")

        # Run signal-cli:
        try:
            self._signal_process = Popen(signal_command_line, text=True, stdout=PIPE, stderr=PIPE)
        except CalledProcessError as e:
            logger.critical("Failed to start signal-cli.")
            __run_callback__(self._callback, "failed to start signal-cli")
            return e
        logger.info("signal-cli started.")
        __run_callback__(self._callback, "signal-cli started")

        # Give signal 5 seconds to start
        __run_callback__(self._callback, "waiting for signal-cli to initialize")
        sleep(5)
        __run_callback__(self._callback, 'signal-cli initialized')
        return True

    #################################
    # Internal methods:
    #################################
    def __remove_socket_file__(self) -> bool:
        """
        Remove the signal socket file.
        :return: bool: Returns True when the file is removed, False if it wasn't.
        """
        logger: logging.Logger = logging.getLogger(
            __name__ + '.' + self.__remove_socket_file__.__name__)
        if isinstance(self._server_address, str) and os.path.exists(self._server_address):
            logger.info("Removing old socket file.")
            try:
                os.remove(self._server_address)
                return True
            except (OSError, FileNotFoundError, PermissionError) as e:
                logger.warning("Failed to remove old socket file: '%s': '%s'", self._server_address,
                               str(e.args))
        return False

    #################################
    # Overrides:
    #################################
    def __del__(self):
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__del__.__name__)

        try:
            for thread in self._receive_threads.values():
                if thread is not None:
                    thread.join(1.0)
        except Exception as e:
            logger.warning("Error occurred during termination of receive process.")
            logger.warning("Error type: %s", str(type(e)))
            logger.warning("Error strArgs: %s", str(e.args))

        if self._signal_process is not None:
            try:
                self.stop_signal()
            except Exception as e:
                logger.warning("Error occurred during termination of signal-cli process.")
                logger.warning("Error type: %s", str(type(e)))
                logger.warning("Error strArgs: %s", str(e.args))

    #################################
    # Methods:
    #################################
    def stop_signal(self) -> None:
        """
        Stop the signal-cli process.
        :returns: None
        :raises CommunicationsError: On error closing a socket.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.stop_signal.__name__)

        # Close the sockets:
        logger.debug("Closing sockets.")
        __run_callback__(self._callback, "closing sockets")
        self.__close_sockets__()
        logger.debug("Sockets closed.")
        __run_callback__(self._callback, "sockets closed")

        # Terminate process:
        if self._signal_process is not None:
            logger.info("Stopping signal-cli.")
            __run_callback__(self._callback, "stopping signal-cli")
            self._signal_process.terminate()  # Kill the process (Sends SigTerm)
            logger.debug("Flushing pipes.")
            stdout, stderr = self._signal_process.communicate()  # Flush the pipes.
            logger.debug("STDOUT: %s", str(stdout))
            logger.debug("STDERR: %s", str(stderr))
            self._signal_process = None  # Clear the process.
            logger.info("signal-cli stopped.")
            __run_callback__(self._callback, "signal-cli stopped")

        # Remove socket file:
        if isinstance(self._server_address, str):
            self.__remove_socket_file__()

    def register_account(self,
                         number: str,
                         captcha: str,
                         voice: bool = False
                         ) -> tuple[bool, SignalAccount | str]:
        """
                Register a new account. NOTE: Subject to rate limiting.
                :param number: str: The phone number to register.
                :param captcha: str: The captcha from
                    'https://signalcaptchas.org/registration/generate.html', can include the
                    'signalcaptcha://'.
                :param voice: bool: True = Voice call verification, False = SMS verification.
                :returns: tuple[bool, SignalAccount | str]: The first element (bool) is True for
                    success or failure.  The second element on success is the new SignalAccount
                    object, which will remain in an unregistered state until verify is called
                    with the verification code.  Upon failure, the second element will contain a
                    string with an error message.
                :raises: TypeError: If number or captcha are not strings, or if voice is not a
                    boolean.
                """
        # Log started:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.register_account.__name__)
        logger.info("Register started.")

        # Type check arguments:
        logger.debug("Type checks.")
        if not isinstance(number, str):
            logger.critical("TypeError: number is type '%s', expected 'str'.", str(type(number)))
            __type_error__("number", "str", number)
        if not isinstance(captcha, str):
            logger.critical("TypeError: captcha is type '%s', expected 'str'.", str(type(captcha)))
            __type_error__("captcha", "str", captcha)
        if not isinstance(voice, bool):
            logger.critical("TypeError: voice is type '%s', expected 'bool'.", str(type(voice)))
            __type_error__("voice", "bool", voice)
        logger.debug("Type checks passed.")
        # Value Check arguments:
        logger.debug("Value checks.")
        number_match = PHONE_NUMBER_REGEX.match(number)
        if number_match is None:
            error_message: str = "number must be in format +nnnnnnnn...."
            logger.error("Returning False, ValueError: %s", error_message)
            return False, error_message
        if captcha.startswith('signalcaptcha://'):
            logger.debug("Stripping signalcaptcha:// from captcha.")
            captcha = captcha[16:]
        if (not captcha.startswith('signal-recaptcha-') and
                not captcha.startswith('signal-hcaptcha')):
            error_message: str = "Invalid captcha."
            logger.error("Returning False, ValueError: %s", error_message)
            return False, error_message
        # Check if the account exists, and isn't registered.
        account = self.accounts.get_by_number(number)
        if account is not None:
            if account.registered:
                error_message: str = "Account already registered."
                logger.error("Returning False, %s", error_message)
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
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        # TODO: Fix error checking:
        # Check for error:
        if 'error' in response_obj.keys():
            # Delete local account data, since signal-cli creates data for the account.
            logger.info("Deleting incomplete account.")
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
            __socket_send__(self._sync_socket, json_command_str)
            response_str = __socket_receive_blocking__(
                self._sync_socket)  # output unused, we don't care if it failed.
            # TODO: Error check delete request response and at least warn about it.
            logger.debug("Delete account response: %s", response_str)
            error_message = (f"Signal error, code: {response_obj['error']['code']},"
                             f"message: {response_obj['error']['message']}")
            logger.error("Raising SignalError(%s)", error_message)
            raise SignalError(response_obj['error']['message'], response_obj['error']['code'],
                              error_message)

        # No error found, get the new account:
        logger.debug("Registration successful, syncing accounts with disk...")
        new_accounts = self.accounts.__sync__()
        if len(new_accounts) == 0:
            error_message: str = "Failed to locate new account."
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)
        logger.info("Account registered. Don't forget to verify.")
        return True, new_accounts[0]

    def start_link(self,
                   gen_text_qr: bool = True,
                   png_qr_file_path: Optional[str] = None,
                   ) -> tuple[str, Optional[str], Optional[str]]:
        """
        Start the link process for linking an existing account.
        :param gen_text_qr: bool: True, generate text qr-code, False, do not.
        :param png_qr_file_path: Optional[str]: The file path to generate the png qr code at,
            if None, the qr code is not generated.
        :returns: tuple[str, str, str]: The first element is the link url generated by signal.
            The second element is a text QR code string, or an empty string if qrencode is not
            installed, or 'gen_text_qr' is set to False. The third element is a path to a generated
            png qrencode, or an empty string if qrencode is not installed.
        :raises: TypeError: If name is not a string or None.
        :raises: LinkInProgress: If a link is already in progress when start_link_account is
            called a second time and finish_link has not been called.
        :raises InvalidServerResponse: If the signal link doesn't seem valid.
        """
        logger = logging.getLogger(__name__ + '.' + self.start_link.__name__)
        logger.info("Staring link process...")

        # Type checks:
        if not isinstance(gen_text_qr, bool):
            logger.critical("Raising TypeError:")
            logger.critical(__type_err_msg__('gen_text_qr', 'bool', gen_text_qr))
            __type_error__('gen_text_qr', 'bool', gen_text_qr)

        if png_qr_file_path is not None and not isinstance(png_qr_file_path, str):
            logger.critical("Raising TypeError:")
            logger.critical(__type_err_msg__("png_qr_code_file_path", 'Optional[str]',
                                             png_qr_file_path))
            __type_error__('png_qr_code_file_path', 'Optional[str]', png_qr_file_path)

        # Check for a running link request:
        if self._link_uri is not None:
            logger.critical("Raising LinkInProgressError().")
            raise LinkInProgress()

        # Ensure sigal is running:
        if self._signal_process is None:
            error_message: str = "signal-clil not running"
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message)

        # Create link request object:
        link_request_command_obj: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "startLink",
        }

        # Create json command string:
        json_command_str: str = json.dumps(link_request_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._command_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)
        __check_response_for_error__(response_obj)

        # Gather the link from response obj:
        self._link_uri = response_obj['result']['deviceLinkUri']

        # Generate text qrcode:
        text_qr_code: str = ''
        if self._qrencode_exec_path is not None and gen_text_qr:
            command_line: list[str] = [self._qrencode_exec_path, '-o', '-', '--type=UTF8', '-m',
                                       '1', self._link_uri]
            logger.debug("Attempting to generate UTF8 QR-Code...")
            try:
                bytes_qr_code: bytes = check_output(command_line)
                text_qr_code: str = bytes_qr_code.decode('UTF8')
                # Clean up qr-code by adding missing top border:
                border_string: str = '\u2584' * len(text_qr_code.splitlines(keepends=False)[0])
                text_qr_code = border_string + '\n' + text_qr_code
                logger.debug("UTF8 QR-Code successfully created.")
            except CalledProcessError:
                logger.warning("Failed to generate UTF8 QR-Code.")

        # Generate png qrcode:
        if self._qrencode_exec_path is not None and png_qr_file_path is not None:
            logger.debug("Attempting to generate png QR-Code...")
            try:
                check_call([self._qrencode_exec_path, '-o', png_qr_file_path, self._link_uri])
                logger.debug("png QR-Code successfully generated.")
            except CalledProcessError:
                logger.warning("Failed to generate png QR-Code.")

        # Linking started successfully:
        logger.info("Link process successfully started.")
        return self._link_uri, text_qr_code, png_qr_file_path

    def finish_link(self,
                    device_name: Optional[str] = None,
                    ) -> tuple[bool, SignalAccount | LinkError]:
        """
        Finish the linking process after confirming the link on the primary device.
        :param device_name: Optional[str]: The device name to give this link.
        :returns: tuple[bool, SignalAccount | str]: The first element is a bool representing
            success or failure; The second element on success will be the new SignalAccount object,
            or on failure will be a string containing an error message.
        :raises LinkNotStarted: If the link process hasn't been started yet.
        :raises InvalidServerResponse: If the signal success code is not recognized.
        """
        logger_name: str = __name__ + '.' + self.finish_link.__name__
        logger: logging.Logger = logging.getLogger(logger_name)
        logger.info("Finish link process started.")

        # Type check name:
        if device_name is not None and not isinstance(device_name, str):
            logger.critical("Raising TypeError:")
            logger.critical(__type_err_msg__('device_name', 'Optional[str]', device_name))
            __type_error__("device_name", "Optional[str]", device_name)

        # Check for a link process:
        if self._link_uri is None:
            logger.critical("Raising LinkNotStarted().")
            raise LinkNotStarted()

        # Check for running signal-cli:
        if self._signal_process is None:
            signal_message: str = "signal-cli not running"
            logger.critical("Raising RuntimeError(%s).", signal_message)
            raise RuntimeError(signal_message)

        # Generate the finishLink command object:
        link_finish_command_obj: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "finishLink",
            "params": {
                "deviceLinkUri": self._link_uri,
            }
        }
        if device_name is not None:
            link_finish_command_obj['params']['deviceName'] = device_name

        # Generate json command string:
        json_command_str = json.dumps(link_finish_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._command_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._command_socket)
        # Raises Invalid server response:
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(response_obj,
                                                                                   [-1, -2, -3])
        if error_occurred:
            self._link_uri = None
            if signal_code == -1:  # User already exists:
                return False, LinkError.USER_EXISTS
            if signal_code == -2:  # TODO: FIND OUT THIS ERROR.
                return False, LinkError.UNKNOWN
            if signal_code == -3:  # Timeout
                return False, LinkError.TIMEOUT

        # Gather linked number from response:
        linked_number: str = response_obj['result']['number']
        logger.debug("Link successful for account: %s.", linked_number)

        # Sync accounts and get the new account:
        logger.debug("Syncing accounts with disk.")
        new_accounts = self.accounts.__sync__()
        if len(new_accounts) == 0:
            signal_message: str = "Failed to locate new account."
            logger.critical("Raising RuntimeError(%s).", signal_message)
            raise RuntimeError(signal_message)
        self._link_uri = None
        return True, new_accounts[0]

    def start_receive(self,
                      account: SignalAccount,
                      all_messages_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                      received_message_callback: Optional[
                          tuple[Callable, Optional[list[Any]]]] = None,
                      receipt_message_callback: Optional[
                          tuple[Callable, Optional[list[Any]]]] = None,
                      sync_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                      typing_message_callback: Optional[
                          tuple[Callable, Optional[list[Any]]]] = None,
                      story_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                      payment_message_callback: Optional[
                          tuple[Callable, Optional[list[Any]]]] = None,
                      reaction_message_callback: Optional[
                          tuple[Callable, Optional[list[Any]]]] = None,
                      call_message_callback: Optional[tuple[Callable, Optional[list[Any]]]] = None,
                      do_expunge: bool = True,
                      ) -> SignalReceiveThread:
        """
        Start receiving messages for the given account.
        NOTE: Callback signature is (account: SignalAccount, message: SignalMessage)
        :param account: SignalAccount: The account to receive messages for.
        :param all_messages_callback: Optional[Callable]: Callback for all messages received.
        :param received_message_callback: Optional[Callable]: Callback for normal received messages.
        :param receipt_message_callback: Optional[Callable]: Callback for receipt messages.
        :param sync_message_callback: Optional[Callable]: Callback for sync messages.
        :param typing_message_callback: Optional[Callable]: Callback for typing messages.
        :param story_message_callback: Optional[Callable]: Callback for story messages.
        :param payment_message_callback: Optional[Callable]: Callback for payment messages.
        :param reaction_message_callback: Optional[Callable]: Callback for reaction messages.
        :param call_message_callback: Optional[Callable]: Callback for incoming call messages.
        :param do_expunge: bool: Honour expiry times.
        :returns: SignalReceiveThread: The created thread.
        :raises: TypeError: If the account is not an SignalAccount object, or if a callback is
            defined, but not callable.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.start_receive.__name__)
        logger.info("Start receive started.")
        # Argument checks NOTE: SignalReceiveThread type checks callbacks:
        if not isinstance(account, SignalAccount):
            logger.critical("Raising TypeError:")
            logger.critical(__type_err_msg__('account', 'SignalAccount', account))
            __type_error__("account", "SignalAccount", account)

        # Start receive:
        thread_id: str = account.number
        thread = SignalReceiveThread(server_address=self._server_address,
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
                                     do_expunge=do_expunge,
                                     )
        thread.start()
        self._receive_threads[thread_id] = thread
        account.is_receiving = True
        return thread

    def stop_receive(self, account: SignalAccount) -> bool:
        """
        Stop receiving messages for the given account.
        :param account: SignalAccount: The account to stop reception for.
        :returns: bool: True reception successfully stopped, False reception wasn't started.
        :raises: TypeError: If the parameter account is not an SignalAccount object.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.stop_receive.__name__)
        logger.info("Stopping reception thread.")
        # Argument checks:
        if not isinstance(account, SignalAccount):
            logger.critical("Raising TypeError:")
            logger.critical(__type_err_msg__('account', "SignalAccount", account))
            __type_error__("account", "SignalAccount", account)
        # Set the thread id:
        thread_id: str = account.number
        # Check that the thread was started:
        if thread_id not in self._receive_threads:
            logger.warning("Trying to stop receive for an account that isn't receiving.")
            return False
        # Get the thread and stop it:

        thread = self._receive_threads[thread_id]
        logger.debug("Stopping thread...")
        thread.stop()
        thread.join()
        account.is_receiving = False
        logger.debug("Thread stopped.")
        self._receive_threads[thread_id] = None
        logger.info("Reception stopped.")
        return True

    def start_link_thread(self,
                          callback: tuple[Callable, Optional[list[Any] | tuple[Any, ...]]],
                          gen_text_qr: bool = True,
                          png_qr_file_path: Optional[str] = None,
                          device_name: Optional[str] = None,
                          wait_time: float = 0.25,
                          ) -> SignalLinkThread:
        """
        Create and return the signal link thread.
        :param callback: tuple[Callable, Optional[list[Any] | tuple[Any, ...]]]: The callback to
            call with the status updates, with a signature of:
            some_callback(status:str, data:Optional[tuple[Optional[str], Optional[str]] | str |
            SignalAccount) -> bool
            If the callback returns True, then the link process is canceled, and the socket is
            closed.
        :param gen_text_qr: bool: Should we generate a text qr-code?
        :param png_qr_file_path: Optional[str]: Path to the png qr-code file. If None, the qr-code
            is not generated.
        :param device_name: Optional[str]: The device name. If None, the default set by signal-cli
            is used.
        :param wait_time: float: The amount of time to give the socket to respond.
        :return: None.
        """
        if self._link_thread is not None:
            raise LinkInProgress()

        self._link_thread = SignalLinkThread(
            server_address=self._server_address,
            accounts=self.accounts,
            callback=callback,
            gen_text_qr=gen_text_qr,
            png_qr_file_path=png_qr_file_path,
            device_name=device_name,
            wait_time=wait_time
        )
        self._link_thread.start()
        return self._link_thread

    def stop_link_thread(self) -> None:
        """
        Stop the running link thread.
        :return: None
        """
        if self._link_thread is None:
            raise LinkNotStarted()
        if self._link_thread.is_complete or self._link_thread.is_canceled:
            return
        self._link_thread.cancel()
        self._link_thread = None
        return

    ############################################
    # Properties:
    ############################################
    @property
    def link_thread(self) -> Optional[SignalLinkThread]:
        """
        The current link thread.
        :return: Optional[SignalLinkThread]: The SignalLinkThread object, other-wise if not
            linking, None.
        """
        return self._link_thread
