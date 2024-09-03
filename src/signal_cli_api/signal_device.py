#!/usr/bin/env python3
"""
File: signal_device.py
Store and handle a single device.
"""
# pylint: disable=R0902, R0912, R0913, R0915
import logging
from typing import TypeVar, Optional, Any
import socket

from .signal_timestamp import SignalTimestamp
from .signal_common import __type_error__, PRIMARY_DEVICE_ID
Self = TypeVar("Self", bound="SignalDevice")


class SignalDevice:
    """
    Class to store a device.
    """
    def __init__(self,
                 sync_socket: socket.socket,
                 account_id: str,
                 this_device: Optional[int] = None,
                 raw_device: Optional[dict[str, Any]] = None,
                 from_dict: Optional[dict[str, Any]] = None,
                 device_id: Optional[int] = None,
                 name: Optional[str] = None,
                 created: Optional[SignalTimestamp] = None,
                 last_seen: Optional[SignalTimestamp] = None,
                 ) -> None:
        """
        Initialize a device:
        :param sync_socket: socket.socket: The socket to use for sync operations.
        :param account_id: str: This account ID.
        :param this_device: Optional[int]: The device ID of the device we're on.
        :param raw_device: Optional[dict[str, Any]]: Load this device from a raw device dict
            from signal.
        :param from_dict: Optional[dict[str, Any]]: Load this device from a dict created
            by __to_dict__().
        :param device_id: Optional[int]: The device ID of this device.
        :param name: Optional[str]: The name of this device.
        :param created: Optional[SignalTimestamp]: When this device was created.
        :param last_seen: Optional[SignalTimestamp]: When this device was last seen.
        :raises RuntimeError: On invalid final device configuration.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Argument checks
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if this_device is not None and not isinstance(this_device, int):
            logger.critical("Raising TypeError:")
            __type_error__("this_device", "Optional[int]", this_device)
        if raw_device is not None and not isinstance(raw_device, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_device", "Optional[dict]", raw_device)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "Optional[dict]", from_dict)
        if device_id is not None and not isinstance(device_id, int):
            logger.critical("Raising TypeError:")
            __type_error__("device_id", "Optional[int]", device_id)
        if name is not None and not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "Optional[str]", name)
        if created is not None and not isinstance(created, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("created", "Optional[SignalTimestamp]", created)
        if last_seen is not None and not isinstance(last_seen, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("last_seen", "Optional[SignalTimestamp]", last_seen)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to preform sync operations on."""
        self._account_id: str = account_id
        """This account ID."""

        # Set external properties:
        self.id: int = device_id
        """The device ID."""
        self.name: Optional[str] = name
        """The name of the device."""
        self.created: Optional[SignalTimestamp] = created
        """The SignalTimestamp of when this device was created."""
        self.last_seen: Optional[SignalTimestamp] = last_seen
        """The SignalTimestamp of when this device was last seen."""
        self.is_this_device: Optional[bool] = None
        """Is this device the device we're using?"""
        self.is_primary_device: Optional[bool] = None

        # Parse Raw device:
        if raw_device is not None:
            logger.debug("Loading from raw device.")
            self.__from_raw_device__(raw_device)
            if self.id == this_device:
                self.is_this_device = True
            if self.id == PRIMARY_DEVICE_ID:
                self.is_primary_device = True
        # Parse from dict:
        elif from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Otherwise, assume all values have been specified, and check that the ID at
        # least is defined:
        else:
            if self.id is None:
                error_message: str = "Invalid device configuration, no device ID."
                logger.critical("Raising RuntimeError(%s).", error_message)
                raise RuntimeError(error_message)
            # Set properties:
            if this_device is not None and self.id == this_device:
                self.is_this_device = True
            if self.id == PRIMARY_DEVICE_ID:
                self.is_primary_device = True

    def __from_raw_device__(self, raw_device: dict[str, Any]) -> None:
        """
        Load properties from raw device dict from signal.
        :param raw_device: dict[str, Any]: The dict provided by signal.
        :return: None
        """
        self.id = raw_device['id']
        self.name = raw_device['name']
        if raw_device['createdTimestamp'] is not None:
            self.created = SignalTimestamp(timestamp=raw_device['createdTimestamp'])
        else:
            self.created = None
        if raw_device['lastSeenTimestamp'] is not None:
            self.last_seen = SignalTimestamp(timestamp=raw_device['lastSeenTimestamp'])
        else:
            self.last_seen = None

    def __merge__(self, other: Self) -> None:
        """
        Merge two devices, assuming the passed in device is the most up to date.
        :param other: SignalDevice: The other device to merge with.
        :return: None
        """
        if self.name is None:
            self.name = other.name
        if self.created != other.created:
            self.created = other.created
        if self.last_seen is not None and other.last_seen is not None:
            if self.last_seen < other.last_seen:
                self.last_seen = other.last_seen
            elif self.last_seen is None and other.last_seen is not None:
                self.last_seen = other.last_seen

    ##########################
    # To / From dict:
    ##########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a json friendly dict to pass to __from_dict__()
        :return: dict[str, Any]: The json friendly dict.
        """
        device_dict: dict[str, Any] = {
            'id': self.id,
            'name': self.name,
            'created': None,
            'lastSeen': None,
            'isAccountDevice': self.is_this_device,
            'isPrimaryDevice': self.is_primary_device,
        }
        if self.created is not None:
            device_dict['created'] = self.created.__to_dict__()
        if self.last_seen is not None:
            device_dict['lastSeen'] = self.last_seen.__to_dict__()
        return device_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a dict created by __to_dict__().
        :param from_dict: dict[str, Any]: The dict to load from.
        :return: None
        """
        self.id = from_dict['id']
        self.name = from_dict['name']
        if from_dict['created'] is not None:
            self.created = SignalTimestamp(from_dict=from_dict['created'])
        else:
            self.created = None
        if from_dict['lastSeen'] is not None:
            self.last_seen = SignalTimestamp(from_dict=from_dict['lastSeen'])
        else:
            self.last_seen = None
        self.is_this_device = from_dict['isAccountDevice']
        self.is_primary_device = from_dict['isPrimaryDevice']

    #########################
    # Overrides:
    #########################
    def __eq__(self, other: Self) -> bool:
        """
        Compare equality against another device.
        :param other: SignalDevice: The device to compare to.
        :return: bool: True if the devices are equal, False if not.
        """
        if isinstance(other, SignalDevice):
            return self.id == other.id
        return False

    def __str__(self) -> str:
        """
        Return a string representation of this device.
        :return: str: The string representation of this device.
        """
        return self.get_display_name()

    ########################
    # Methods:
    ########################
    def __seen__(self, time_seen: SignalTimestamp) -> None:
        """
        Update the last time this device has been seen.
        :param time_seen: SignalTimestamp: The time this device was seen at.
        :raises TypeError: If time_seen not a SignalTimestamp.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__seen__.__name__)
        if not isinstance(time_seen, SignalTimestamp):
            logger.critical("Raising TypeError:")
            __type_error__("time_seen", "SignalTimestamp", time_seen)
        if self.last_seen is not None:
            self.last_seen = max(self.last_seen, time_seen)
        else:
            self.last_seen = time_seen

    def get_display_name(self) -> str:
        """
        Return a pretty name to display.
        """
        return f"{self.name}<{self.id}>"
