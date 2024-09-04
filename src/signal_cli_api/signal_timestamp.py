#!/usr/bin/env python3
"""
File signal_timestamp.py
Store and manage a timestamp.
"""
# pylint: disable=E0401, R0904, R0911
import logging
from typing import TypeVar, Optional, Any
import datetime
import pytz
from tzlocal import get_localzone

from .signal_common import __type_error__, STRINGS
from .signal_exceptions import ParameterError

Self = TypeVar("Self", bound="SignalTimestamp")
DEBUG: bool = False


class SignalTimestamp:
    """Time stamp object."""

    def __init__(self,
                 timestamp: Optional[int] = None,
                 from_dict: Optional[dict[str, object]] = None,
                 datetime_obj: Optional[datetime.datetime] = None,
                 now: bool = False,
                 ) -> None:
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Verify args:
        if timestamp is None and from_dict is None and datetime_obj is None and not now:
            error_message = ("'timestamp', 'from_dict', 'date_time' must be defined, or 'now' "
                             "must be True.")
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        # Type check args:
        if timestamp is not None and not isinstance(timestamp, int):
            logger.critical("Raising TypeError:")
            __type_error__("timestamp", "int", timestamp)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, object]", from_dict)
        if datetime_obj is not None and not isinstance(datetime_obj, datetime.datetime):
            logger.critical("Raising TypeError:")
            __type_error__("date_time", "date_time.date_time", datetime_obj)
        if not isinstance(now, bool):
            logger.critical("Raising TypeError:")
            __type_error__("now", "bool", now)

        # Set vars:
        self._timestamp: int = timestamp  # Int
        """The integer timestamp."""
        self._datetime: Optional[datetime.datetime] = None  # Python tz aware date_time object.
        """The tz aware datetime object."""

        # Load from INT timestamp:
        if self._timestamp is not None:
            self.__set_date_time__()
        # Load from dict:
        elif from_dict is not None:
            self.__from_dict__(from_dict=from_dict)
        # Load from a datetime object:
        elif datetime_obj is not None:
            self.__from_date_time__(datetime_obj)
        # Set timestamp as NOW:
        elif now:
            self.__from_now__()

    ##########################
    # Init functions:
    ##########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of the timestamp.
        :return: dict[str, Any]: The dict to pass to __from_dict__()
        """
        timestamp_dict = {
            'timestamp': self._datetime.timestamp()
        }
        return timestamp_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        self._datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(from_dict['timestamp']))
        self._timestamp = int(from_dict['timestamp'] * 1000)

    def __from_now__(self) -> None:
        """
        Generate properties from now.
        :return: None
        """
        self._datetime = pytz.utc.localize(datetime.datetime.utcnow())
        seconds = int(self._datetime.timestamp())
        self._timestamp = seconds * 1000

    def __from_date_time__(self, date_time: datetime.datetime) -> None:
        """
        Generate properties from a datetime object.
        :param date_time: The datetime object to load from.
        :return: None
        """
        try:
            self._datetime = pytz.utc.localize(date_time)
        except ValueError:
            self._datetime = date_time
        seconds = self._datetime.timestamp()
        self._timestamp = int(seconds * 1000)

    def __set_date_time__(self) -> None:
        """
        Calculate the datetime property from the timestamp.
        :return: None
        """
        seconds = int(self._timestamp // 1000)
        microseconds = int((((self._timestamp / 1000) - seconds) * 1000) * 1000)
        self._datetime = pytz.utc.localize(datetime.datetime.fromtimestamp(seconds))
        self._datetime = self._datetime.replace(microsecond=microseconds)

    ##########################################
    # Object functions/ methods:
    ##########################################
    def __int__(self) -> int:
        """
        Represent as an int.
        :return: int
        """
        return self._timestamp

    def __float__(self) -> float:
        """
        Represent as a float.
        :return: float
        """
        return self._datetime.timestamp()

    def __str__(self) -> str:
        """
        Represent as a string.
        :return: str: A formatted string with timestamp int, and datetime in iso format.
        """
        return f"{self._datetime.isoformat()}<{self._timestamp}>"

    def __eq__(self, other: Self | int) -> bool:
        """
        Calculate equality.
        :param other: SignalTimestamp | int: The object to compare to.
        :return: bool
        :raises TypeError: If other is not a SignalTimestamp or int.
        """
        # logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__eq__.__name__)
        if isinstance(other, SignalTimestamp):
            return self._datetime == other._datetime
        if isinstance(other, int):
            return self._timestamp == other
        error_message: str = "Can only compare equality to SignalTimestamp or int."
        logging.critical("Raising TypeError(%s).", error_message)
        raise TypeError(error_message)

    def __lt__(self, other: Self | int) -> bool:
        """
        Compare less than.
        :param other: SignalTimestamp or int: The object to compare to.
        :return: bool
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__lt__.__name__)
        if isinstance(other, SignalTimestamp):
            return self._datetime < other._datetime
        if isinstance(other, int):
            return self._timestamp < other
        error_message: str = "Can only compare less than to SignalTimestamp or int."
        logger.critical("Raising TypeError(%s).", error_message)
        raise TypeError(error_message)

    def __gt__(self, other: Self | int) -> bool:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__gt__.__name__)
        if isinstance(other, SignalTimestamp):
            return self._datetime > other._datetime
        if isinstance(other, int):
            return self._timestamp > other
        error_message: str = "Can only compare greater than to SignalTimestamp or int."
        logger.critical("Raising TypeError(%s).", error_message)
        raise TypeError(error_message)

    ##########################
    # Getters:
    ##########################
    def get_timestamp(self) -> int:
        """
        Get the timestamp int.
        :returns: int: SignalTimestamp integer.
        """
        return self._timestamp

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

        t_delta = self._datetime - pytz.utc.localize(datetime.datetime.utcnow())
        if t_delta.total_seconds() == 0:
            return STRINGS['lessThanASecond'] + '.'
        if 0 < t_delta.total_seconds() < 2:
            return str(t_delta.total_seconds()) + ' ' + STRINGS['secondAgo'] + '.'
        if 2 <= t_delta.total_seconds() < 60:
            return str(t_delta.total_seconds()) + ' ' + STRINGS['secondsAgo'] + '.'
        if 60 <= t_delta.total_seconds() < 61:
            return str(self.get_minutes_ago()) + ' ' + STRINGS['minuteAgo'] + '.'
        if 61 <= t_delta.total_seconds() < 3600:
            return str(self.get_minutes_ago()) + ' ' + STRINGS['minutesAgo'] + '.'
        if 3600 <= t_delta.total_seconds() < 7200:
            return str(self.get_hours_ago()) + ' ' + STRINGS['hourAgo'] + '.'
        if 7200 <= t_delta.total_seconds() < 86400:
            return str(self.get_hours_ago()) + ' ' + STRINGS['hoursAgo'] + '.'
        if 86400 <= t_delta.total_seconds() < 172800:
            return str(self.get_days_ago()) + ' ' + STRINGS['dayAgo'] + '.'
        if 172800 <= t_delta.total_seconds() < 604800:
            return str(self.get_days_ago()) + ' ' + STRINGS['daysAgo'] + '.'

        if local_time:
            return self.get_local_time(include_micros=False).isoformat()

        return self.get_datetime(include_micros=False).isoformat()

    def get_local_time(self, include_micros: bool = True) -> datetime.datetime:
        """
        Get a datetime.datetime object that has been localized to the system timezone.
        :returns: datetime.datetime object representing the timestamp in local time.
        """
        date_time_obj = self.get_datetime(include_micros)
        return date_time_obj.astimezone(get_localzone())

    def get_seconds_ago(self) -> int:
        """
        Get the number of seconds that has elapsed since this timestamp's time.
        :return: int: The number of seconds.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self._datetime
        return int(t_delta.total_seconds())

    def get_minutes_ago(self) -> int:
        """
        Get the number of minutes that has elapsed since this timestamp's time.
        :return: int: The number of minutes.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self._datetime
        return int(t_delta.total_seconds() / 60)

    def get_hours_ago(self) -> int:
        """
        Get the number of hours that has elapsed since this timestamp's time.
        :return: int: The number of hours.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self._datetime
        return int(t_delta.total_seconds() / 3600)

    def get_days_ago(self) -> int:
        """
        Get the number of days elapsed since this timestamp's time.
        :return: int: The number of days.
        """
        now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
        t_delta: datetime.timedelta = now - self._datetime
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
        return datetime.date(self.year, self.month, self.day)

    def get_time(self, include_micros: bool = False) -> datetime.time:
        """
        Get the time portion of the datetime.
        :param include_micros: bool: Include the microsecond portion. Defaults to False.
        :return: datetime.time: The time portion.
        """
        if include_micros:
            return datetime.time(self.hour, self.minute, self.second, self.microsecond,
                                 tzinfo=self.tz_info)
        return datetime.time(self.hour, self.minute, self.second, tzinfo=self.tz_info)

    def get_datetime(self, include_micros: bool) -> datetime.datetime:
        """
        Get a datetime object for this timestamp:
        :param include_micros: bool: True, include the microseconds in the time portion.
        :return: datetime.datetime: The new datetime object.
        """
        if include_micros:
            return datetime.datetime(self.year, self.month, self.day, self.hour, self.minute,
                                     self.second, self.microsecond, self.tz_info)
        return datetime.datetime(self.year, self.month, self.day, self.hour, self.minute,
                                 self.second, tzinfo=self.tz_info)

#################################
# Properties:
#################################
    @property
    def timestamp(self) -> int:
        """
        The signal timestamp value.
        :returns: int
        """
        return self._timestamp

    @property
    def datetime_obj(self) -> datetime.datetime:
        """
        The timestamp as a datetime object.
        :return: datetime
        """
        return self._datetime

    @property
    def year(self) -> int:
        """
        The year of this timestamp.
        :returns: int
        """
        return self._datetime.year

    @property
    def month(self) -> int:
        """
        The month of this timestamp.
        :returns: int
        """
        return self._datetime.month

    @property
    def day(self) -> int:
        """
        The day of the month for this timestamp.
        :returns: int
        """
        return self._datetime.day

    @property
    def hour(self) -> int:
        """
        The hour of this timestamp.
        :returns: int
        """
        return self._datetime.hour

    @property
    def minute(self) -> int:
        """
        The minute of this timestamp.
        :returns: int
        """
        return self._datetime.minute

    @property
    def second(self) -> int:
        """
        The second of this timestamp.
        :returns: int
        """
        return self._datetime.second

    @property
    def microsecond(self) -> int:
        """
        The microseconds of this message.
        :returns: int
        """
        return self._datetime.microsecond

    @property
    def tz_info(self) -> pytz.tzinfo:
        """
        The timezone for this timestamp.
        :returns: pytz.tzinfo
        """
        return self._datetime.tzinfo
