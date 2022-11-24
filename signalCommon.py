#!/usr/bin/env python3

from subprocess import check_output, CalledProcessError
from typing import Pattern, NoReturn, Optional, Any
import socket
import select
import re

########################################
# Regex:
########################################
phoneNumberRegex:Pattern = re.compile(r'(?P<number>\+\d+)')
uuidRegex:Pattern = re.compile(r'(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-f0-9]{12})')

#########################
# Strings:
#########################
UUID_FORMAT_STR = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
NUMBER_FORMAT_STR = "+nnnnnnn..."



####################################
# xdg-open helper:
####################################
def findXdgOpen() -> Optional[str]:
    '''Use which to find xdg-open'''
    xdgopenPath: Optional[str]
    try:
        xdgopenPath = check_output(['which', 'xdg-open'])
        xdgopenPath = xdgopenPath.rstrip()
    except CalledProcessError:
        xdgopenPath = None
    return xdgopenPath

####################################
# qrencode helper:
####################################
def findQrencode() -> Optional[str]:
    '''Use which to fild qrencode.'''
    qrencodePath:Optional[str]
    try:
        qrencodePath = check_output(['which', 'qrencode'])
        qrencodePath = qrencodePath.rstrip()
    except CalledProcessError:
        qrencodePath = None
    return qrencodePath

####################################
# Signal cli helpers:
####################################
def findSignal() -> str | NoReturn:
    '''Find signal-cli in it's many forms. Returns str, exeption FileNotFound if signal not found.'''
    signalPath = None
    try:
        signalPath = check_output(['which', 'signal-cli'], text=True)
        signalPath = signalPath.strip()
    except CalledProcessError as e:
        signalPath = None
# Check for 'signal-cli-native':
    if (signalPath == None):
        try:
            signalPath = check_output(['which', 'signal-cli-native'], text=True)
            signalPath = signalPath.strip()
        except CalledProcessError as e:
            signalPath = None
# Check for 'signal-cli-jre':
    if (signalPath == None):
        try:
            signalPath = check_output(['which', 'signal-cli-jre'], text=True)
            signalPath = signalPath.strip()
        except CalledProcessError as e:
            signalPath = None
# Exit if we couldn't find signal
    if (signalPath == None):
        errorMessage = "FATAL: Could not find [ signal-cli | signal-cli-native | signal-cli-jre ]. Please ensure it's installed and in you $PATH enviroment variable."
        raise FileNotFoundError(errorMessage)
    return signalPath

def parseSignalReturnCode(returncode:int, commandLine:str | list[str], output:str) -> NoReturn:
        if (returncode == 1):
            errorMessage = "Exit code 1: Invalid command line: %s" % str(commandLine)
            raise RuntimeError(errorMessage)
        elif (returncode == 2):
            errorMessage = "Exit Code 2: Unexpected error. %s" % output
            raise RuntimeError(errorMessage)
        elif (returncode == 3):
            errorMessage = "FATAL: Server / Network error. Try again later: %s" % (output)
            raise RuntimeError(errorMessage)
        elif (returncode == 4):
            errorMessage = "FATAL: Operation failed due to untrusted key: %s" % (output)
            raise RuntimeError(errorMessage)
        else:
            errorMessage = "FATAL: Unknown / unhandled error. Running '%s' returned exit code: %i : %s" % (str(commandLine),
                                                                                                        returncode, output)
            raise RuntimeError(errorMessage)

####################################
# Socket helpers:
####################################

def __socketCreate__(serverAddress:tuple[str,int]|str) -> socket.socket:
    '''Create a socket.socket object based on server address type.'''
    if (isinstance(serverAddress, tuple) == True):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif (isinstance(serverAddress, str) == True):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    else:
        errorMessage = "serverAddress must be of type tuple(str,int) or str"
        raise TypeError(errorMessage)
    return sock

def __socketConnect__(sock:socket.socket, serverAddress:tuple[str,int]|str) -> None:
    '''Connect a socket to a server address.'''
    try:
        sock.connect(serverAddress)
    except socket.error as e:
        errorMessage = "FATAL: Couldn't connect to socket: %s" % (str(e.args))
        raise RuntimeError(errorMessage)
    return
    
def __socketSend__(sock:socket.socket, message:str) -> int:
    '''Send a message to the socket.'''
    try:
        bytesSent = sock.send(message.encode())
    except socket.error as e:
        errorMessage = "FATAL: Couldn't send to socket: %s" % (str(e.args))
        raise RuntimeError(errorMessage)
    return bytesSent

def __socketReceive__(sock:socket.socket) -> str:
    '''Read a string from a socket. Blocks until msg read.'''
    try:
        while (True):
            readable, writeable, errored = select.select([sock],[],[], 0.5)
            if (len(readable) > 0):
                message = b''
                while (True):
                    data = sock.recv(1)
                    message = message + data
                    try:
                        if data.decode() == '\n':
                            break
                    except Exception as e:
                        pass
                return message.decode()
    except socket.error as e:
        errorMessage = "FATAL: Failed to read from socket: %s" % (str(e.args))
        raise RuntimeError(errorMessage)
    return None

def __socketClose__(sock:socket.socket) -> None:
    '''Close a socket.'''
    try:
        sock.close()
    except socket.error as e:
        errorMessage = "FATAL: Couldn't close socket connection: %s" % (str(e.args))
        raise RuntimeError(errorMessage)
    return None

################################
# Type checking helper:
###############################
def __typeError__(varName:str, validTypeName:str, var:Any) -> NoReturn:
    errorMessage = "%s must be of type %s, not: %s" % (varName, validTypeName, str(type(var)))
    raise TypeError(errorMessage)