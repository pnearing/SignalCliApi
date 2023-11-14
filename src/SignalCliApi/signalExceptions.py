#!/usr/bin/env python3
"""
File: signalExceptions.py
Collection of Exceptions to throw.
"""
import json
import socket
from typing import Optional, Any
import logging


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
        :param traceback: str: The traceback of the error.
        :param args: tuple[Any]: Any additional arguments to add to the Exception.
        """
        Error.__init__(self, message, error, *args)
        return

