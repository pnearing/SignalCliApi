#!/usr/bin/env python3
"""
File signalTimestamp.py
Store and manage a timestamp.
"""
import logging
from typing import TypeVar, Optional, IO, Any
import datetime
import sys
import pytz
from tzlocal import get_localzone

from .signalCommon import __type_error__
from .signalExceptions import ParameterError

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
        # Super:
        object.__init__(self)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Verify args:
        if timestamp is None and from_dict is None and not now and date_time is None:
            error_message = "'timestamp', 'from_dict', 'date_time' must be defined, or 'now' must be True."
            logger.critical("Raising ParameterError(%s)." % error_message)
            raise ParameterError(error_message)

        # Type check args:
        if timestamp is not None and not isinstance(timestamp, int):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "int", timestamp)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, object]", from_dict)
        if date_time is not None and not isinstance(date_time, datetime.datetime):
            logger.critical("Raising TypeError:")
            __type_error__("date_time", "date_time.date_time", date_time)
        if not isinstance(now, bool):
            logger.critical("Raising TypeError:")
            __type_error__("now", "bool", now)

        # Set vars:
        self.timestamp: int = timestamp  # Int
        """The integer timestamp."""
        self.date_time: Optional[datetime.datetime] = None  # Python tz aware date_time object.
        """The tz aware datetime object."""

        # Load from INT timestamp:
        if self.timestamp is not None:
            self.__set_date_time__()
        # Load from dict:
        elif from_dict is not None:
            self.__from_dict__(from_dict=from_dict)
        # Load from a datetime object:
        elif date_time is not None:
            self.__from_date_time__(date_time)
        # Set timestamp as NOW:
        elif now:
            self.__from_now__()
        return

    ##########################
    # Init functions:
    ##########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of the timestamp.
        :return: dict[str, Any]: The dict to pass to __from_dict__()
        """
        timestamp_dict = {
            'timestamp': self.date_time.timestamp()
        }
        return timestamp_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        self.date_time = pytz.utc.localize(datetime.datetime.fromtimestamp(from_dict['timestamp']))
        self.timestamp = int(from_dict['timestamp'] * 1000)
        return

    def __from_now__(self) -> None:
        """
        Generate properties from now.
        :return: None
        """
        self.date_time = pytz.utc.localize(datetime.datetime.utcnow())
        seconds = self.date_time.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __from_date_time__(self, date_time: datetime.datetime) -> None:
        """
        Generate properties from a datetime object.
        :param date_time: The datetime object to load from.
        :return: None
        """
        try:
            self.date_time = pytz.utc.localize(date_time)
        except ValueError:
            self.date_time = date_time
        seconds = self.date_time.timestamp()
        self.timestamp = int(seconds * 1000)
        return

    def __set_date_time__(self) -> None:
        """
        Calculate the datetime property from the timestamp.
        :return: None
        """
        seconds = int(self.timestamp // 1000)
        microseconds = int((((self.timestamp / 1000) - seconds) * 1000) * 1000)
        self.date_time = pytz.utc.localize(datetime.datetime.fromtimestamp(seconds))
        self.date_time = self.date_time.replace(microsecond=microseconds)
        return

    ##########################################
    # Object functions/ methods:
    ##########################################
    def __int__(self) -> int:
        """
        Represent as an int.
        :return: int
        """
        return self.timestamp

    def __float__(self) -> float:
        """
        Represent as a float.
        :return: float
        """
        return self.date_time.timestamp()

    def __str__(self) -> str:
        """
        Represent as a string.
        :return: str: A formatted string with timestamp int, and datetime in iso format.
        """
        return_str: str = "%s<%i>" % (self.date_time.isoformat(), self.timestamp)
        return return_str

    def __eq__(self, other: Self | int) -> bool:
        """
        Calculate equality.
        :param other: Timestamp | int: The object to compare to.
        :return: bool
        :raises TypeError: If other is not a Timestamp or int.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__eq__.__name__)
        if isinstance(other, Timestamp):
            return self.date_time == other.date_time
        elif isinstance(other, int):
            return self.timestamp == other
        error_message: str = "Can only compare equality to Timestamp or int."
        logging.critical("Raising TypeError(%s)." % error_message)
        raise TypeError(error_message)

    def __lt__(self, other: Self | int) -> bool:
        """
        Compare less than.
        :param other: Timestamp or int: The object to compare to.
        :return: bool
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__lt__.__name__)
        if isinstance(other, Timestamp):
            return self.date_time < other.date_time
        elif isinstance(other, int):
            return self.timestamp < other
        error_message: str = "Can only compare less than to Timestamp or int."
        logger.critical("Raising TypeError(%s)." % error_message)
        raise TypeError(error_message)

    def __gt__(self, other: Self | int) -> bool:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__gt__.__name__)
        if isinstance(other, Timestamp):
            return self.date_time > other.date_time
        elif isinstance(other, int):
            return self.timestamp > other
        error_message: str = "Can only compare greater than to Timestamp or int."
        logger.critical("Raising TypeError(%s)." % error_message)
        raise TypeError(error_message)

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
        :returns: str: A display version of the timestamp, optionally converted to localtime.
        :raises: TypeError: If local_time is not a boolean.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_display_time.__name__)
        if not isinstance(local_time, bool):
            logger.critical("Raising TypeError:")
            __type_error__("local_time", "bool", local_time)
        if local_time:
            return self.get_local_time().isoformat()
        else:
            return self.date_time.isoformat()

    def get_local_time(self) -> datetime.datetime:
        """
        Get a datetime.datetime object that has been localized to the system timezone.
        :returns: datetime.datetime object representing the timestamp in local time.
        """
        return self.date_time.astimezone(get_localzone())

    def get_seconds_ago(self) -> int:
        """
        Get the number of seconds that has elapsed since this timestamp's time.
        :return: int: The number of seconds.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self.date_time
        return int(t_delta.total_seconds())

    def get_minutes_ago(self) -> int:
        """
        Get the number of minutes that has elapsed since this timestamp's time.
        :return: int: The number of minutes.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self.date_time
        return int(t_delta.total_seconds() / 60)

    def get_hours_ago(self) -> int:
        """
        Get the number of hours that has elapsed since this timestamp's time.
        :return: int: The number of hours.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self.date_time
        return int(t_delta.total_seconds() / 3600)

    def get_days_ago(self) -> int:
        """
        Get the number of days elapsed since this timestamp's time.
        :return: int: The number of days.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self.date_time
        return int(t_delta.total_seconds() / 86400)

    def get_weeks_ago(self) -> int:
        """
        Get the number of weeks that have elapsed since the timestamp's time.
        :return: int: The number of weeks.
        """
        return int(self.get_days_ago() / 7)

    def get_date(self) -> datetime.date:
        """
        Get the date portion of this timestamp.
        :return: datetime.date: The date portion.
        """
        return datetime.date(self.date_time.year, self.date_time.month, self.date_time.year)

    def get_time(self) -> datetime.time:
        """
        Get the time portion of the datetime.
        :return: datetime.time: The time portion.
        """
        return datetime.time(self.date_time.hour, self.date_time.minute, self.date_time.second,
                             self.date_time.microsecond, tzinfo=self.date_time.tzinfo)

