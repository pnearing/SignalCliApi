#!/usr/bin/env python3
"""
File: signal_errors.py
Store enums and other error stuff.
"""
# pylint: disable=W0511
from enum import Enum


class LinkError(Enum):
    """
    Enum to store Link process errors.
    """
    USER_EXISTS = 'user already exists'  # Code -1
    UNKNOWN = 'an unknown error occurred'  # Code -2  # TODO: Try and find out what this is.
    TIMEOUT = 'timeout during link process'  # Code -3
