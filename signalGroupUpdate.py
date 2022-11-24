#!/usr/bin/env python3
from typing import Optional
import socket

from signalContact import Contact
from signalContacts import Contacts
from signalDevice import Device
from signalDevices import Devices
from signalGroup import Group
from signalGroups import Groups
from signalMessage import Message
from signalTimestamp import Timestamp

class GroupUpdate(Message):
    def __init__(self,
                    commandSocket: socket.socket,
                    accountId: str,
                    configPath: str,
                    contacts: Contacts,
                    groups: Groups,
                    devices: Devices,
                    thisDevice: Device,
                    fromDict: Optional[dict] = None,
                    rawMessage: Optional[dict] = None,
                    sender: Optional[Contact] = None,
                    recipient: Optional[Contact | Group] = None,
                    device: Optional[Device] = None,
                    timestamp: Optional[Timestamp] = None,
                    isDelivered: bool = False,
                    timeDelivered: Optional[Timestamp] = None,
                    isRead: bool = False,
                    timeRead: Optional[Timestamp] = None,
                    isViewed: bool = False,
                    timeViewed: Optional[Timestamp] = None
                ) -> None:
    # Set external properties:
        self.body: str = ''
    # Run super init:
        super().__init__(commandSocket, accountId, configPath, contacts, groups, devices, thisDevice, fromDict,
                            rawMessage, sender, recipient, device, timestamp, Message.TYPE_GROUP_UPDATE_MESSAGE,
                            isDelivered, timeDelivered, isRead, timeRead, isViewed, timeViewed)
        self.__updateBody__()
        return


    def __updateBody__(self) -> None:
        if (self.sender != None and self.recipient != None):
            self.body = "At %s, %s updated the group %s." % (
                                                            self.timestamp.getDisplayTime(),
                                                            self.sender.getDisplayName(),
                                                            self.recipient.getDisplayName()
                                                        )
        else:
            self.body = "Invalid group update."