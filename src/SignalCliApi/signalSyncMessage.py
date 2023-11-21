#!/usr/bin/env python3
"""
File: signalSyncMessage.py
Store and handle Sync Messages.
"""
import logging
from typing import Optional, Any
import socket

from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroups import Groups
from .signalMessage import Message
from .signalSticker import StickerPacks
from .signalTimestamp import Timestamp
from .signalCommon import __type_error__, MessageTypes, SyncTypes


# noinspection GrazieInspection
class SyncMessage(Message):
    """
    Class to store the different type of sync messages.
    """
    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 sticker_packs: StickerPacks,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_message: Optional[dict[str, Any]] = None,
                 ) -> None:
        """
        Initialize a SyncMessage object.
        :param command_socket: socket.socket: The socket to run commands on.
        :param account_id: str: This accounts' ID.
        :param config_path: str: The full path to signal-cli directory.
        :param contacts: Contacts: This accounts' Contacts object.
        :param groups: Groups: This accounts' Groups object.
        :param devices: Devices: This accounts' Devices object.
        :param this_device: Device: The device object representing the device we're on.
        :param sticker_packs: StickerPacks: The loaded sticker packs.
        :param from_dict: Optional[dict[str, Any]]: Load properties from a dict provided by __to_dict__().
        :param raw_message: Optional[dict[str, Any]]: Load properties from a dict provided by Signal.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument checks:
        if not isinstance(sticker_packs, StickerPacks):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)

        # Set internal properties:
        # Set sticker packs:
        self._sticker_packs: StickerPacks = sticker_packs
        """The loaded StickerPacks object."""

        # Set external properties:
        # Set sync type:
        self.sync_type: SyncTypes = SyncTypes.NOT_SET
        """The type of sync this message represents."""
        # Set sent message properties:
        # TODO: Why am I doing this?
        self.raw_sent_message: Optional[dict[str, Any]] = None
        """The raw dict of a sent message.???"""
        # Set read messages list:
        self.read_messages: list[tuple[Contact, Timestamp]] = []
        """Read message sync list."""
        # Set blocked Contacts and group lists:
        self.blocked_contacts: list[str] = []
        """Blocked contact sync list."""
        self.blocked_groups: list[str] = []
        """Blocked groups sync list."""
        # Run super Init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, None, None, None, None, MessageTypes.SYNC)
        # Mark viewed delivered and read:
        super().mark_delivered(self.timestamp)
        super().mark_read(self.timestamp)
        super().mark_viewed(self.timestamp)
        return

    ######################
    # Init:
    ######################
    def __from_raw_message__(self, raw_message: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by Signal.
        :param raw_message: dict[str, Any]: The dict to load from.
        :return: None
        :raises NotImplemented: On unrecognized sync type.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_raw_message__.__name__)
        # Run super:
        super().__from_raw_message__(raw_message)
        # Fetch sync message data:
        raw_sync_message: dict[str, Any] = raw_message['sync_message']
        # Parse Data:
        # Read messages:
        if 'read_messages' in raw_sync_message.keys():
            # print(rawSyncMessage['read_messages'])
            self.sync_type = SyncTypes.READ_MESSAGES
            read_message_list: list[dict[str, Any]] = raw_sync_message['read_messages']
            self.read_messages: list[tuple[Contact, Timestamp]] = []
            for read_message_dict in read_message_list:
                _, contact = self._contacts.__get_or_add__(contact_id=read_message_dict['sender'])
                timestamp = Timestamp(timestamp=read_message_dict['timestamp'])
                self.read_messages.append((contact, timestamp))
        # Sent message:
        elif 'sentMessage' in raw_sync_message.keys():
            print(raw_sync_message['sentMessage'])
            self.sync_type = SyncTypes.SENT_MESSAGES
            self.raw_sent_message = raw_message  # TODO: Follow this.
        # Blocked Numbers / Groups:
        elif 'blockedNumbers' in raw_sync_message.keys() or 'blockedGroupsIds' in raw_sync_message.keys():
            self.sync_type = SyncTypes.BLOCKS
            self.blocked_contacts = []
            if 'blockedNumbers' in raw_sync_message.keys():
                for contactId in raw_sync_message['blockedNumbers']:
                    self.blocked_contacts.append(contactId)
            self.blocked_groups = []
            if 'blockedGroupIds' in raw_sync_message.keys():
                for groupId in raw_sync_message['blockedGroupIds']:
                    self.blocked_groups.append(groupId)
        elif 'type' in raw_sync_message.keys():
            # Group sync:
            if raw_sync_message['type'] == "GROUPS_SYNC":
                self.sync_type = SyncTypes.GROUPS
                # TODO: What do I do now?
                logger.debug("...NOT IMPLEMENTED: GROUPS SYNC HERE...")
                logger.debug("str(raw_sync_message) = %s" % str(raw_sync_message))
            # Contacts sync:
            elif raw_sync_message['type'] == "CONTACTS_SYNC":
                self.sync_type = SyncTypes.CONTACTS
                # TODO: What do I do now?
                logger.debug("...NOT IMPLEMENTED: CONTACTS SYNC HERE...")
                logger.debug("str(raw_sync_message) = %s" % str(raw_sync_message))
            else:
                error_message: str = "unhandled sync 'type': '%s'." % raw_sync_message['type']
                logger.critical("Raising NotImplemented(%s)")
                logger.debug("raw_sync_message['type'] = %s" % raw_sync_message['type'])
                logger.debug("str(raw_sync_message) = %s" % str(raw_sync_message))
                raise NotImplemented(error_message)
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict to store this sync message.
        :return: dict[str, Any]: A dict to provide to __from_dict__().
        """
        sync_message_dict = super().__to_dict__()
        # Store sync type:
        sync_message_dict['syncType'] = self.sync_type.value
        # Store sent message properties:
        sync_message_dict['rawSentMessage'] = self.raw_sent_message
        # Store the read messages list:
        # Store the list as a list of tuples[contactID:str, timestampDict:dict]
        sync_message_dict['readMessages'] = []
        for (contact, timestamp) in self.read_messages:
            target_message_tuple = (contact.get_id(), timestamp.__to_dict__())
            sync_message_dict['readMessages'].append(target_message_tuple)
        # Store Blocked contacts and groups lists:
        sync_message_dict['blockedContacts'] = self.blocked_contacts
        sync_message_dict['blockedGroups'] = self.blocked_groups
        return sync_message_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: A dict provided by __to_dict__().
        :return: None
        """
        super().__from_dict__(from_dict)
        # Load sync type:
        self.sync_type = from_dict['syncType']
        # Load sent message properties:
        self.raw_sent_message = from_dict['rawSentMessage']
        # Set read messages list:
        # Load read messages:
        self.read_messages = []
        for (contact_id, timestamp_dict) in from_dict['readMessages']:
            added, contact = self._contacts.__get_or_add__(contact_id=contact_id)
            timestamp = Timestamp(from_dict=timestamp_dict)
            self.read_messages.append((contact, timestamp))
        # Set blocked groups and contacts:
        self.blocked_contacts = from_dict['blockedContacts']
        self.blocked_groups = from_dict['blockedGroups']

        return
