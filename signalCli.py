#!/usr/bin/env python3

from typing import Optional, Callable
import threading
import sys
import argparse
import os
import socket
from subprocess import Popen, PIPE, CalledProcessError, check_output, check_call
from time import sleep
import json
import re

from signalAccount import Account
from signalAccounts import Accounts
from signalCommon import __typeError__, findSignal, findQrencode, parseSignalReturnCode, __socketCreate__, __socketConnect__, __socketClose__, __socketReceive__, __socketSend__, phoneNumberRegex
from signalMessage import Message
from signalReceiveThread import ReceiveThread
from signalSticker import StickerPacks
global DEBUG
DEBUG:bool = True



class SignalCli(object):
    def __init__(self,
                    signalConfigPath: Optional[str] = None,
                    signalExecPath: Optional[str] = None,
                    serverAddress: Optional[list[str, int] | tuple[str, int] | str] = None,
                    logFilePath: Optional[str] = None,
                    startSignal: bool = True,
                ) -> None:
# Argument checks:
    # Check signal config path:
        if (signalConfigPath != None):
            if(isinstance(signalConfigPath, str) == False):
                __typeError__("signalConfigPath", "str", signalConfigPath)
            elif (os.path.exists(signalConfigPath) == False and startSignal==False):
                errorMessage = "FATAL: signalConfigPath '%s' doesn't exist." % signalConfigPath
                raise FileNotFoundError(errorMessage)
    # Check signal exec path:
        if (signalExecPath != None):
            if (isinstance(signalExecPath, str) == False):
                __typeError__("signalExecPath", "str", signalExecPath)
            elif (os.path.exists(signalExecPath) == False and startSignal == True):
                errorMessage = "FATAL: signalExecPath '%s' does not exist." % signalExecPath
                raise FileNotFoundError(errorMessage)
    # Check server address:
        if (serverAddress != None):
            if (isinstance(serverAddress, list) == True or isinstance(serverAddress, tuple) == True):
                if (isinstance(serverAddress[0], str) == False):
                    __typeError__("serverAddress[0]", "str", serverAddress[0])
                elif (isinstance(serverAddress[1], int) == False):
                    __typeError__("serverAddress[1]", "int", serverAddress[1])
            elif (isinstance(serverAddress, str) == True):
                if (os.path.exists(serverAddress) == True and startSignal == True):
                    errorMessage = "socket path '%s' already exists. Perhaps signal is already running."
                    raise FileExistsError(errorMessage)
    # Check log file path:
        if (logFilePath != None):
            if (isinstance(logFilePath, str) == False):
                __typeError__("logFilePath", "str", logFilePath)
    # Check start signal:
        if (isinstance(startSignal, bool) == False):
            __typeError__("startSignal", "bool", startSignal)

# Set internal vars:
    # Set config path:
        self.configPath: str
        if (signalConfigPath != None):
            self.configPath = signalConfigPath
        else:
            homePath = os.environ.get('HOME')
            self.configPath = os.path.join(homePath, '.local', 'share', 'signal-cli')
    # Set signal exec path:
        self._signalExecPath:Optional[str]
        if (signalExecPath != None):
            self._signalExecPath = signalExecPath
        elif (startSignal == True):
            self._signalExecPath = findSignal()
        else:
            self._signalExecPath = None
    # Set server address:
        self._serverAddress: tuple[str, int] | str
        if (serverAddress != None):
            self._serverAddress = serverAddress
        else:
            self._serverAddress = os.path.join(self.configPath, 'socket')
    # Check to see if we're starting signal, if the socket exists, throw an error.
        if (isinstance(self._serverAddress, str) == True and startSignal == True):
            if (os.path.exists(self._serverAddress) == True):
                errorMessage = "socket path '%s' already exists. Perhaps signal is already running."
                raise FileExistsError(errorMessage)

    # set var to hold main signal process
        self._process: Optional[Popen] = None
    # Set sync socket:
        self._syncSocket: socket.socket = None
    # Set command socket:
        self._commandSocket: socket.socket = None
    # Set var to hold link process:
        self._linkProcess: Optional[Popen] = None
    # Set qrencode exec path:
        self._qrencodeExecPath:Optional[str] = findQrencode()
# Set external properties and objects:
    # Set accounts:
        self.accounts: Accounts = None
    # Set sticker packs:
        self.stickerPacks: StickerPacks = None

    # Start signal-cli if requested:
        if (startSignal == True):
        # Build signal-cli command line:
            signalCommandLine = [self._signalExecPath]
            if (logFilePath != None):
                signalCommandLine.extend(['--verbose', '--log-file', logFilePath])
            signalCommandLine.extend(['--config', self.configPath, 'daemon'])
            if (isinstance(self._serverAddress, str) == True):
                signalCommandLine.extend(['--socket', self._serverAddress])
            else:
                address = "%s:%i" % (self._serverAddress[0], self._serverAddress[1])
                signalCommandLine.extend(['--tcp', address])
            signalCommandLine.extend(['--no-receive-stdout', '--receive-mode', 'manual'])
        # Run signal-cli in daemon mode:
            try:
                if (DEBUG == True):
                    self._process = Popen(signalCommandLine, text=True, stdout=PIPE)
                else:
                    self._process = Popen(signalCommandLine, text=True, stdout=PIPE, stderr=PIPE)
            except CalledProcessError as e:
                parseSignalReturnCode(e.returncode, signalCommandLine, e.output)
    # Give signal 5 seconds to start
        sleep(5)
    # Wait for socket to appear:
        if (isinstance(self._serverAddress, str) == True):
            if (startSignal == True):
                while (os.path.exists(self._serverAddress) != True):
                    if (DEBUG == True):
                        print("Waiting for socket to appear at: %s" % self._serverAddress)
                        sleep(0.5)
                sleep(1)
            else:
                if (os.path.exists(self._serverAddress) == False):
                    errorMessage = "Failed to to locate socket at '%s'" % self._serverAddress
                    raise RuntimeError(errorMessage)
    # Create sockets and connect to them:
        self._syncSocket = __socketCreate__(self._serverAddress)
        __socketConnect__(self._syncSocket, self._serverAddress)
        self._commandSocket = __socketCreate__(self._serverAddress)
        __socketConnect__(self._commandSocket, self._serverAddress)
    # Load stickers:
        self.stickerPacks = StickerPacks(configPath=self.configPath)
    # Load accounts:
        self.accounts = Accounts(syncSocket=self._syncSocket, commandSocket=self._commandSocket,
                                    configPath=self.configPath, stickerPacks=self.stickerPacks, doLoad=True)
    # Create dict to hold processes:
        self._recieveThreads:dict[str, ReceiveThread] = {}
        return
#################################
# Overrides:
#################################
    def __del__(self):
        try:
            if (self._process != None):
                if (isinstance(self._serverAddress, str) == True):
                        os.remove(self._serverAddress)
        except:
            pass
        return


#################################
# Methods:
#################################
    def stopSignal(self):
        try:
            __socketClose__(self._syncSocket)
            __socketClose__(self._commandSocket)
        except:
            pass
        try:
            self._process.terminate()
            self._linkProcess.terminate()
        except Exception:
            pass
        try:
            if (isinstance(self._serverAddress, str) == True):
                os.remove(self._serverAddress)
        except Exception:
            pass
        return

    def registerAccount(self, number:str, captcha:str, voice:bool=False) -> tuple[bool, Account|str]:
    # Check arguments:
        numberMatch = phoneNumberRegex.match(number)
        if (numberMatch == None):
            return (False, "number must be in format +nnnnnnnn....")
        if (captcha[:16] == 'signalcaptcha://'):
            captcha = captcha[16:]
        if (captcha[:17] != 'signal-recaptcha-'):
            return (False, "invalid captcha")
    # Check if account exists, and isn't registered.
        account = self.accounts.getByNumber(number)
        if (account != None):
            if (account.registered == True):
                return (False, "Account already registered.")
    # Create register account command object and json command string:
        registerAccountCommandObj = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "register",
            "params": {
                "account": number,
                "captcha": captcha,
                "voice": voice,
            }
        }
        jsonCommandStr = json.dumps(registerAccountCommandObj) + '\n'
    # Communicate with signal:
        __socketSend__(self._syncSocket, jsonCommandStr)
        responseStr = __socketReceive__(self._syncSocket)
    # Parse response:
        responseObj:dict = json.loads(responseStr)
    # Check for error:
        if ('error' in responseObj.keys()):
            errorMessage = "ERROR: signal error, code: %i, message: %s" % (responseObj['error']['code'], responseObj['error']['message'])
        # Delete local account data, since signal-cli creates data for the account.
            deleteLocalDataCommandObj = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "deleteLocalAccountData",
                "params": {
                    "account": number
                }
            }
            jsonCommandStr = json.dumps(deleteLocalDataCommandObj) + '\n'
        # Communicate with signal:  
            __socketSend__(self._syncSocket, jsonCommandStr)
            responseStr = __socketReceive__(self._syncSocket)
            # print(responseStr)
            return (False, errorMessage)
    # No error found, get the new account:
        newAccount = self.accounts.__sync__()
        if (newAccount == None):
            newAccount = self.accounts.getByNumber(number)
        return (True, newAccount)

    def startLinkAccount(self, name:Optional[str]=None) -> tuple[str, str, str]:
    # Check for running process:
        if (self._linkProcess != None):
            raise RuntimeError("link already in process.")
    # create signal link command line:
        linkCommandLine = [ self._signalExecPath, '--config', self.configPath, 'link']
        if (name != None):
            linkCommandLine.extend( ('--name', name))
    # Run signal link process:
        try:
            self._linkProcess = Popen(linkCommandLine, text=True, stdout=PIPE, stderr=PIPE)
        except CalledProcessError as e:
            parseSignalReturnCode(e.returncode, linkCommandLine, e.output)
            # :NO RETURN :
    # Gather link from stdout
        signalLink = self._linkProcess.stdout.readline()
        signalLink = signalLink.rstrip()
    # Generate text qrcode:
        try:
            textQrCode = check_output([self._qrencodeExecPath, '-o', '-', '--type=UTF8', signalLink]).decode('UTF8')
        except CalledProcessError:
            textQrCode = ''
    # Generate png qrcode:
        pngQrCodeFileName = "link-qrcode.png"
        pngQrCodePath: str = os.path.join(self.configPath, pngQrCodeFileName)
        try:
            check_call([self._qrencodeExecPath, '-o', pngQrCodePath, signalLink])
        except CalledProcessError:
            pngQrCodePath = ''
        return (signalLink, textQrCode, pngQrCodePath)

    def finshLink(self) -> tuple[bool, str]:
    # Check for process:
        if (self._linkProcess == None):
            errorMessage = "link not started"
            return (False, errorMessage)
    # Wait for process:
        returncode = self._linkProcess.wait()
    # Parse returncode:
        if (returncode == 0):
            newAccount = self.accounts.__sync__()
            responseLine = self._linkProcess.stdout.readline()
            print(responseLine)
            if (newAccount == None):
                regex = r'^Associated with: (?P<number>.*)$'
                match = re.match(regex, responseLine)
                newAccount = self.accounts.getByNumber(match['number'])
            return (True, newAccount)
        elif (returncode == 1):
            responseString = self._linkProcess.stderr.read()
            regex = r'The user (?P<number>\+\d+) already exists'
            match = re.match(regex, responseString)
            if (match != None):
                errorMessage = "Account '%s' already exists." % match["number"]
                return(False, errorMessage)
        elif (returncode == 3):
            responseString = self._linkProcess.stderr.read()
            regex = r'Link request error: Connection closed!'
            match = re.match(regex, responseString)
            if (match != None):
                errorMessage = "Link request timeout."
                return(False, errorMessage)
        responseString = self._linkProcess.stderr.read()
        return (False, responseString)

    def startRecieve(self,
                        account:Account,
                        allMessagesCallback: Optional[Callable] = None,
                        receivedMessageCallback: Optional[Callable] = None,
                        receiptMessageCallback: Optional[Callable] = None,
                        syncMessageCallback: Optional[Callable] = None,
                        typingMessageCallback: Optional[Callable] = None,
                        storyMessageCallback: Optional[Callable] = None,
                        paymentMessageCallback: Optional[Callable] = None,
                        reactionMessageCallback: Optional[Callable] = None,
                        callMessageCallback: Optional[Callable] = None,
                    ) -> None:
        threadId = account.number
        thread = ReceiveThread(serverAddress=self._serverAddress,
                                commandSocket=self._commandSocket,
                                configPath=self.configPath,
                                account=account,
                                stickerPacks=self.stickerPacks,
                                allMessagesCallback=allMessagesCallback,
                                receivedMessageCallback=receivedMessageCallback,
                                receiptMessageCallback=receiptMessageCallback,
                                syncMessageCallback=syncMessageCallback,
                                typingMessageCallback=typingMessageCallback,
                                storyMessageCallback=storyMessageCallback,
                                paymentMessageCallback=paymentMessageCallback,
                                reactionMessageCallback=reactionMessageCallback,
                                callMessageCallback=callMessageCallback,
                            )
        thread.start()
        self._recieveThreads[threadId] = thread
        return


    def stopReceive(self, account:Account):
        threadId = account.number
        thread = self._recieveThreads[threadId]
        self._recieveThreads[threadId] = None
        thread.stop()
        return


