#!/usr/bin/env python3
"""
File: run_callback.py
    Store everything needed to run a callback.
"""

from typing import Optional, Callable, Any, Final, Iterable
from enum import IntEnum

###############################
# Constants:
###############################
_VERSION: Final[str] = "1.0.2"
"""The runCallback version."""
_TYPE_STRING: Final[str] = "Optional[tuple[Callable, Optional[list[Any] | tuple[Any, ...]]]]"

###############################
# Variables:
###############################
_SUPRESS_ERROR: bool = True
"""Should we supress errors caused by the callback?"""


class CallbackIndex(IntEnum):
    """
    Callback Indexes.
    """
    CALLABLE = 0
    """The callable portion of the index."""
    PARAMS = 1
    """The parameter portion of the index."""


class CallbackError(Exception):
    """
    Exception to throw when a callback error occurs.
    """
    def __init__(
            self, cb_callable: Callable, cb_params: Iterable[Any], cb_error: Exception, *args
    ) -> None:
        """
        :param cb_callable: Callable: The Callable that caused the error.
        :param cb_params: Iterable[Any]: Any parameters that was passed to the callback.
        :param cb_error: Exception: The Exception that was raised.
        :param args: tuple[Any, ...]: Any additional arguments passed.
        """
        self._callable: Callable = cb_callable
        self._params: tuple[Any, ...] = (*cb_params,)
        self._error: Exception = cb_error

        error_message: str = (f"Callback: '{self.callable_name}', called with "
                              f"params: '{self.str_params}' raised exception of"
                              f"type: '{self.str_error_type}' with"
                              f"arguments: '{self.str_error_args}")
        super().__init__(error_message, cb_callable, cb_params, cb_error, *args)

    @property
    def callable(self) -> Callable:
        """
        Get the callable portion of the callback.
        """
        return self._callable

    @property
    def callable_name(self) -> str:
        """
        Get the callable name.
        """
        return self._callable.__name__

    @property
    def params(self) -> tuple[Any, ...]:
        """
        Get the parameter portion of the callback.
        """
        return self._params

    @property
    def str_params(self) -> str:
        """
        Get the string representation of the parameters.
        """
        return str(self._params)

    @property
    def error(self) -> Exception:
        """
        Get the exception raised when the callback error occurs.
        """
        return self._error

    @property
    def error_type(self):
        """
        Get the exception type raised when the callback error occurs.
        """
        return type(self._error)

    @property
    def str_error_type(self) -> str:
        """
        Get the string representation of the exception type raised when the callback error occurs.
        """
        return str(self.error_type)

    @property
    def error_args(self) -> tuple[Any, ...]:
        """
        Get the exception arguments raised when the callback error occurs.
        """
        return self._error.args

    @property
    def str_error_args(self) -> str:
        """
        Get the string representation of the exception arguments raised when the callback error
        occurs.
        """
        return str(self._error.args)


def __type_check_callback__(
        callback: Optional[tuple[Callable, Optional[list[Any] | tuple[Any, ...]]]]
                            ) -> tuple[bool, str]:
    """
    Type-check a callback variable.
    :param callback: Optional[tuple[Callable, Optional[list[Any] | tuple[Any, ...]]]]: The callback
    to check.
    :returns: Tuple[bool, str]: The first element is True or False for if the type-check was passed.
    The second element is either the string 'SUCCESS' or an error message stating what failed the
    test.
    """
    passed: bool = True
    reason: str = ""
    # If callback is None, everything is good.
    if callback is None:
        return True, 'SUCCESS'
    # Check that callback is a tuple of 2 elements.
    if not isinstance(callback, tuple):
        passed = False
        reason = 'callback is not a tuple'
    elif len(callback) != 2:
        passed = False
        reason = 'callback does not have 2 elements'
    # Check the first element is callable:
    elif not callable(callback[CallbackIndex.CALLABLE]):
        passed = False
        reason = 'callback is not callable'
    if not passed:
        return False, reason
    # Check the second element is None, and if so return success:
    if callback[CallbackIndex.PARAMS] is None:
        return True, 'SUCCESS'
    # Check that the second element is Iterable:
    if not isinstance(callback[CallbackIndex.PARAMS], Iterable):
        return False, "callback[1] is not None | Iterable"
    return True, 'SUCCESS'


def __run_callback__(callback: Optional[tuple[Callable, Optional[Iterable[Any]]]],
                     *cb_params
                     ) -> Optional[Any] | CallbackError:
    """
    Run a given callback.
    :param callback: Optional[tuple[Callable, Optional[Iterable[Any]]]]: The callback.
    If None, no callback is called, otherwise, callback should be a tuple with two elements.
    The first element is the Callable,
    the second is an Iterable of user parameters to pass to the callback after the
    primary parameters.
    :param cb_params: tuple[Any, ...]: Any primary parameters to pass to the callback before the
    user parameters.
    :returns: Optional[Any]: If callback is None, None is returned, otherwise the return value of
    the callback is returned.
    """
    # If callback is None, return None:
    if callback is None:
        return None
    # Determine the parameters to pass to the callback:
    params: tuple[Any, ...]
    if callback[CallbackIndex.PARAMS] is None:
        params = (*cb_params, )
    else:
        params = (*cb_params, *callback[CallbackIndex.PARAMS])
    # Try to call the callback:
    try:
        return callback[CallbackIndex.CALLABLE](*params)
    except Exception as e:
        # Callback failed.
        callback_error = CallbackError(callback[CallbackIndex.CALLABLE], params, e)
        if _SUPRESS_ERROR:
            return callback_error
        raise callback_error from e


###############################
# Get and Set vars:
###############################
def version() -> str:
    """
    The version of run_callback.py
    :returns: str: The current version.
    """
    return _VERSION


def type_string() -> str:
    """
    Get the string representation of the type expected.
    """
    return _TYPE_STRING


def get_suppress_error() -> bool:
    """
    Should we suppress any error the callback raises and return it, or should we raise
    CallbackError?
    :returns: bool: The current state.
    """
    return _SUPRESS_ERROR


def set_suppress_error(value: bool) -> None:
    """
    Should we suppress any error the callback raises and return it, or should we raise
    CallbackError?
    Setter.
    :returns: None.
    :raises TypeError: If value is not a bool.
    """
    # pylint: disable=W0603
    global _SUPRESS_ERROR
    if not isinstance(value, bool):
        raise TypeError("'supress_error' value, must be a bool.")
    _SUPRESS_ERROR = value
