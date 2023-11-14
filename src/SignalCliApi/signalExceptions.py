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
    def __init__(self, message: str, error: Optional[Exceptionstr(e.args)], *args: tuple) -> None:
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
    def __init__(self, message: str, error: json.JSONDecodeError, *args: tuple) -> None:
        """
        Initialise InvalidServerResponse error.
        :param message: str: The error message.
        :param traceback: str: The JSON error traceback.
        :param json_msg: str: The JSON error message.
        :param args: tuple[Any, ...]: Additional arguments to store in the Exception.
        """
        Error.__init__(self, message, error, *args)
        self._json_msg: str = error.msg
        return

    @property
    def json_msg(self) -> str:
        """The JSON message describing the JSON encoding error."""
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
