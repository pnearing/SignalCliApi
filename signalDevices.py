#!/usr/bin/env python3

from typing import Optional
import json
import socket

from signalCommon import __socketReceive__, __socketSend__
from signalDevice import Device
from signalTimestamp import Timestamp

class Devices(object):
    def __init__(self,
                    syncSocket: socket.socket,
                    accountId: str,
                    accountDevice: Optional[int] = None,
                    fromDict: Optional[dict] = None,
                    doSync:bool = False,
                ) -> None:
    # TODO: Argument checking:
    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._accountId: str = accountId
        self._accountDevice: int = accountDevice
        self._devices: list[Device] = []
    # Parse from dict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Load devices from signal:
        elif (doSync == True):
            self.__sync__()
        return

###############################
# To / From dict:
###############################
    def __toDict__(self) -> dict:
        devicesDict = {
            'devices': []
        }
        for device in self._devices:
            devicesDict['devices'].append(device.__toDict__())
        return devicesDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        self._devices = []
        for deviceDict in fromDict['devices']:
            device = Device(syncSocket=self._syncSocket, accountId=self._accountId, accountDevice=self._accountDevice,
                                fromDict=deviceDict)
            self._devices.append(device)
        return

##############################
# Sync with signal:
##############################
    def __sync__(self) -> bool:
    # Create list devices command Obj:
        listDevicesCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "listDevices",
        }
        listDevicesCommandObj['params'] = { 'account': self._accountId }
    # Create json command string
        jsonCommand = json.dumps(listDevicesCommandObj) + '\n'
    # Communicate with the socket:  
        __socketSend__(self._syncSocket, jsonCommand)
        responseString = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj:dict = json.loads(responseString)
    # Check for error:
        if ('error' in responseObj.keys()):
            return False
    # Parse devices:
        for rawDevice in responseObj['result']:
            newDevice = Device(syncSocket=self._syncSocket, accountId=self._accountId, accountDevice=self._accountDevice,
                                rawDevice=rawDevice)
        # Check for existing device:
            deviceFound = False
            for device in self._devices:
                if (device.id == newDevice.id):
                    device.__merge__(newDevice)
                    deviceFound = True
        # Add device if not found:
            if (deviceFound == False):
                self._devices.append(newDevice)
        return True

#################################
# Helpers:
#################################
    def __getOrAdd__(self, name:str, id:int) -> tuple[bool, Device]:
        for device in self._devices:
            if (device.id == id):
                return (False, device)
        device = Device(syncSocket=self._syncSocket, accountId=self._accountId, accountDevice=self._accountDevice,
                            id=id, name=name, created=Timestamp(now=True))
        self._devices.append(device)
        return (True, device)

########################
# Getters:
########################
    def getAccountDevice(self) -> Optional[Device]:
        for device in self._devices:
            if (device.isAccountDevice == True):
                return device
        return None