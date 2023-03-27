#!/usr/bin/env python3

from typing import TypeVar, Optional
import socket

from .signalTimestamp import Timestamp

Self = TypeVar("Self", bound="Device")


class Device(object):
    """Class to store a device."""
    def __init__(self,
                 sync_socket: socket.socket,
                 account_id: str,
                 account_device: Optional[int] = None,
                 raw_device: Optional[dict] = None,
                 from_dict: Optional[dict] = None,
                 device_id: Optional[int] = None,
                 name: Optional[str] = None,
                 created: Optional[Timestamp] = None,
                 last_seen: Optional[Timestamp] = None,
                 is_account_device: Optional[bool] = None,
                 is_primary_device: Optional[bool] = None,
                 ) -> None:
        # TODO: Argument checks
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._account_id: str = account_id
        # Set external properties:
        self.id: int = device_id
        self.name: Optional[str] = name
        self.created: Optional[Timestamp] = created
        self.last_seen: Optional[Timestamp] = last_seen
        self.is_account_device: Optional[bool] = is_account_device
        self.is_primary_device: Optional[bool] = is_primary_device
        # Parse Raw device:
        if raw_device is not None:
            self.__fromRawDevice__(raw_device)
            if self.id == account_device:
                self.is_account_device = True
            if self.id == 1:
                self.is_primary_device = True
        # Parse from dict:
        elif from_dict is not None:
            self.__from_dict__(from_dict)
        # Otherwise assume all values have been specified.
        else:
            if self.id is not None and account_device is not None and self.id == account_device:
                self.is_account_device = True
            if self.id is not None and self.id == 1:
                self.is_primary_device = True
        return

    def __fromRawDevice__(self, raw_device: dict) -> None:
        print(raw_device)
        exit(255)
        self.id = raw_device['id']
        self.name = raw_device['name']
        if raw_device['createdTimestamp'] is not None:
            self.created = Timestamp(timestamp=raw_device['createdTimestamp'])
        else:
            self.created = None
        if raw_device['lastSeenTimestamp'] is not None:
            self.last_seen = Timestamp(timestamp=raw_device['lastSeenTimestamp'])
        else:
            self.last_seen = None
        return

    def __merge__(self, __o: Self) -> None:
        if self.name is None:
            self.name = __o.name
        if self.created != __o.created:
            self.created = __o.created
        if self.last_seen is not None and __o.last_seen is not None:
            if self.last_seen < __o.last_seen:
                self.last_seen = __o.last_seen
            elif self.last_seen is None and __o.last_seen is not None:
                self.last_seen = __o.last_seen
        return

    ##########################
    # To / From dict:
    ##########################
    def __to_dict__(self) -> dict:
        device_dict = {
            'id': self.id,
            'name': self.name,
            'created': None,
            'lastSeen': None,
            'isAccountDevice': self.is_account_device,
            'isPrimaryDevice': self.is_primary_device,
        }
        if self.created is not None:
            device_dict['created'] = self.created.__to_dict__()
        if self.last_seen is not None:
            device_dict['lastSeen'] = self.last_seen.__to_dict__()
        return device_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self.id = from_dict['id']
        self.name = from_dict['name']
        if from_dict['created'] is not None:
            self.created = Timestamp(from_dict=from_dict['created'])
        else:
            self.created = None
        if from_dict['lastSeen'] is not None:
            self.last_seen = Timestamp(from_dict=from_dict['lastSeen'])
        else:
            self.last_seen = None
        self.is_account_device = from_dict['isAccountDevice']
        self.is_primary_device = from_dict['isPrimaryDevice']
        return

    ########################
    # Methods:
    ########################
    def seen(self, time_seen: Timestamp) -> None:
        if self.last_seen is not None:
            if self.last_seen < time_seen:
                self.last_seen = time_seen
        else:
            self.last_seen = time_seen
        return

    def get_display_name(self) -> str:
        return "%i<%s>" % (self.id, self.name)
