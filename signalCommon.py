#!/usr/bin/env python3

from subprocess import check_output, CalledProcessError
from typing import Pattern, NoReturn, Optional, Any
import socket
import select
import re

########################################
# Regex:
########################################
phone_number_regex: Pattern = re.compile(r'(?P<number>\+\d+)')
uuid_regex: Pattern = re.compile(
    r'(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-f0-9]{12})')

#########################
# Strings:
#########################
UUID_FORMAT_STR = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
NUMBER_FORMAT_STR = "+nnnnnnn..."


####################################
# xdg-open helper:
####################################
def find_xdgopen() -> Optional[str]:
    """Use which to find xdg-open"""
    xdgopen_path: Optional[str]
    try:
        xdgopen_path = check_output(['which', 'xdg-open'])
        xdgopen_path = xdgopen_path.rstrip()
    except CalledProcessError:
        xdgopen_path = None
    return xdgopen_path


####################################
# qrencode helper:
####################################
def find_qrencode() -> Optional[str]:
    """Use which to fild qrencode."""
    qrencode_path: Optional[str]
    try:
        qrencode_path = check_output(['which', 'qrencode'])
        qrencode_path = qrencode_path.rstrip()
    except CalledProcessError:
        qrencode_path = None
    return qrencode_path


####################################
# Signal cli helpers:
####################################
def find_signal() -> str | NoReturn:
    """Find signal-cli in it's many forms. Returns str, exeption FileNotFound if signal not found."""
    signal_path = None
    try:
        signal_path = check_output(['which', 'signal-cli'], text=True)
        signal_path = signal_path.strip()
    except CalledProcessError as e:
        signal_path = None
    # Check for 'signal-cli-native':
    if signal_path is None:
        try:
            signal_path = check_output(['which', 'signal-cli-native'], text=True)
            signal_path = signal_path.strip()
        except CalledProcessError as e:
            signal_path = None
    # Check for 'signal-cli-jre':
    if signal_path is None:
        try:
            signal_path = check_output(['which', 'signal-cli-jre'], text=True)
            signal_path = signal_path.strip()
        except CalledProcessError as e:
            signal_path = None
    # Exit if we couldn't find signal
    if signal_path is None:
        error_message = "FATAL: Could not find [ signal-cli | signal-cli-native | signal-cli-jre ]."
        error_message += " Please ensure it's installed and in you $PATH environment variable."
        raise FileNotFoundError(error_message)
    return signal_path


def parse_signal_return_code(return_code: int, command_line: str | list[str], output: str) -> NoReturn:
    if return_code == 1:
        error_message = "Exit code 1: Invalid command line: %s" % str(command_line)
        raise RuntimeError(error_message)
    elif return_code == 2:
        error_message = "Exit Code 2: Unexpected error. %s" % output
        raise RuntimeError(error_message)
    elif return_code == 3:
        error_message = "FATAL: Server / Network error. Try again later: %s" % output
        raise RuntimeError(error_message)
    elif return_code == 4:
        error_message = "FATAL: Operation failed due to untrusted key: %s" % output
        raise RuntimeError(error_message)
    else:
        error_message = "FATAL: Unknown / unhandled error. Running '%s' returned exit code: %i : %s" % (
                                                                                                    str(command_line),
                                                                                                    return_code,
                                                                                                    output)
        raise RuntimeError(error_message)


####################################
# Socket helpers:
####################################

def __socket_create__(server_address: tuple[str, int] | str) -> socket.socket:
    """Create a socket.socket object based on server address type."""
    if isinstance(server_address, tuple):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif isinstance(server_address, str):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    else:
        error_message = "server_address must be of type tuple(str,int) or str"
        raise TypeError(error_message)
    return sock


def __socket_connect__(sock: socket.socket, server_address: tuple[str, int] | str) -> None:
    """Connect a socket to a server address."""
    try:
        sock.connect(server_address)
    except socket.error as e:
        error_message = "FATAL: Couldn't connect to socket: %s" % (str(e.args))
        raise RuntimeError(error_message)
    return


def __socket_send__(sock: socket.socket, message: str) -> int:
    """Send a message to the socket."""
    try:
        bytes_sent = sock.send(message.encode())
    except socket.error as err:
        error_message = "FATAL: Couldn't send to socket: %s" % (str(err.args))
        raise RuntimeError(error_message)
    return bytes_sent


def __socket_receive__(sock: socket.socket) -> str:
    """Read a string from a socket. Blocks until msg read."""
    try:
        while True:
            readable, writeable, erred = select.select([sock], [], [], 0.5)
            if len(readable) > 0:
                message = b''
                while True:
                    data = sock.recv(1)
                    message += data
                    try:
                        if data.decode() == '\n':
                            break
                    except Exception as err:
                        pass
                return message.decode()
    except socket.error as err:
        error_message = "FATAL: Failed to read from socket: %s" % (str(err.args))
        raise RuntimeError(error_message)
    return None


def __socket_close__(sock: socket.socket) -> None:
    """Close a socket."""
    try:
        sock.close()
    except socket.error as e:
        error_message = "FATAL: Couldn't close socket connection: %s" % (str(e.args))
        raise RuntimeError(error_message)
    return None


################################
# Type checking helper:
###############################
def __type_error__(var_name: str, valid_type_name: str, var: Any) -> NoReturn:
    errorMessage = "%s must be of type %s, not: %s" % (var_name, valid_type_name, str(type(var)))
    raise TypeError(errorMessage)
