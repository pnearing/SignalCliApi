#!/usr/bin/env python3

from typing import TypeVar, Optional
import datetime
import pytz

try:
    from tzlocal import get_localzone
except ModuleNotFoundError:
    print("Module: tzlocal not found, you can install using 'sudo apt install python3-tzlocal', or by using")
    print("pip install tzlocal")
import sys

from .signalCommon import __type_error__

Self = TypeVar("Self", bound="Timestamp")


class Timestamp(object):
    def __init__(self,
                 timestamp: Optional[int] = None,
                 fromDict: Optional[dict[str, object]] = None,
                 dateTime: Optional[datetime.datetime] = None,
                 now: bool = False,
                 ) -> None:
        # Verify args:
        if timestamp is None and fromDict is None and now is False and dateTime is None:
            error_message = "FATAL: timestamp, from_dict, date_time must be defined, or now must be True."
            raise RuntimeError(error_message)
        # Type check args:
        if timestamp is not None and isinstance(timestamp, int) is False:
            __type_error__("timestamp", "int", timestamp)
        if fromDict != None and isinstance(fromDict, dict) is False:
            __type_error__("from_dict", "dict[str, object]", fromDict)
        if dateTime != None and isinstance(dateTime, datetime.datetime) is False:
            __type_error__("date_time", "datetime.datetime", dateTime)
        if isinstance(now, bool) is False:
            __type_error__("now", "bool", now)
        # Set vars:
        self.timestamp: int = timestamp  # Int
        self.datetime: Optional[datetime.datetime] = None  # Python tz aware datetime object.
        # Load from dict:
        if self.timestamp is not None:
            self.__setDateTime__()
        elif fromDict is not None:
            self.__fromDict__(from_dict=fromDict)
        elif dateTime is not None:
            self.__fromDateTime__(dateTime)
        elif now:
            self.__fromNow__()
        return

    ##########################
    # Init functions:
    ##########################
    def __toDict__(self) -> dict:
        timestamp_dict = {
            'timestamp': self.datetime.timestamp()
        }
        return timestamp_dict

    def __fromDict__(self, from_dict: dict) -> None:
        self.datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(from_dict['timestamp']))
        self.timestamp = int(from_dict['timestamp'] * 1000)
        return

    def __fromNow__(self) -> None:
        self.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        seconds = self.datetime.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __fromDateTime__(self, date_time: datetime.datetime) -> None:
        try:
            self.datetime = pytz.utc.localize(date_time)
        except ValueError:
            self.datetime = date_time
        seconds = self.datetime.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __setDateTime__(self) -> None:
        seconds = int(self.timestamp / 1000)
        microseconds = int((((self.timestamp / 1000) - seconds) * 1000) * 1000)
        self.datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(seconds))
        self.datetime = self.datetime.replace(microsecond=microseconds)
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

    def __eq__(self, __o: Self) -> bool:
        if isinstance(__o, Timestamp) == False:
            return False
        return self.datetime == __o.datetime

    def __lt__(self, __o: Self) -> bool:
        if isinstance(__o, Timestamp) == False:
            raise TypeError("FATAL: only Timestamp is supported.")
        return self.datetime < __o.datetime

    def __gt__(self, __o: Self | int) -> bool:
        if isinstance(__o, Timestamp) == False:
            raise TypeError("FATAL: Only SignalTimestamp and int are supported.")
        return self.datetime > __o.datetime

    ##########################
    # Getters:
    ##########################

    def get_timestamp(self) -> int:
        return self.timestamp

    def get_datetime(self) -> datetime.datetime:
        return self.datetime

    def get_display_time(self, local_time: bool = True) -> str:
        if local_time:
            display_time = self.get_local_time()
        else:
            display_time = self.datetime
        display_time_str = "%i<%s>" % (self.timestamp, display_time.isoformat())
        return display_time_str

    def get_local_time(self) -> datetime.datetime:
        local_tz = get_localzone()
        return self.datetime.astimezone(local_tz)

    ########################
    # Method:
    ########################
    def print(self, indent: int = 0, indent_char: str = ' ', file=sys.stdout) -> None:
        # Arg Checks:
        if not isinstance(indent, int):
            raise TypeError("indent must be of type int.")
        if not isinstance(indent_char, str):
            raise TypeError("indent_char must be of type str.")
        if len(indent_char) != 1:
            raise ValueError("indent_char must be 1 character long.")
        # Convert to local time:
        localTz = get_localzone()
        localDatetime = self.datetime.astimezone(localTz)
        # Create indent string:
        indentString: str = indent_char * indent
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
