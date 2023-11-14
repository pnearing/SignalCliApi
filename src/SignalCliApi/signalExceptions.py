#!/usr/bin/env python3
"""
File: signalExceptions.py
Collection of Exceptions to throw.
"""
import json
import socket
from typing import Optional


class Error(Exception):
    """
    Base signal error 
    """
    def __init__(self, message: str, error: Optional[Exception], *args: tuple) -> None:
        """
        Base exception to throw when an error occurs.
        :param message: str: The error message.
        :param error: Optional[Exception]: The actual exception that was raised.
        :param args: tuple[*Any]: Additional arguments to store in the Exception. 
        """
        Exception.__init__(self, *args)
        self._message: str = message
        self._error: Optional[Exception] = error
        return
    
    @property
    def message(self) -> str:
        """
        The error message.
        :return: str
        """
        return self._message

    @property
    def error(self) -> Optional[Exception]:
        """
        The Exception that caused this error.
        :return: Optional[Exception]: The Exception object.
        """
        return self._error


class InvalidServerResponse(Error):
    """
    signal-cli provided us with invalid JSON.
    """
    def __init__(self, message: str, error: Optional[json.JSONDecodeError], *args: tuple) -> None:
        """
        Initialise InvalidServerResponse error.
        :param message: str: The error message.
        :param traceback: str: The JSON error traceback.
        :param json_msg: str: The JSON error message.
        :param args: tuple[Any, ...]: Additional arguments to store in the Exception.
        """
        Error.__init__(self, message, error, *args)
        self._json_msg: Optional[str] = None
        if error is not None:
            self._json_msg = error.msg
        return

    @property
    def json_msg(self) -> Optional[str]:
        """
        The JSON message describing the JSON encoding error.
        :return: Optional[str] The error message if available.
        """
        return self._json_msg


class CommunicationsError(Error):
    """
    An error occurred during socket communications.
    """
    def __init__(self, message: str, error: socket.error, *args: tuple) -> None:
        """
        Initialize CommunicationsError.
        :param message: str: The error message.
        :param error: socket.error: The socket error that caused the error.
        :param args: tuple[Any]: Any additional arguments to add to the Exception.
        """
        Error.__init__(self, message, error, *args)
        return


class InvalidDataFile(Error):
    """
    Exception to throw when an error occurs while loading a signal-cli data file.
    """
    def __init__(self, message: str, error: json.JSONDecodeError | KeyError, file_path: str, *args: tuple) -> None:
        """
        Initialize an InvalidDataFile Error.
        :param message: str: The error message.
        :param error: JSONDecodeError | KeyError: The exception that caused the error.
        :param file_path: The full path to the offending file.
        :param args: tuple[Any]: Any additional arguments to store in the exception.
        """
        Error.__init__(self, message, error, *args)
        self._file_path: str = file_path
        self._json_msg: Optional[str] = None
        if isinstance(error, json.JSONDecodeError):
            self._json_msg = error.msg
        return

    @property
    def file_path(self) -> str:
        """
        The full path to the offending file.
        :return: str: The file path.
        """
        return self._file_path

    @property
    def json_msg(self) -> Optional[str]:
        """
        The JSON decoding error message, if available, otherwise None.
        :return: Optional[str]: The JSON decoding error message, or None.
        """
        return self._json_msg


class UnsupportedVersion(Error):
    """
    Exception to throw when encountering an unsupported version.
    """
    def __init__(self, message: str, version: int, supported_versions: tuple, *args: tuple) -> None:
        """
        Initialize an UnsupportedVersion error.
        :param message: str: The error message.
        :param version: int: The version causing the issue.
        :param supported_versions: tuple[*int]: The supported versions of the library.
        :param args: tuple[*Any]: Any additional arguments to store in the Exception.
        """
        Error.__init__(self, message, None, *args)
        self._version: int = version
        self._supported_versions: tuple = supported_versions
        return

    @property
    def version(self) -> int:
        """
        The version that is unsupported.
        :return: int: The version number.
        """
        return self._version

    @property
    def supported_versions(self) -> tuple:
        """
        The versions supported by the library.
        :return: tuple[*int]: The supported versions.
        """
        return self._supported_versions


class LinkInProgress(Error):
    """
    Exception to throw when start_link is called twice in a row.
    """
    def __init__(self, *args: tuple) -> None:
        """
        Initialize LinkInProgress error.
        :param args: tuple[*Any]: Any additional arguments to store in the Exception.
        """
        Error.__init__(self, "Link already in progress.", None, *args)
        return


class LinkNotStarted(Error):
    """
    Exception to throw when the link hasn't been started yet and finish_link is called.
    """
    def __init__(self, *args: tuple) -> None:
        """
        Initialize a LinkNotStarted error.
        :param args: tuple[*Any]: Any additional arguments to store in the exception.
        """
        Error.__init__(self, "Link not started.", None, *args)
        return
