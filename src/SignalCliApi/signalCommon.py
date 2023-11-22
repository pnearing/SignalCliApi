#!/usr/bin/env python3
"""
File: signalCommon.py
Common Constants, Vars, and helper functions.
"""
import json
from subprocess import check_output, CalledProcessError
from typing import Pattern, NoReturn, Optional, Any, Final
import socket
import select
import re
import logging
from enum import IntEnum, auto
from .signalExceptions import CommunicationsError, SignalError, InvalidServerResponse

###################
# Version:
###################
VERSION: Final[str] = '0.3.0'
"""Version of the library"""
########################################
# Regex:
########################################
phone_number_regex: Final[Pattern] = re.compile(r'(?P<number>\+\d+)')
"""Regex matching a phone number."""
uuid_regex: Final[Pattern] = re.compile(
    r'(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-f0-9]{12})'
)
"""Regex matching a UUID."""
#########################
# Strings:
#########################
UUID_FORMAT_STR: Final[str] = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
"""UUID format string."""
NUMBER_FORMAT_STR: Final[str] = "+nnnnnnn..."
"""Number format string."""
SELF_CONTACT_NAME: Final[str] = 'Note-To-Self'
"""The contact name for the self-contact."""
UNKNOWN_CONTACT_NAME: Final[str] = '<UNKNOWN-CONTACT>'
"""The default name for an unknown contact. If this the contact name it signals the library to update it if ever an
    actual name for the contact comes up."""
UNKNOWN_GROUP_NAME: Final[str] = '<UNKNOWN-GROUP>'
"""The default name for an unknown group. If this is the group name it signals the library to update it if even an
    actual group name comes up."""
UNKNOWN_DEVICE_NAME: Final[str] = '<UNKNOWN-DEVICE>'
"""The default name for an unknown device."""
PRIMARY_DEVICE_ID: Final[int] = 1
"""The device ID of the primary device for an account."""
STICKER_MANIFEST_FILENAME: Final[str] = 'manifest.json'
"""The filename of a sticker manifest file."""


###########################
# Enum's:
###########################
class CallbackIdx(IntEnum):
    """
    Enum to index the callbacks. (Callable, Optional[list[Any]])
    """
    CALLABLE = 0
    """Callback callable index."""
    PARAMS = 1
    """Callback parameters index."""


class MessageTypes(IntEnum):
    """
    Enum for message types:
    """
    NOT_SET = auto()
    """Message type not set."""
    SENT = auto()
    """Sent message type."""
    RECEIVED = auto()
    """Received message type."""
    TYPING = auto()
    """Typing message type."""
    RECEIPT = auto()
    """Receipt message type."""
    STORY = auto()
    """Story message type."""
    PAYMENT = auto()
    """Payment message type."""
    REACTION = auto()
    """Reaction message type."""
    GROUP_UPDATE = auto()
    """Group update message type."""
    SYNC = auto()
    """Sync message type."""
    CALL = auto()
    """Call message type."""


class RecipientTypes(IntEnum):
    """
    Enum to store message recipient types.
    """
    GROUP = auto()
    """Recipient is a Group."""
    CONTACT = auto()
    """Recipient is a Contact."""


class ConversationTypes(IntEnum):
    """
    Enum to store conversation types.
    """
    CONTACT = auto()
    """Conversation with a contact."""
    GROUP = auto()
    """Conversation with a group."""


class ReceiptTypes(IntEnum):
    """
    Enum to store different receipt types:
    """
    NOT_SET = auto()
    """Receipt type not set."""
    DELIVER = auto()
    """Delivery receipt type."""
    READ = auto()
    """Read message receipt type."""
    VIEWED = auto()
    """Viewed message receipt type."""


class AttachmentTypes(IntEnum):
    """
    Enum for attachment types:
    """
    NOT_SET = auto()
    """Attachment type not set."""
    TEXT = auto()
    """Attachment is a TextAttachment."""
    FILE = auto()
    """Attachment is an Attachment (file)."""


class SyncTypes(IntEnum):
    """
    Enum for different sync message types:
    """
    # Sync message types:
    NOT_SET = auto()
    """Sync type not set."""
    CONTACTS = auto()
    """Sync Contacts type."""
    GROUPS = auto()
    """Sync Groups type."""
    SENT_MESSAGES = auto()
    """Sync SentMessages type."""
    READ_MESSAGES = auto()
    """Sync read messages type."""
    BLOCKS = auto()
    """Sync blocked contacts or groups type."""


class TypingStates(IntEnum):
    """
    Enum to represent the two different typing states.
    """
    NOT_SET = auto()
    STARTED = auto()
    STOPPED = auto()

####################################
# Find command helpers:
####################################
def __find_xdgopen__() -> Optional[str]:
    """
    Use which to find xdg-open
    :return: Optional[str]: The path to xdg-open or None if not found.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __find_xdgopen__.__name__)
    logger.debug("Searching for xdg-open...")
    xdgopen_path: Optional[str]
    try:
        xdgopen_path = check_output(['which', 'xdg-open'], text=True).rstrip()
        logger.debug("xdg-open found at '%s'." % xdgopen_path)
    except CalledProcessError:
        logger.warning("xdg-open not found, the functions named display() will do nothing.")
        xdgopen_path = None
    return xdgopen_path


def __find_qrencode__() -> Optional[str]:
    """
    Use which to find qrencode.
    :return: Optional[str]: The path to qrencode, or None if not found.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __find_qrencode__.__name__)
    logger.debug("Searching for qrencode...")
    qrencode_path: Optional[str]
    try:
        qrencode_path = check_output(['which', 'qrencode'], text=True).rstrip()
        logger.debug("qrencode found at: %s" % qrencode_path)
    except CalledProcessError:
        qrencode_path = None
        logger.warning("qrencode not found, cannot generate link qr-codes.")
    return qrencode_path


def __find_convert__() -> Optional[str]:
    """
    Find the imageMagick convert utility.
    :return: Optional[str]: The full path convert, or None if not found.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __find_convert__.__name__)
    logger.debug("Searching for convert...")
    convert_path: Optional[str]
    try:
        convert_path = check_output(['which', 'convert'], text=True).rstrip()
        logger.debug("convert found at: %s" % convert_path)
        return convert_path
    except CalledProcessError:
        logger.warning("convert not found, cannot generate thumbnails.")
    return None


def __find_signal__() -> str | NoReturn:
    """
    Find signal-cli in it's many forms.
    :return: str | NoReturn: The path to [signal-cli | signal-cli-native | signal-cli-jre]
    :raises FileNotFoundError: If signal executable is not found.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __find_signal__.__name__)
    signal_path: str
    try:
        logger.debug("Searching for signal-cli...")
        signal_path = check_output(['which', 'signal-cli'], text=True)
        signal_path = signal_path.strip()
        logger.debug("signal-cli found at: %s" % signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli not found.")
    # Check for 'signal-cli-native':
    try:
        logger.debug("Searching for signal-cli-native...")
        signal_path = check_output(['which', 'signal-cli-native'], text=True)
        signal_path = signal_path.strip()
        logger.debug("signal-cli-native found at: %s" % signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli-native not found.")
    # Check for 'signal-cli-jre':
    try:
        logger.debug("Searching for signal-cli-jre...")
        signal_path = check_output(['which', 'signal-cli-jre'], text=True)
        signal_path = signal_path.strip()
        logger.debug("signal-cli-jre found at: %s" % signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli-jre not found.")
    # Exit if we couldn't find signal
    error_message: str = ("FATAL: Could not find [ signal-cli | signal-cli-native | signal-cli-jre ].  "
                          "Please ensure it's installed and in your $PATH environment variable.")
    logger.critical(error_message)
    raise FileNotFoundError(error_message)


def __parse_signal_return_code__(return_code: int, command_line: str | list[str], output: str) -> NoReturn:
    """
    Parse the signal return code.
    :param return_code: int: The return code from signal.
    :param command_line: str | list[str]: The command line used to call signal.
    :param output: str: The output generated by signal.
    :raises SignalError: All the time with the error message and exit code.
    """
    logger_name = __name__ + '.' + __parse_signal_return_code__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.error("signal-cli returned non-zero return code: %i" % return_code)
    if return_code == 1:
        error_message = "Exit code 1: Invalid command line: %s" % str(command_line)
        logger.critical("Raising SignalError(%s)." % error_message)
        raise SignalError(error_message, return_code)
    elif return_code == 2:
        error_message = "Exit Code 2: Unexpected error. %s" % output
        logger.critical("Raising SignalError(%s)." % error_message)
        raise SignalError(error_message, return_code)
    elif return_code == 3:
        error_message = "Exit Code 3: Server / Network error. Try again later: %s" % output
        logger.critical("Raising SignalError(%s)." % error_message)
        raise SignalError(error_message, return_code)
    elif return_code == 4:
        error_message = "Exit Code 4: Operation failed due to untrusted key: %s" % output
        logger.critical("Raising SignalError(%s)." % error_message)
        raise SignalError(error_message, return_code)
    else:
        error_message = "Exit Code %i: Unknown / unhandled error. Running '%s' returned output: %s" \
                        % (return_code, str(command_line), output)
        logger.critical("Raising SignalError(%s)." % error_message)
        raise SignalError(error_message, return_code)


####################################
# Socket helpers:
####################################
def __socket_create__(server_address: tuple[str, int] | str) -> socket.socket:
    """
    Create a socket.socket object based on the server address type.
    :param server_address: tuple[str, str] | str: The server address, either (HOSTNAME, PORT) or "PATH_TO_SOCKET".
    :return: socket.socket: The created socket.
    :raises CommunicationsError: On failure to create socket.
    """
    logger_name: str = __name__ + '.' + __socket_create__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    if isinstance(server_address, (tuple, list)):
        logger.debug("Creating INET socket.")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            error_message: str = "Failed to create INET socket: %s" % str(e.args)
            logger.critical("Raising CommunicationsError(%s)." % error_message)
            raise CommunicationsError(error_message, e)
    elif isinstance(server_address, str):
        logger.debug("Creating UNIX socket.")
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except socket.error as e:
            error_message: str = "Failed to create UNIX socket: %s" % str(e.args)
            logger.critical("Raising CommunicationsError(%s)." % error_message)
            raise CommunicationsError(error_message, e)
    else:
        logger.critical("Raising TypeError:")
        logger.critical(__type_err_msg__('server_address', 'tuple[str, int] | str', server_address))
        __type_error__('server_address', 'tuple[str, int] | str', server_address)
    return sock


def __socket_connect__(sock: socket.socket, server_address: tuple[str, int] | str) -> None:
    """
    Connect a socket to a server address.
    :param sock: socket.socket: The socket to connect with.
    :param server_address: tuple[str, int] | str: The server address: (HOSTNAME, PORT) or "PATH_TO_SOCKET"
    :return: None
    :raises CommunicationsError: On failure to connect.
    """
    logger_name: str = __name__ + '.' + __socket_connect__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        logger.debug("Connecting to: %s" % str(server_address))
        sock.connect(server_address)
    except socket.error as e:
        error_message = "Couldn't connect to socket: %s" % (str(e.args))
        logger.critical("socket.error: %s, Raising CommunicationsError." % error_message)
        raise CommunicationsError(error_message, e)
    logger.debug("Connected to: %s" % str(server_address))
    return


def __socket_send__(sock: socket.socket, message: str) -> int:
    """
    Send a message to the socket.
    :param sock: socket.socket: The socket to send the message over.
    :param message: str: The message to send.
    :return: int: The number of bytes sent.
    :raises CommunicationsError: On failure to send.
    """
    logger_name: str = __name__ + '.' + __socket_send__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        logger.debug("Sending message: %s" % message)
        bytes_sent = sock.send(message.encode())
    except socket.error as e:
        error_message = "Couldn't send to socket: %s" % (str(e.args))
        logger.critical("socket.error: %s, Raising CommunicationsError." % error_message)
        raise CommunicationsError(error_message, e)
    logger.debug("Sent %i bytes." % bytes_sent)
    return bytes_sent


def __socket_receive__(sock: socket.socket) -> str:
    """
    Read a string from a socket; Blocks until msg read.
    :param sock: socket.socket: The socket to read from.
    :return: str: The read message.
    :raises CommunicationsError: On failure to read from the socket.
    """
    logger_name: str = __name__ + '.' + __socket_receive__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        while True:
            readable, _, _ = select.select([sock], [], [], 0.5)
            if len(readable) > 0:
                message = b''
                byte_count: int = 0
                while True:
                    data = sock.recv(1)
                    message += data
                    byte_count += 1
                    try:
                        if data.decode() == '\n':
                            logger.debug("Received %i bytes." % byte_count)
                            break
                    except UnicodeDecodeError:
                        pass
                logger.debug("Returning message: %s" % message.decode())
                return message.decode()
    except socket.error as e:
        error_message = "Failed to read from socket: %s" % (str(e.args))
        logger.critical("socket.error: %s" % error_message)
        raise CommunicationsError(error_message, e)


def __socket_close__(sock: socket.socket) -> None:
    """
    Close a socket.
    :param sock: socket.socket: The socket to close.
    :return: None
    :raises CommunicationsError: On error closing socket.
    """
    logger_name: str = __name__ + '.' + __socket_close__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        logger.debug("Closing socket.")
        sock.close()
    except socket.error as e:
        error_message = "Couldn't close socket connection: %s" % (str(e.args))
        logger.critical(error_message)
        raise CommunicationsError(error_message, e)
    logger.debug("Socket closed successfully.")
    return None


################################
# Signal response helpers:
################################
def __parse_signal_response__(response_str: str) -> dict[str, Any] | NoReturn:
    """
    Parse signal JSON response string in to a python dict; response_obj.
    :param response_str: str: The json encoded string.
    :return: dict[str, Any]: The response_obj.
    """
    logger: logging.Logger = logging.getLogger(__name__ + __parse_signal_response__.__name__)
    try:
        return json.loads(response_str)
    except json.JSONDecodeError as e:
        error_message: str = "Failed to load JSON from server response: %s" % e.msg
        logger.critical("Raising InvalidServerResponse(%s)." % error_message)
        raise InvalidServerResponse(error_message, e)


def __check_response_for_error__(response_obj: dict[str, Any],
                                 non_fatal_errors: list[int] = [],
                                 ) -> tuple[bool, int, str] | NoReturn:
    """
    Check the signal response object for error.
    :param response_obj: dict[str, Any]: The response object from signal.
    :param non_fatal_errors: list[int]: Any non-fatal error codes.
    :return: tuple[bool, int, str] | NoReturn: If no error occurs, returns the tuple: (False, 0, 'no error'); If a
        non-fatal error occurs, return the tuple (True, error_code: int, error_message: str); If a fatal error occurs
        then SignalError is raised.
    :raises: SignalError: On fatal error.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __check_response_for_error__.__name__)
    if 'error' in response_obj.keys():
        error: dict[str, Any] = response_obj['error']
        if error['code'] in non_fatal_errors:
            warning_message: str = "Signal error, code: %i, message: %s" % (error['code'], error['message'])
            logger.warning(warning_message)
            return True, error['code'], error['message']
        else:
            error_message: str = "Signal error, code: %i, message: %s" % (error['code'], error['message'])
            logger.error("Raising SignalError(%s)" % error_message)
            raise SignalError(response_obj['error']['message'], response_obj['error']['code'], error_message)
    return False, 0, 'no error'


################################
# Type checking helpers:
###############################
def __type_err_msg__(var_name: str, valid_type_names: str, var: Any) -> str:
    """
    Generate a type error message.
    :param var_name: str: The variable name that failed the type check.
    :param valid_type_names: str: Expected type names.
    :param var: Any: The received type.
    :return: str: The received objet.
    """
    return "'%s' is of type '%s', expected: '%s'." % (var_name, str(type(var)), valid_type_names)


def __type_error__(var_name: str, valid_type_name: str, var: Any) -> NoReturn:
    """
    Raise a TypeError with a nice message.
    :param var_name: str: The name of the variable that failed the type check.
    :param valid_type_name: str: The names of the expected types.
    :param var: Any: The received object.
    :return: NoReturn
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __type_error__.__name__)
    error_message: str = __type_err_msg__(var_name, valid_type_name, var)
    logger.critical("--> TypeError(%s)." % error_message)
    raise TypeError(error_message)
