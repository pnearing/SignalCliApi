#!/usr/bin/env python3

from typing import TypeVar, Optional
import datetime
import pytz
from tzlocal import get_localzone
import sys

from signalCommon import __typeError__

Self = TypeVar("Self", bound="Timestamp")

class Timestamp(object):
    def __init__(self,
                    timestamp: Optional[int] = None,
                    fromDict: Optional[dict[str, object]] = None,
                    dateTime: Optional[datetime.datetime] = None,
                    now:bool = False,
                ) -> None:
    # Verify args:
        if (timestamp == None and fromDict == None and now == False and dateTime == None):
            errorMessage = "FATAL: timestamp, fromDict, dateTime must be defined, or now must be True."
            raise RuntimeError(errorMessage)
    # Type check args:
        if (timestamp != None and isinstance(timestamp, int) == False):
            __typeError__("timestamp", "int", timestamp)
        if (fromDict != None and isinstance(fromDict, dict) == False):
            __typeError__("fromDict", "dict[str, object]", fromDict)
        if (dateTime != None and isinstance(dateTime, datetime.datetime) == False):
            __typeError__("dateTime", "datetime.datetime", dateTime)
        if (isinstance(now, bool) == False):
            __typeError__("now", "bool", now)
    # Set vars:
        self.timestamp: int = timestamp # Int
        self.datetime:datetime.datetime = None # Python tz aware datetime object.
    # Load from dict:
        if (self.timestamp != None):
            self.__setDateTime__()
        elif (fromDict != None):
            self.__fromDict__(fromDict=fromDict)
        elif (dateTime != None):
            self.__fromDateTime__(dateTime)
        elif (now == True):
            self.__fromNow__()
        return
##########################
# Init functions:
##########################
    def __toDict__(self) -> dict:
        timestampDict = {
            'timestamp': self.datetime.timestamp()
        }
        return timestampDict
    
    def __fromDict__(self, fromDict:dict) -> None:
        self.datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(fromDict['timestamp']))
        self.timestamp = int(fromDict['timestamp'] * 1000)
        return

    def __fromNow__(self) -> None:
        self.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        seconds = self.datetime.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __fromDateTime__(self, dateTime:datetime.datetime) -> None:
        try:
            self.datetime = pytz.utc.localize(dateTime)
        except ValueError:
            self.datetime = dateTime
        seconds = self.datetime.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __setDateTime__(self) -> None:
        seconds = int(self.timestamp / 1000)
        microseconds = int((((self.timestamp / 1000) - seconds) * 1000) * 1000)
        self.datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(seconds))
        self.datetime = self.datetime.replace(microsecond = microseconds)
        return

##########################################
# Object functions/ methods:
##########################################
    def __int__(self) -> int:
        return self.timestamp

    def __float__(self) -> float:
        return self.datetime.timestamp()

    def __str__(self) -> str:
        return self.datetime.isoformat()
    
    def __eq__(self, __o:Self|object) -> bool:
        if (isinstance(__o, Timestamp) == False):
            return False
        return (self.datetime == __o.datetime)
    
    def __lt__(self, __o:Self) -> bool:
        if (isinstance(__o, Timestamp) == False):
            raise TypeError("FATAL: only Timestamp is supported.")
        return (self.datetime < __o.datetime)
        
    def __gt__(self, __o:Self|int) -> bool:
        if (isinstance(__o, Timestamp) == False):
            raise TypeError("FATAL: Only SignalTimestamp and int are supported.")
        return (self.datetime > __o.datetime)

##########################
# Getters:
##########################

    def getTimestamp(self) -> int:
        return self.timestamp

    def getDateTime(self) -> datetime.datetime:
        return self.datetime

    def getDisplayTime(self, localTime:bool=True) -> str:
        if (localTime == True):
            displayTime = self.getLocalTime()
        else:
            displayTime = self.datetime
        displayTimeStr = "%i<%s>" % (self.timestamp, displayTime.isoformat())
        return displayTimeStr

    def getLocalTime(self) -> datetime.datetime:
        localTz = get_localzone()
        return self.datetime.astimezone(localTz)
########################
# Method:
########################
    def print(self, indent:int=0, indentChar:str=' ', file=sys.stdout) -> None:
    # Arg Checks:
        if (isinstance(indent,int) == False):
            raise TypeError("indent must be of type int.")
        if (isinstance(indentChar, str) == False):
            raise TypeError("indentChar must be of type str.")
        if (len(indentChar) != 1):
            raise ValueError("indentChar must be 1 character long.")
    # Convert to local time:
        localTz = get_localzone()
        localDatetime = self.datetime.astimezone(localTz)
    # Create indent string:
        indentString:str = indentChar * indent
        print(indentString, "--------Begin Timestamp--------", file=file)
        displayLine = "Timestamp: %i(%s)" % (self.timestamp, self.datetime.isoformat())
        print(indentString, displayLine, file=file)
        displayLine = "Local Time: %s" % (localDatetime.isoformat())
        print(indentString, displayLine, file=file)
        print(indentString, "---------End Timestamp---------", file=file)
        return


if __name__ == '__main__':
    timestamp = Timestamp(now=True)
    timestamp.print()