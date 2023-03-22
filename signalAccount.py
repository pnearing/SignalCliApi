#!/usr/bin/env python3

from typing import Optional
import os
import json
import sys
import socket

from .signalCommon import __socketReceive__, __socketSend__
from .signalDevice import Device
from .signalDevices import Devices
from .signalContacts import Contacts
from .signalGroups import Groups
from .signalMessages import Messages
from .signalProfile import Profile
from .signalSticker import StickerPacks

global DEBUG
DEBUG: bool = True

class Account(object):
    supportedAccountFileVersion: int = 6
    def __init__(self,
                    syncSocket: socket.socket,
                    commandSocket: socket.socket,
                    configPath: str,
                    stickerPacks: StickerPacks,
                    signalAccountPath: str = None,
                    doLoad: bool = False,
                    number: Optional[str] = None,
                    uuid: Optional[str] = None,
                    deviceId: Optional[int] = None,
                    device: Optional[Device] = None,
                    registered: bool = False,
                    config: Optional[dict] = None,
                    devices: Optional[Devices] = None,
                    contacts: Optional[Contacts] = None,
                    groups: Optional[Groups] = None,
                    profile: Optional[Profile] = None,
                ) -> None:
    #TODO: Argument checks:
    # Set internal Vars:
        self._syncSocket: socket.socket = syncSocket
        self._commandSocket: socket.socket = commandSocket
        self.configPath: str = configPath
        self._stickerPacks: StickerPacks = stickerPacks
        self._accountPath: str = os.path.join(configPath, 'data', signalAccountPath +'.d')
        self._accountFilePath: str = os.path.join(configPath, 'data', signalAccountPath)
    # Set external properties:
        self.number: str = number
        self.uuid: str = uuid
        self.deviceId: int = deviceId
        self.device: Device = device
        self.registered: bool = registered
        self.config: Optional[dict] = config
        self.devices: Optional[Devices] = devices
        self.contacts: Optional[Contacts] = contacts
        self.groups: Optional[Groups] = groups
        self.profile: Optional[Profile] = profile
    # Do load:
        if (doLoad == True):
            self.__doLoad__()
    # If the account is registered load account data from signal:
        if (self.registered == True):
        # Load devices from signal:
            self.devices = Devices(syncSocket=self._syncSocket, accountId=self.number, accountDevice=self.deviceId,
                                    doSync=True)
        # Set this device:
            self.device = self.devices.getAccountDevice()
        # Load contacts from signal:
            self.contacts = Contacts(syncSocket=self._syncSocket, configPath=self.configPath, accountId=self.number,
                                        accountPath=self._accountPath, doLoad=True, doSync=True)
        # Load groups from signal:
            self.groups = Groups(syncSocket=self._syncSocket, configPath=self.configPath, accountId=self.number,
                                    accountContacts=self.contacts, doSync= True)
        # Load messages from file:
            self.messages = Messages(commandSocket=self._commandSocket, configPath=self.configPath,
                                        accountId=self.number, accountPath=self._accountPath, contacts=self.contacts,
                                        groups=self.groups, devices=self.devices, thisDevice=self.devices.getAccountDevice(),
                                        stickerPacks=self._stickerPacks, doLoad=True)
        # Load profile from file and merge self contact.
            self.profile = Profile(syncSocket=self._syncSocket, configPath=self.configPath, accountId=self.number,
                                    contactId = self.number, accountPath=self._accountPath, doLoad=True,
                                    isAccountProfile=True)
            selfContact = self.contacts.getSelf()
            self.profile.__merge__(selfContact.profile)
        else:
        # Set devices to None:
            self.devices = None
        # Set this device to None:
            self.device = None
        # Set contacts to None:
            self.contacts = None
        # Set groups to None
            self.groups = None
        # Set messages to None
            self.messages = None
        # Set profile to None
            self.profile = None
        return

    def __doLoad__(self) -> None:
    # Try to open the file for reading:
        try:
            fileHandle = open(self._accountFilePath, 'r')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open '%s' for reading: %s" % (self._accountFilePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Try to load the json from the file:
        try:
            rawAccount:dict = json.loads(fileHandle.read())
        except json.JSONDecodeError as e:
            errorMessage = "FATAL: Failed to load json from '%s': %s" % (self._accountFilePath, e.msg)
            raise RuntimeError(errorMessage)
    # Version check account file:
        if (rawAccount['version'] > 6):
            errorMessage = "WARNING: Account detail file %s is of a different supported version. This may cause things to break."
            print(errorMessage, file=sys.stderr, flush=True)
    # Set the properties from the account json:
        self.number = rawAccount['username']
        self.uuid = rawAccount['uuid']
        self.deviceId = rawAccount['deviceId']
        self.registered = rawAccount['registered']
        self.config = rawAccount['configurationStore']
        return


##########################
# Methods:
##########################
    def verify(self, code:str, pin:str | None = None) -> tuple[bool, str]:
    # Create verify command object:
        verifyCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "verify",
            "params": {
                "account": self.number,
                "verificationCode": code,
            }
        }
        if (pin != None):
            verifyCommandObj['params']['pin'] = pin
        jsonCommandStr = json.dumps(verifyCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj:dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            errorMessage = "ERROR: Signal error, code: %i, message: %s" % (responseObj['error']['code'], responseObj['error']['message'])
            if (DEBUG == True):
                print(errorMessage, file=sys.stderr)
            return (False, errorMessage)
        print(responseObj)
        
        return (True, "verification successful")