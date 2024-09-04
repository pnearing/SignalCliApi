#!/usr/bin/env python3
"""
File signal_thumbnail.py
Store and handle a signal thumbnail.
"""
# pylint: disable=R0902, R0903, R0915
import logging
import mimetypes
from typing import Optional, Any
import os
from subprocess import check_call, CalledProcessError
from .signal_exceptions import ParameterError
from .signal_common import __type_error__, __find_xdgopen__
from .signal_timestamp import SignalTimestamp


class SignalThumbnail:
    """Class to store a thumbnail."""
    def __init__(self,
                 config_path: str,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_thumbnail: Optional[dict[str, Any]] = None,
                 local_path: Optional[str] = None,
                 ) -> None:
        """
        Initialize a SignalThumbnail.
        :param config_path: str: The full path to the signal-cli config directory.
        :param from_dict: Optional[dict[str, Any]]: The dict provided by __to_dict__().
        :param raw_thumbnail: Optional[dict[str, Any]]: The raw dict provided by signal.
        :param local_path: Optional[str]: The local path of the thumbnail.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if raw_thumbnail is not None and not isinstance(raw_thumbnail, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_thumbnail", "dict", raw_thumbnail)
        if local_path is not None and not isinstance(local_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("local_path", "str", local_path)

        # Parameter checks:
        not_nones: int = 0
        for parameter in (from_dict, raw_thumbnail, local_path):
            if parameter is not None:
                not_nones += 1
        if not_nones == 0:
            error_message: str = ("One of 'config_path', 'from_dict', or 'local_path' "
                                  "must be defined.")
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)
        if not_nones >= 2:
            error_message: str = ("Only one of 'config_path', 'from_dict', and 'local_path', "
                                  "can be defined at once.")
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        # Value checks:
        if local_path is not None and not os.path.exists(local_path):
            error_message: str = f"'local_path': {local_path}, does not exist."
            logger.critical("Raising FileNotFoundError(%s).", error_message)
            raise FileNotFoundError(error_message)

        # Set internal vars:
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._xdgopen_path: Optional[str] = __find_xdgopen__()
        """The full path to the xdg-open executable."""

        # Set external properties:
        # Content-Type:
        self.content_type: Optional[str] = None
        """The thumbnail content-type."""
        # Thumbnail filename:
        self.filename: Optional[str] = None
        """The thumbnail filename."""
        self.local_path: Optional[str] = local_path
        """The local path to the file."""
        self.exists: bool = False
        """Does this file exist on disk?"""
        self.size: Optional[int] = None
        """The size of the thumbnail file in bytes."""
        self.height: Optional[int] = None
        """The height of the thumbnail in pixels."""
        self.width: Optional[int] = None
        """The width of the thumbnail in pixels."""
        self.caption: Optional[str] = None
        """The caption of the image."""
        self.upload_timestamp: Optional[SignalTimestamp] = None
        """When the thumbnail was uploaded."""
        # Parse from_dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Parse raw thumbnail:
        elif raw_thumbnail is not None:
            logger.debug("Loading from raw thumbnail.")
            self.__from_raw_thumbnail__(raw_thumbnail)
        # Generate properties from local_path:
        elif local_path is not None:
            self.content_type = mimetypes.guess_type(local_path)
            self.exists = os.path.exists(local_path)
            self.size = os.path.getsize(local_path)
            self.filename = os.path.split(local_path)[-1]

    ###################
    # Init:
    ###################
    def __from_raw_thumbnail__(self, raw_thumbnail: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_thumbnail: dict[str, Any]: The dict to load from.
        :return: None
        """
        # Load content type:
        self.content_type = None
        if 'contentType' in raw_thumbnail.keys():
            self.content_type = raw_thumbnail['contentType']

        # Load filename:
        self.filename = None
        if 'filename' in raw_thumbnail.keys():
            self.filename = raw_thumbnail['filename']

        # Load ID:
        self.id = None
        if 'id' in raw_thumbnail.keys():
            self.id = raw_thumbnail['id']

        # Load size:
        self.size = None
        if 'size' in raw_thumbnail.keys():
            self.size = raw_thumbnail['size']

        # Load height:
        self.height = None
        if 'height' in raw_thumbnail.keys():
            self.height = raw_thumbnail['height']

        # Load width:
        self.width = None
        if 'width' in raw_thumbnail.keys():
            self.width = raw_thumbnail['width']

        # Load caption:
        self.caption = None
        if 'caption' in raw_thumbnail.keys():
            self.caption = raw_thumbnail['caption']

        # Set local path and exists:
        self.local_path = None
        self.exists = False
        if self.filename is not None:
            self.local_path = os.path.join(self._config_path, 'attachments', self.filename)
            self.exists = os.path.exists(self.local_path)
        elif self.id is not None:
            self.local_path = os.path.join(self._config_path, 'attachments', self.id)
            self.exists = os.path.exists(self.local_path)

    ############################
    # To / From dict:
    ############################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Store properties in a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        thumbnail_dict: dict[str, Any] = {
            'contentType': self.content_type,
            'filename': self.filename,
            'id': self.id,
            'size': self.size,
            'height': self.height,
            'width': self.width,
            'caption': self.caption,
            'localPath': self.local_path,
        }
        return thumbnail_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        self.content_type = from_dict['contentType']
        self.filename = from_dict['filename']
        self.id = from_dict['id']
        self.size = from_dict['size']
        self.height = from_dict['height']
        self.width = from_dict['width']
        self.caption = from_dict['caption']
        self.local_path = from_dict['localPath']
        self.exists = False
        if self.local_path is not None:
            self.exists = os.path.exists(self.local_path)

    ############################
    # Methods:
    ############################
    def display(self) -> bool:
        """
        Run xdgopen on the thumbnail.
        :returns: bool: True = xdgopen successfully called.
        """
        if self._xdgopen_path is None:
            return False
        if not self.exists:
            return False
        try:
            check_call([self._xdgopen_path, self.local_path])
        except CalledProcessError:
            return False
        return True
