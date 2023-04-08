#!/usr/bin/env python3

from typing import TypeVar, Optional, IO
import datetime
import sys
try:
    import pytz
except ModuleNotFoundError:
    print("Module: pytz not found, you can install using pip3 install pytz")
    exit(1)
try:
    from tzlocal import get_localzone
except ModuleNotFoundError:
    print("Module: tzlocal not found, you can install using 'sudo apt install python3-tzlocal', or by using ", end='')
    print("pip install tzlocal")
    exit(1)


from .signalCommon import __type_error__

Self = TypeVar("Self", bound="Timestamp")
DEBUG: bool = False


class Timestamp(object):
    """Time stamp object."""

    def __init__(self,
                 timestamp: Optional[int] = None,
                 from_dict: Optional[dict[str, object]] = None,
                 date_time: Optional[datetime.datetime] = None,
                 now: bool = False,
                 ) -> None:
        # Verify args:
        if timestamp is None and from_dict is None and not now and date_time is None:
            error_message = "FATAL: timestamp, from_dict, date_time must be defined, or now must be True."
            raise RuntimeError(error_message)
        # Type check args:
        if timestamp is not None and not isinstance(timestamp, int):
            __type_error__("timestamp", "int", timestamp)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict[str, object]", from_dict)
        if date_time is not None and not isinstance(date_time, datetime.datetime):
            __type_error__("date_time", "date_time.date_time", date_time)
        if not isinstance(now, bool):
            __type_error__("now", "bool", now)
        # Set vars:
        self.timestamp: int = timestamp  # Int
        self.date_time: Optional[datetime.datetime] = None  # Python tz aware date_time object.
        # Load from dict:
        if self.timestamp is not None:
            self.__set_date_time__()
        elif from_dict is not None:
            self.__from_dict__(from_dict=from_dict)
        elif date_time is not None:
            self.__from_date_time__(date_time)
        elif now:
            self.__from_now__()
        return

    ##########################
    # Init functions:
    ##########################
    def __to_dict__(self) -> dict:
        timestamp_dict = {
            'timestamp': self.date_time.timestamp()
        }
        return timestamp_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self.date_time = pytz.utc.localize(datetime.datetime.fromtimestamp(from_dict['timestamp']))
        self.timestamp = int(from_dict['timestamp'] * 1000)
        return

    def __from_now__(self) -> None:
        self.date_time = pytz.utc.localize(datetime.datetime.utcnow())
        seconds = self.date_time.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __from_date_time__(self, date_time: datetime.datetime) -> None:
        try:
            self.date_time = pytz.utc.localize(date_time)
        except ValueError:
            self.date_time = date_time
        seconds = self.date_time.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __set_date_time__(self) -> None:
        seconds = int(self.timestamp // 1000)
        microseconds = int((((self.timestamp / 1000) - seconds) * 1000) * 1000)
        self.date_time = pytz.utc.localize(datetime.datetime.fromtimestamp(seconds))
        self.date_time = self.date_time.replace(microsecond=microseconds)
        return

    ##########################################
    # Object functions/ methods:
    ##########################################
    def __int__(self) -> int:
        return self.timestamp

    def __float__(self) -> float:
        return self.date_time.timestamp()

    def __str__(self) -> str:
        return self.date_time.isoformat()

    def __eq__(self, __o: Self | int) -> bool:
        if not isinstance(__o, Timestamp) and not isinstance(__o, int):
            return False
        if isinstance(__o, Timestamp):
            return self.date_time == __o.date_time
        else:
            return self.timestamp == __o

    def __lt__(self, __o: Self | int) -> bool:
        if not isinstance(__o, Timestamp) and not isinstance(__o, int):
            raise TypeError("FATAL: only Timestamp and int are supported.")
        if isinstance(__o, Timestamp):
            return self.date_time < __o.date_time
        else:
            return self.timestamp < __o

    def __gt__(self, __o: Self | int) -> bool:
        if not isinstance(__o, Timestamp) and not isinstance(__o, int):
            raise TypeError("FATAL: Only SignalTimestamp and int are supported.")
        if isinstance(__o, Timestamp):
            return self.date_time > __o.datetime
        else:
            return self.timestamp > __o

    ##########################
    # Getters:
    ##########################

    def get_timestamp(self) -> int:
        """
        Get the timestamp int.
        :returns: int: Timestamp integer.
        """
        return self.timestamp

    def get_datetime(self) -> datetime.datetime:
        """
        Get the datetime.datetime object.
        :returns: datetime.datetime: The datetime object representing this timestamp.
        """
        return self.date_time

    def get_display_time(self, local_time: bool = True) -> str:
        """
        Get the timestamp as a display string.
        :param local_time: bool: True to convert to local time, False to leave as UTC.
        :returns: str: A display version of the timestamp, optionally converting to localtime.
        :raises: TypeError: If local_time is not a boolean.
        """
        if not isinstance(local_time, bool):
            __type_error__("local_time", "bool", local_time)
        if local_time:
            display_time = self.get_local_time()
        else:
            display_time = self.date_time
        display_time_str = "%i<%s>" % (self.timestamp, display_time.isoformat())
        return display_time_str

    def get_local_time(self) -> datetime.datetime:
        """
        Get a datetime.datetime object that has been localized to the system timezone.
        :returns: datetime.datetime object representing the timestamp in local time.
        """
        local_tz = get_localzone()
        return self.date_time.astimezone(local_tz)

    ########################
    # Method:
    ########################
    def print(self, indent: int = 0, indent_char: str = ' ', local_time: bool = True, file: IO = sys.stdout) -> None:
        """
        Print out the timestamp.
        :param: int: indent: The number of 'indent_char' to indent each line with.
        :param: str: indent_char: The character to indent with, defaults to ' ' (space).
        :param: bool: local_time: Convert to local time.
        :param: IO: file: The io stream to output to, defaults to sys.stdout.
        :raises: TypeError: If indent not an int, if indent_char not a string, or if file not an IO object.
        :raises: ValueError: If indent char not a single character (len != 1).
        """
        # Arg Checks:
        if not isinstance(indent, int):
            __type_error__("indent", "int", indent)
        if not isinstance(indent_char, str):
            __type_error__("indent_char", "str", indent_char)
        if len(indent_char) != 1:
            raise ValueError("indent_char must be 1 character long.")
        if not isinstance(local_time, bool):
            __type_error__("local_time", "bool", local_time)
        display_datetime: datetime.datetime
        if local_time:
            # Convert to local time:
            local_tz = get_localzone()
            display_datetime = self.date_time.astimezone(local_tz)
        else:
            display_datetime = self.date_time
        # Create indent string:
        indent_string: str = indent_char * indent
        print(indent_string, "--------Begin Timestamp--------", file=file)
        display_line = "Timestamp: %i(%s)" % (self.timestamp, display_datetime.isoformat())
        print(indent_string, display_line, file=file)
        print(indent_string, "---------End Timestamp---------", file=file)
        return


if __name__ == '__main__':
    timestamp = Timestamp(now=True)
    timestamp.print()
