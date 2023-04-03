#!/usr/bin/env python3

from typing import Optional
import socket
import sys

from .signalContact import Contact
from .signalContacts import Contacts
from .signalDevice import Device
from .signalDevices import Devices
from .signalGroup import Group
from .signalGroups import Groups
from .signalMessage import Message
from .signalSticker import StickerPacks
from .signalTimestamp import Timestamp
from .signalCommon import __type_error__

DEBUG: bool = False


# noinspection GrazieInspection
class SyncMessage(Message):
    """Class to store the different type of sync messages."""
    # Sync message types:
    TYPE_CONTACT_SYNC: int = 1
    TYPE_GROUPS_SYNC: int = 2
    TYPE_SENT_MESSAGE_SYNC: int = 3
    TYPE_READ_MESSAGE_SYNC: int = 4
    TYPE_BLOCKED_SYNC: int = 5
    # Sent message, message types:
    SENT_TYPE_SENT_MESSAGE: int = 1
    SENT_TYPE_GROUP_UPDATE_MESSAGE: int = 2

    def __init__(self,
                 command_socket: socket.socket,
                 account_id: str,
                 config_path: str,
                 contacts: Contacts,
                 groups: Groups,
                 devices: Devices,
                 this_device: Device,
                 sticker_packs: StickerPacks,
                 from_dict: Optional[dict] = None,
                 raw_message: Optional[dict] = None,
                 sender: Optional[Contact] = None,
                 recipient: Optional[Contact | Group] = None,
                 device: Optional[Device] = None,
                 timestamp: Optional[Timestamp] = None,
                 is_delivered: bool = False,
                 time_delivered: Optional[Timestamp] = None,
                 is_read: bool = False,
                 time_read: Optional[Timestamp] = None,
                 is_viewed: bool = False,
                 time_viewed: Optional[Timestamp] = None,
                 sync_type: int = Message.TYPE_NOT_SET,
                 ) -> None:
        # Argument checks:
        if not isinstance(sticker_packs, StickerPacks):
            __type_error__("sticker_packs", "StickerPacks", sticker_packs)
        if not isinstance(sync_type, int):
            __type_error__("sync_type", "int", sync_type)
        # Set internal properties:
        # Set sticker packs:
        self._sticker_packs: StickerPacks = sticker_packs
        # Set external properties:
        # Set sync type:
        self.sync_type: int = sync_type
        # Set sent message properties:
        self.raw_sent_message: Optional[dict[str, object]] = None
        # Set read messages list:
        self.read_messages: list[tuple[Contact, Timestamp]] = []
        # Set blocked Contacts and group lists:
        self.blocked_contacts: list[str] = []
        self.blocked_groups: list[str] = []
        # Run super Init:
        super().__init__(command_socket, account_id, config_path, contacts, groups, devices, this_device, from_dict,
                         raw_message, sender, recipient, device, timestamp, Message.TYPE_SYNC_MESSAGE, is_delivered,
                         time_delivered, is_read, time_read, is_viewed, time_viewed)
        # Mark viewed delivered and read:
        super().mark_delivered(self.timestamp)
        super().mark_read(self.timestamp)
        super().mark_viewed(self.timestamp)
        return

    ######################
    # Init:
    ######################
    def __from_raw_message__(self, raw_message: dict) -> None:
        super().__from_raw_message__(raw_message)
        # print("DEBUG: %s" % __name__)
        raw_sync_message: dict[str, object] = raw_message['sync_message']
        ######## Read messages #########
        if 'read_messages' in raw_sync_message.keys():
            # print(rawSyncMessage['read_messages'])
            self.sync_type = self.TYPE_READ_MESSAGE_SYNC
            read_message_list: list[dict[str, object]] = raw_sync_message['read_messages']
            self.read_messages: list[tuple[Contact, Timestamp]] = []
            for read_message_dict in read_message_list:
                added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", read_message_dict['sender'])
                timestamp = Timestamp(timestamp=read_message_dict['timestamp'])
                self.read_messages.append((contact, timestamp))
        ######### Sent message ########
        elif 'sentMessage' in raw_sync_message.keys():
            print(raw_sync_message['sentMessage'])
            self.sync_type = self.TYPE_SENT_MESSAGE_SYNC
            self.raw_sent_message = raw_message
        ########## Blocked Numbers / Groups #############
        elif 'blockedNumbers' in raw_sync_message.keys():
            self.sync_type = self.TYPE_BLOCKED_SYNC
            self.blocked_contacts = []
            for contactId in raw_sync_message['blockedNumbers']:
                self.blocked_contacts.append(contactId)
            self.blocked_groups = []
            for groupId in raw_sync_message['blockedGroupIds']:
                self.blocked_groups.append(groupId)
        elif 'type' in raw_sync_message.keys():
            ########### Group sync #################
            if raw_sync_message['type'] == "GROUPS_SYNC":
                self.sync_type = self.TYPE_GROUPS_SYNC
                # print("Groups sync message")
            ########### Contacts Sync ###############
            elif raw_sync_message['type'] == "CONTACTS_SYNC":
                self.sync_type = self.TYPE_CONTACT_SYNC
                # print("Contacts sync message")
            else:
                if DEBUG:
                    debugMessage = "Unrecognized type: %s OBJ: %s" % (raw_sync_message['type'], str(raw_sync_message))
                    print(debugMessage, file=sys.stderr)
        return

    ###########################
    # To / From Dict:
    ###########################
    def __to_dict__(self) -> dict:
        sync_message_dict = super().__to_dict__()
        # Store sync type:
        sync_message_dict['sync_type'] = self.sync_type
        # Store sent message properties:
        sync_message_dict['raw_sent_message'] = self.raw_sent_message
        # Store the read messages list:
        # Store the list as a list of tuples[contactID:str, timestampDict:dict]
        sync_message_dict['read_messages'] = []
        for (contact, timestamp) in self.read_messages:
            target_message_tuple = (contact.get_id(), timestamp.__to_dict__())
            sync_message_dict['read_messages'].append(target_message_tuple)
        # Store Blocked contacts and groups lists:
        sync_message_dict['blocked_contacts'] = self.blocked_contacts
        sync_message_dict['blocked_groups'] = self.blocked_groups
        return sync_message_dict

    def __from_dict__(self, from_dict: dict) -> None:
        super().__from_dict__(from_dict)
        # Load sync type:
        self.sync_type = from_dict['sync_type']
        # Load sent message properties:
        self.raw_sent_message = from_dict['raw_sent_message']
        # Set read messages list:
        # Load read messages:
        self.read_messages = []
        for (contact_id, timestamp_dict) in from_dict['read_messages']:
            added, contact = self._contacts.__get_or_add__("<UNKNOWN-CONTACT>", contact_id)
            timestamp = Timestamp(from_dict=timestamp_dict)
            self.read_messages.append((contact, timestamp))
        # Set blocked groups and contacts:
        self.blocked_contacts = from_dict['blocked_contacts']
        self.blocked_groups = from_dict['blocked_groups']

        return
