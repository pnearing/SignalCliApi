#!/usr/bin/env python3
"""
File: signal_common.py
    Common Constants, Vars, and helper functions. Common display strings are put here for future
    localization in case this takes off.
"""
# pylint: disable= R1702, W0511, W0603
import json
from subprocess import check_output, CalledProcessError
from typing import Pattern, NoReturn, Optional, Any, Final
import socket
import select
import re
import logging
from enum import IntEnum, auto, Enum, IntFlag
from .signal_exceptions import (CommunicationsError, SignalError, InvalidServerResponse)

########################################
# Regex:
########################################
PHONE_NUMBER_REGEX: Final[Pattern] = re.compile(r'(?P<number>\+\d+)')
"""Regex matching a phone number."""
UUID_REGEX: Final[Pattern] = re.compile(
    r'(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-f0-9]{12})'
)
"""Regex matching a UUID."""
#########################
# Constants:
#########################
UUID_FORMAT_STR: Final[str] = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
"""UUID format string."""
NUMBER_FORMAT_STR: Final[str] = "+nnnnnnn..."
"""Number format string."""
SELF_CONTACT_NAME: Final[str] = 'Note-To-Self \u2318'
"""The contact name for the self-contact."""
UNKNOWN_CONTACT_NAME: Final[str] = '<UNKNOWN-CONTACT>'
"""The default name for an unknown contact. If this the contact name it signals the library to
update it if ever an actual name for the contact comes up."""
UNKNOWN_GROUP_NAME: Final[str] = '<UNKNOWN-GROUP>'
"""The default name for an unknown group. If this is the group name it signals the library to
update it if even an actual group name comes up."""
UNKNOWN_DEVICE_NAME: Final[str] = '<UNKNOWN-DEVICE>'
"""The default name for an unknown device."""
PRIMARY_DEVICE_ID: Final[int] = 1
"""The device ID of the primary device for an account."""
STICKER_MANIFEST_FILENAME: Final[str] = 'manifest.json'
"""The filename of a sticker manifest file."""

STRINGS: dict[str, str] = {
    'lessThanASecond': 'less than a second ago',
    'secondAgo': 'second ago',
    'secondsAgo': 'seconds ago',
    'minuteAgo': 'minute ago',
    'minutesAgo': 'minutes ago',
    'hourAgo': 'hour ago',
    'hoursAgo': 'hours ago',
    'dayAgo': 'day ago',
    'daysAgo': 'days ago',
}
"""Common strings that can be translated."""
###########################
# Vars:
###########################
DEBUG: bool = False
"""Preform debug actions."""
CALLBACK_RAISES_ERROR: bool = False
"""Does a callback raise an exception?"""
_CLOSING_SOCKET: bool = False
"""Are we closing a socket right now?"""
_OPEN_SOCKETS: list[dict[str, socket.socket | str | tuple[str, int]]] = []
"""A list of open sockets, and the server they're associated with so we can automatically
reconnect them."""
SERVER_ADDRESS: Optional[str | tuple[str, int]] = None
"""The current server address."""
HONOUR_VIEW_ONCE: bool = True
"""Should we honour the view once message property?"""
HONOUR_EXPIRY: bool = True
"""Should we honour the expiry times of the messages?"""


###########################
# Enum's:
###########################
class MessageFilter(IntFlag):
    """
    IntFlag enum for different filters.
    """
    NONE = 0
    """No filter applied."""
    READ = auto()
    """Filter if the message has been read."""
    NOT_READ = auto()
    """Filter if the message has not been read."""
    VIEWED = auto()
    """Filter if the message has been viewed."""
    NOT_VIEWED = auto()
    """Filter if the message has not been viewed."""
    DELIVERED = auto()
    """Filter if the message has been delivered."""
    NOT_DELIVERED = auto()
    """Filter if the message has not been delivered."""


def valid_message_filter(message_filter: int) -> bool:
    """
    Evaluate a filter and determine if it's valid.
    :param message_filter: int: The filter.
    :return: bool: True the fileter if valid, False it is not.
    """
    max_value: int = (
            MessageFilter.READ | MessageFilter.NOT_READ |
            MessageFilter.VIEWED | MessageFilter.NOT_VIEWED |
            MessageFilter.DELIVERED | MessageFilter.NOT_DELIVERED
    )
    if (message_filter < 0) or (message_filter > max_value):
        return False
    if (message_filter & MessageFilter.READ) and (message_filter & MessageFilter.NOT_READ):
        return False
    if (message_filter & MessageFilter.VIEWED) and (message_filter & MessageFilter.NOT_VIEWED):
        return False
    if (message_filter & MessageFilter.DELIVERED) and (message_filter &
                                                       MessageFilter.NOT_DELIVERED):
        return False
    return True


class LinkAccountCallbackStates(Enum):
    """
    The link message state messages.
    """
    GENERATE_URI_START = 'generating link uri'
    """Generating link uri start message."""
    GENERATE_URI_STOP = 'link uri generated'
    """Generating link uri stop message."""
    GENERATE_QR_START = 'generating qr-code'
    """Generating qr-code start message."""
    GENERATE_QR_STOP = 'qr-code generated'
    """Generating qr-code stop message."""
    FINISH_START = 'finish link started'
    """Finish link started."""
    LINK_SUCCESS = 'link success'
    """Link was successful."""
    LINK_EXISTS_ERROR = 'account already linked'
    """Link failed, account exists."""
    LINK_TIMEOUT_ERROR = 'link process time-out'
    """Link failed, time out."""
    LINK_UNKNOWN_ERROR = 'an unknown error occurred'  # TODO: FIND OUT THIS ERROR.
    """Link failed, -2 error code."""
    LINK_WAITING = 'waiting for response from signal.'
    """Link waiting on response from signal."""
    LINK_CANCELED = 'the link process has been canceled'
    """Link process has been canceled."""


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
    """Recipient is a SignalGroup."""
    CONTACT = auto()
    """Recipient is a SignalContact."""
    NOT_SET = auto()
    """Recipient type is not set."""


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
    """SignalReceipt type not set."""
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
    """SignalAttachment is a SignalTextAttachment."""
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
    SENT_REACTION = auto()
    """Sync sent Reaction type."""
    READ_MESSAGES = auto()
    """Sync read messages type."""
    BLOCKS = auto()
    """Sync blocked contacts or groups type."""


class TypingStates(IntEnum):
    """
    Enum to represent the two different typing states.
    """
    NOT_SET = auto()
    """User typing state not set."""
    STARTED = auto()
    """User started typing."""
    STOPPED = auto()
    """User stopped typing."""


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
        logger.debug("xdg-open found at '%s'.", xdgopen_path)
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
        logger.debug("qrencode found at: %s", qrencode_path)
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
        logger.debug("convert found at: %s", convert_path)
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
        logger.debug("signal-cli found at: %s", signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli not found.")
    # Check for 'signal-cli-native':
    try:
        logger.debug("Searching for signal-cli-native...")
        signal_path = check_output(['which', 'signal-cli-native'], text=True)
        signal_path = signal_path.strip()
        logger.debug("signal-cli-native found at: %s", signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli-native not found.")
    # Check for 'signal-cli-jre':
    try:
        logger.debug("Searching for signal-cli-jre...")
        signal_path = check_output(['which', 'signal-cli-jre'], text=True)
        signal_path = signal_path.strip()
        logger.debug("signal-cli-jre found at: %s", signal_path)
        return signal_path
    except CalledProcessError:
        logger.debug("signal-cli-jre not found.")
    # Exit if we couldn't find signal
    error_message: str = ("FATAL: Could not find [ signal-cli | signal-cli-native |"
                          "signal-cli-jre ]. Please ensure it's installed and in your "
                          "$PATH environment variable.")
    logger.critical(error_message)
    raise FileNotFoundError(error_message)


def __parse_signal_return_code__(return_code: int, command_line: str | list[str], output: str
                                 ) -> NoReturn:
    """
    Parse the signal return code.
    :param return_code: int: The return code from signal.
    :param command_line: str | list[str]: The command line used to call signal.
    :param output: str: The output generated by signal.
    :raises SignalError: All the time with the error message and exit code.
    """
    logger_name = __name__ + '.' + __parse_signal_return_code__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.error("signal-cli returned non-zero return code: %i", return_code)
    if return_code == 1:
        error_message = f"Exit code 1: Invalid command line: {str(command_line)}"
        logger.critical("Raising SignalError(%s).", error_message)
        raise SignalError(error_message, return_code)
    if return_code == 2:
        error_message = f"Exit Code 2: Unexpected error. {output}"
        logger.critical("Raising SignalError(%s).", error_message)
        raise SignalError(error_message, return_code)
    if return_code == 3:
        error_message = f"Exit Code 3: Server / Network error. Try again later: {output}"
        logger.critical("Raising SignalError(%s).", error_message)
        raise SignalError(error_message, return_code)
    if return_code == 4:
        error_message = f"Exit Code 4: Operation failed due to untrusted key: {output}"
        logger.critical("Raising SignalError(%s).", error_message)
        raise SignalError(error_message, return_code)

    error_message = (f"Exit Code {return_code}: Unknown / unhandled error. Running "
                     f"'{str(command_line)}' returned output: {output}")
    logger.critical("Raising SignalError(%s).", error_message)
    raise SignalError(error_message, return_code)


####################################
# Socket helpers:
####################################
def __find_socket_dict_by_socket__(sock: socket.socket) -> Optional[dict[str, socket.socket | str |
                                                                              tuple[str, int]]]:
    for socket_dict in _OPEN_SOCKETS:
        if socket_dict['socket'] == sock:
            return socket_dict
    return None


def __socket_create__(server_address: Optional[tuple[str, int] | str] = None) -> socket.socket:
    """
    Create a socket.socket object based on the server address type.
    :param server_address: tuple[str, str] | str: The server address, either (HOSTNAME, PORT) or
        "PATH_TO_SOCKET".
    :return: socket.socket: The created socket.
    :raises CommunicationsError: On failure to create socket.
    """
    if server_address is None:
        server_address = SERVER_ADDRESS

    if server_address is None:
        raise ValueError("No server address defined.")

    logger_name: str = __name__ + '.' + __socket_create__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)

    if isinstance(server_address, (tuple, list)):
        logger.debug("Creating INET socket.")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            error_message: str = f"Failed to create INET socket: {str(e.args)}"
            logger.critical("Raising CommunicationsError(%s).", error_message)
            raise CommunicationsError(error_message, e) from e
    elif isinstance(server_address, str):
        logger.debug("Creating UNIX socket.")
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except socket.error as e:
            error_message: str = f"Failed to create UNIX socket: {str(e.args)}"
            logger.critical("Raising CommunicationsError(%s).", error_message)
            raise CommunicationsError(error_message, e) from e
    else:
        logger.critical("Raising TypeError:")
        logger.critical(__type_err_msg__('server_address', 'tuple[str, int] | str', server_address))
        __type_error__('server_address', 'tuple[str, int] | str', server_address)
    # Create the socket dict and append it to the socket list.
    socket_dict: dict[str, socket.socket | str | tuple[str, int]] = {
        'server': server_address,
        'socket': sock,
        'status': 'created'
    }
    _OPEN_SOCKETS.append(socket_dict)
    return sock


def __socket_connect__(sock: socket.socket, server_address: Optional[tuple[str, int] | str] = None
                       ) -> None:
    """
    Connect a socket to a server address.
    :param sock: socket.socket: The socket to connect with.
    :param server_address: tuple[str, int] | str: The server address: (HOSTNAME, PORT) or
        "PATH_TO_SOCKET"
    :return: None
    :raises CommunicationsError: On failure to connect.
    """
    if server_address is None:
        server_address = SERVER_ADDRESS
    if server_address is None:
        raise ValueError("Server address not defined.")

    logger_name: str = __name__ + '.' + __socket_connect__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        # logger.debug("Connecting to: %s" % str(server_address))
        # sock.connect(server_address)
        logger.debug("Connecting to: %s", str(server_address))
        sock.connect(server_address)
    except socket.error as e:
        error_message = f"Couldn't connect to socket: {str(e.args)}"
        logger.critical("socket.error: %s, Raising CommunicationsError.", error_message)
        raise CommunicationsError(error_message, e) from e
    socket_dict = __find_socket_dict_by_socket__(sock)
    socket_dict['status'] = 'connected'
    logger.debug("Connected to: %s", str(server_address))


def __socket_reconnect__(sock: socket.socket) -> None:
    logger: logging.Logger = logging.getLogger(__name__ + '.' + __socket_reconnect__.__name__)
    socket_dict = __find_socket_dict_by_socket__(sock)
    if socket_dict['status'] == 'connected':
        try:
            __socket_close__(sock)
        except socket.error:
            warning_message = "Error while closing socket, ignoring."
            logger.warning(warning_message)
        try:
            __socket_connect__(sock, socket_dict['server'])
        except socket.error as e:
            error_message = f"Couldn't reconnect the socket: {str(e.args)}"
            logger.critical("socket.error: %s, raising CommunicationsError.", error_message)
            raise CommunicationsError(error_message, e) from e


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
        logger.debug("Sending message: %s", message)
        bytes_sent = sock.send(message.encode())
    except socket.error as e:
        if e.args[0] == 32:
            logger.warning("Error while sending message. Broken pipe. Reconnecting.")
            __socket_reconnect__(sock)
            try:
                logger.debug("Resending message: %s", message)
                bytes_sent = sock.send(message.encode())
            except socket.error as err:
                error_message = f"Sending still failed: {str(e.args)}"
                logger.critical("resending message failed: %s, raising CommunicationsError.",
                                error_message)
                raise CommunicationsError(error_message, e) from err
        else:
            error_message = f"Couldn't send to socket: {str(e.args)}"
            logger.critical("socket.error: %s, Raising CommunicationsError.", error_message)
            raise CommunicationsError(error_message, e) from e
    logger.debug("Sent %i bytes.", bytes_sent)
    return bytes_sent


def __socket_receive_blocking__(sock: socket.socket) -> str:
    """
    Read a string from a socket; Blocks until msg read.
    :param sock: socket.socket: The socket to read from.
    :return: str: The read message.
    :raises CommunicationsError: On failure to read from the socket.
    """
    logger_name: str = __name__ + '.' + __socket_receive_blocking__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        while True:
            readable, _, erred = select.select([sock], [], [sock], 0.5)
            if len(erred) > 0:
                logger.critical("GOT ERRORS DURING SELECT.")
            if len(readable) > 0:
                message = b''
                byte_count: int = 0
                while True:
                    data = sock.recv(1)
                    message += data
                    byte_count += 1
                    try:
                        if data.decode() == '\n':
                            logger.debug("Received %i bytes.", byte_count)
                            break
                    except UnicodeDecodeError:
                        pass
                logger.debug("Returning message: %s", message.decode())
                return message.decode()
    except socket.error as e:
        error_message = f"Failed to read from socket: {str(e.args)}"
        if _CLOSING_SOCKET and e.args[0] == 9:
            logger.info("Read error received while closing socket. This is normal during shutdown.")
        else:
            logger.critical("socket.error: %s", error_message)
        raise CommunicationsError(error_message, e) from e


def __socket_receive_non_blocking__(sock: socket.socket, wait_time: float = 0.1) -> Optional[str]:
    """
    Read a string from a socket; Blocks until msg read.
    :param sock: socket.socket: The socket to read from.
    :param wait_time: float: The waiting time in seconds for a message to appear.
    :return: Optional[str]: The read message, or None if wait_time elapsed.
    :raises CommunicationsError: On failure to read from the socket.
    """
    logger_name: str = __name__ + '.' + __socket_receive_non_blocking__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    try:
        readable, _, erred = select.select([sock], [], [sock], wait_time)
        if len(erred) > 0:
            logger.critical("GOT ERRORS WHILE SELECTING SOCKET.")
        if len(readable) > 0:
            message = b''
            byte_count: int = 0
            while True:
                data = sock.recv(1)
                message += data
                byte_count += 1
                try:
                    if data.decode() == '\n':
                        logger.debug("Received %i bytes.", byte_count)
                        break
                except UnicodeDecodeError:
                    pass
            logger.debug("Returning message: %s", message.decode())
            return message.decode()
    except socket.error as e:
        error_message = f"Failed to read from socket: {str(e.args)}"
        if _CLOSING_SOCKET:
            logger.warning("Socket read error while closing socket."
                           "This is normal during shutdown.")
        else:
            logger.critical("socket.error: %s", error_message)
        raise CommunicationsError(error_message, e) from e
    return None


def __socket_close__(sock: socket.socket) -> None:
    """
    Close a socket.
    :param sock: socket.socket: The socket to close.
    :return: None
    :raises CommunicationsError: On error closing socket.
    """
    global _CLOSING_SOCKET
    logger_name: str = __name__ + '.' + __socket_close__.__name__
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.debug("Closing socket.")
    _CLOSING_SOCKET = True
    try:
        sock.close()
    except socket.error as e:
        error_message = f"Couldn't close socket connection: {str(e.args)}"
        logger.critical(error_message)
        raise CommunicationsError(error_message, e) from e
    _CLOSING_SOCKET = False
    logger.debug("Socket closed successfully.")


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
        error_message: str = f"Failed to load JSON from server response: {e.msg}"
        logger.critical("Raising InvalidServerResponse(%s).", error_message)
        raise InvalidServerResponse(error_message, e) from e


def __check_response_for_error__(response_obj: dict[str, Any],
                                 non_fatal_errors: list[int] | tuple[int, ...] = (),
                                 ) -> tuple[bool, int, str] | NoReturn:
    """
    Check the signal response object for error.
    :param response_obj: dict[str, Any]: The response object from signal.
    :param non_fatal_errors: list[int]: Any non-fatal error codes.
    :return: tuple[bool, int, str] | NoReturn: If no error occurs, returns the tuple:
        (False, 0, 'no error'); If a non-fatal error occurs, returns the tuple
        (True, error_code: int, error_message: str); If a fatal error occurs then SignalError is
        raised.
    :raises: SignalError: On fatal error.
    """
    logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                               __check_response_for_error__.__name__)
    if 'error' in response_obj.keys():
        error: dict[str, Any] = response_obj['error']
        if error['code'] in non_fatal_errors:
            warning_message: str = (f"Signal error, code: {error['code']}, "
                                    f"message: {error['message']}")
            logger.warning(warning_message)
            return True, error['code'], error['message']

        error_message: str = f"Signal error, code: {error['code']}, message: {error['message']}"
        logger.error("Raising SignalError(%s)", error_message)
        raise SignalError(response_obj['error']['message'], response_obj['error']['code'],
                          error_message)
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
    return f"'{var_name}' is of type '{str(type(var))}', expected: '{valid_type_names}'."


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
    logger.critical("--> TypeError(%s).", error_message)
    raise TypeError(error_message)
