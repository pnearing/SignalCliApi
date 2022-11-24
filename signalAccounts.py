#!/usr/bin/env python3

from typing import Optional, Iterator
import os
import json
import socket

from signalCommon import phoneNumberRegex, uuidRegex
from signalAccount import Account
from signalSticker import StickerPacks

global DEBUG
DEBUG = True

global ACCOUNTS
ACCOUNTS:list[Account] = []

class Accounts(object):
    supportedAccountsVersion:int = 2
    def __init__(self,
                    syncSocket: socket.socket,
                    commandSocket: socket.socket,
                    configPath: str,
                    stickerPacks: StickerPacks,
                    doLoad:bool = False,
                ) -> None:
    # TODO: Argument checks:
    # Set internal vars:
        self._syncSocket: socket.socket = syncSocket
        self._commandSocket: socket.socket = commandSocket
        self._configPath: str = configPath
        self._stickerPacks: StickerPacks = stickerPacks
        self._accountsFilePath: str =  os.path.join(configPath, 'data', 'accounts.json')
        if (doLoad == True):
            self.__doLoad__()
        return

    def __loadAccountsFile__(self) -> dict:
    # Try to open the accounts file:
        try:
            fileHandle = open(self._accountsFilePath, 'r')
        except Exception as e:
            errorMessage = "FATAL: Failed to open '%s' for reading: %s" %(self._accountsFilePath, str(e.args))
            raise RuntimeError(errorMessage)
    # Try to load the json from the file:
        try:
            responseObj:dict = json.loads(fileHandle.read())
        except json.JSONDecodeError as e:
            errorMessage = "FATAL: Failed to load json from file '%s': %s" % (self._accountsFilePath, e.msg)
            raise RuntimeError(errorMessage)
        fileHandle.close()
    # Version check accounts file:
        if (responseObj['version'] != self.supportedAccountsVersion):
            errorMessage = "FATAL: Version %i is not supported. Currently only version %i is supported." % (responseObj['version'], self.supportedAccountsVersion)
            raise RuntimeError(errorMessage)
        return responseObj

    def __doLoad__(self) -> None:
    # Load acccounts file:
        accountsDict = self.__loadAccountsFile__()
    # Parse the file and create the accounts:
        global ACCOUNTS
        ACCOUNTS = []
        count = 0
        for rawAccount in accountsDict['accounts']:
            count = count + 1
            account = Account(syncSocket=self._syncSocket, commandSocket=self._commandSocket, configPath=self._configPath,
                                stickerPacks=self._stickerPacks, signalAccountPath=rawAccount['path'], doLoad=True)
            ACCOUNTS.append(account)
        return
    
    def __sync__(self) -> list[Account]:
        global ACCOUNTS
        newAccount = None
    # Load accounts file:
        accountsDict: dict = self.__loadAccountsFile__()
    # Parse the accounts file looking for a new account.
        for rawAccount in accountsDict['accounts']:
            accountFound = False
            for account in ACCOUNTS:
                if (account.number == rawAccount['number']):
                    accountFound = True
            if (accountFound == False):
                newAccount = Account(syncSocket=self._syncSocket, commandSocket=self._commandSocket,
                                        configPath=self._configPath, stickerPacks=self._stickerPacks,
                                        signalAccountPath=rawAccount['path'], doLoad=True)
                ACCOUNTS.append(newAccount)
                # newAccounts.append(newAccount)
        return newAccount
##############################
# Overrides:
##############################
    def __iter__(self) -> Iterator:
        global ACCOUNTS
        return iter(ACCOUNTS)
##############################
# Getters:
##############################
    def getUnregistered(self) -> list[Account]:
        global ACCOUNTS
        return [acct for acct in ACCOUNTS if acct.registered == False]
    
    def getByNumber(self, number:str) -> Optional[Account]:
        global ACCOUNTS
        numberMatch = phoneNumberRegex.match(number)
        if (numberMatch == None):
            errorMessage = "number must be in format: +nnnnnnnn..."
            raise ValueError(errorMessage)
        for account in ACCOUNTS:
            if (account.number == number):
                return account
        return None