#!/usr/bin/env python3
"""
File: signal_exceptions.py
Collection of Exceptions to throw.
"""
import json
import socket
from typing import Optional, Any


class Error(Exception):
    """
    Base signal error 
    """
    def __init__(self, message: str, error: Optional[Exception], *args) -> None:
        """
        Base exception to throw when an error occurs.
        :param message: str: The error message.
        :param error: Optional[Exception]: The actual exception that was raised.
        :param args: tuple[*Any]: Additional arguments to store in the Exception. 
        """
        Exception.__init__(self, message, error, *args)
        self._message: str = self.args[0]
        self._error: Optional[Exception] = self.args[1]

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


class SignalError(Error):
    """
    Exception to throw when signal returns an error code.
    """
    def __init__(self, message: str, code: int, *args) -> None:
        """
        Initialize a SignalError
        :param message: The signal error message.
        :param code: The signal error code.
        :param args: tuple[*Any]: Any additional arguments to the Exception.
        """
        Error.__init__(self, message, None, *args)
        self._code: int = code

    @property
    def code(self) -> int:
        """
        The signal error code.
        :return: int: The error code.
        """
        return self._code


class ParameterError(Error):
    """
    Exception to throw when parameters conflict.
    """
    def __init__(self, message: str, *args) -> None:
        """
        Initialize a ParameterError.
        :param message: str: The error message.
        :param args: tuple[*Any]: Any additional arguments to the Exception.
        """
        Error.__init__(self, message, None, *args)


class InvalidServerResponse(Error):
    """
    signal-cli provided us with invalid JSON.
    """
    def __init__(self, message: str, error: Optional[json.JSONDecodeError], *args) -> None:
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
    def __init__(self, message: str, error: socket.error, *args) -> None:
        """
        Initialize CommunicationsError.
        :param message: str: The error message.
        :param error: socket.error: The socket error that caused the error.
        :param args: tuple[Any]: Any additional arguments to add to the Exception.
        """
        Error.__init__(self, message, error, *args)


class InvalidDataFile(Error):
    """
    Exception to throw when an error occurs while loading a signal-cli data file.
    """
    def __init__(self,
                 message: str,
                 error: json.JSONDecodeError | KeyError,
                 file_path: str, *args
                 ) -> None:
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
    def __init__(self, message: str, version: int, supported_versions: tuple, *args) -> None:
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
    def __init__(self, *args) -> None:
        """
        Initialize LinkInProgress error.
        :param args: tuple[*Any]: Any additional arguments to store in the Exception.
        """
        Error.__init__(self, "Link already in progress.", None, *args)


class LinkNotStarted(Error):
    """
    Exception to throw when the link hasn't been started yet and finish_link is called.
    """
    def __init__(self, *args) -> None:
        """
        Initialize a LinkNotStarted error.
        :param args: tuple[*Any]: Any additional arguments to store in the exception.
        """
        Error.__init__(self, "Link not started.", None, *args)


class CallbackCausedError(Error):
    """
    Exception to throw when a callback causes an error.
    """
    def __init__(self,
                 callback_name: str,
                 params: tuple[Any, ...],
                 error: Exception,
                 *args
                 ) -> None:
        """
        Initialize a CallbackCausedError exception.
        :param callback_name: str: The __name__ of the callback.
        :param error: Exception: The error the callback caused.
        :param args: tuple[Any]: Any additional arguments to store in the exception.
        """
        message: str = (f"Callback: '{callback_name}', caused an exception of "
                        f"type: '{str(type(error))}', with arguments: '{str(error.args)}'.")
        self._callback_name: str = callback_name
        self._params: tuple[Any, ...] = params
        Error.__init__(self, message, error, *args)

    @property
    def callback_name(self) -> str:
        """
        The name of the callback that caused the exception.
        :return: str
        """
        return self._callback_name

    @property
    def params(self) -> tuple[Any, ...]:
        """
        The parameters to the callback that caused the exception.
        :return: tuple[Any]
        """
        return self._params


class SignalAlreadyRunningError(Error):
    """
    Exception to throw when signal is already running.
    """
    def __init__(self, *args) -> None:
        """
        Initialize the Exception.
        """
        message: str = "An instance of signal-cli is already running."
        super().__init__(message, None, *args)
