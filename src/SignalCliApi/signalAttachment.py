#!/usr/bin/env python3
"""
File: signalAttachment.py
Store and manage a signal attachment.
"""
import logging
from typing import TypeVar, Optional, Any
import mimetypes
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, __find_xdgopen__
from .signalThumbnail import SignalThumbnail
from .signalExceptions import ParameterError
# Define Self:
Self = TypeVar("Self", bound="SignalAttachment")


class SignalAttachment(object):
    """
    Class to store an attachment.
    """

    def __init__(self,
                 config_path: str,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_attachment: Optional[dict[str, Any]] = None,
                 local_path: Optional[str] = None,
                 thumbnail: Optional[SignalThumbnail] = None,
                 ) -> None:
        """
        Initialize an SignalAttachment object.
        :param config_path: str: The path to the signal-cli config directory.
        :param from_dict: Optional[dict[str, Any]]: The dict provided by __to_dict__().
        :param raw_attachment: Optional[dict[str, Any]]: The dict provided by signal.
        :param local_path: Optional[str]: The local path of this attachment.
        :param thumbnail: Optional[SignalThumbnail]: The SignalThumbnail object for this attachment.
        """
        # Super:
        object.__init__(self)

        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks:
        # Check config_path:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        # Check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict[str, object]", from_dict)
        # Check raw Attachment:
        if raw_attachment is not None and not isinstance(raw_attachment, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_attachment", "dict[str, object]", raw_attachment)
        # Check local_path:
        if local_path is not None and not isinstance(local_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("local_path", "str", local_path)
        if thumbnail is not None and not isinstance(thumbnail, SignalThumbnail):
            logger.critical("Raising TypeError:")
            __type_error__("thumbnail", "Optional[SignalThumbnail]", thumbnail)

        # Parameter checks:
        not_nones: int = 0
        for param in (from_dict, raw_attachment, local_path):
            if param is not None:
                not_nones += 1
        if not_nones == 0:
            error_message: str = "At least one of 'from_dict', 'raw_attachment', or 'local_path' must be defined."
            logger.critical("Raising ParameterError(%s)." % error_message)
            raise ParameterError(error_message)
        elif not_nones >= 2:
            error_message: str = "Only one of 'from_dict', 'raw_attachment', and local_path' can be defined at once."
            logger.critical("Raising ParameterError(%s)." % error_message)
            raise ParameterError(error_message)

        # Value checks:
        if local_path is not None and not os.path.exists(local_path):
            error_message: str = "'local_path' %s, does not exist." % local_path
            logger.critical("Raising FileNotFoundError(%s)." % error_message)
            raise FileNotFoundError(error_message)

        # Set internal vars:
        self._config_path: str = config_path
        """The path to the signal-cli config directory."""
        self._xdgopen_path: Optional[str] = __find_xdgopen__()
        """The path to xdg-open executable."""

        # Set external vars:
        # Content-Type:
        self.content_type: Optional[str] = None
        """The content-type of the attachment."""
        # Filename:
        self.filename: Optional[str] = None
        """The filename of this attachment."""
        # Size in bytes:
        self.size: Optional[int] = None
        """The size in bytes of the attachment."""
        # Local path:
        self.local_path: Optional[str] = local_path
        """The path to the local copy of the attachment."""
        # File exists:
        self.exists: bool = False
        """Does the local file exist?"""
        # Thumbnail:
        self.thumbnail: Optional[SignalThumbnail] = thumbnail
        """The SignalThumbnail object for this attachment."""

        # Parse from_dict:
        if from_dict is not None:
            logger.debug("Loading from dict.")
            self.__from_dict__(from_dict)
        # Parse from raw Attachment
        elif raw_attachment is not None:
            logger.debug("Loading from raw signal dict.")
            self.__from_raw_attachment__(raw_attachment)
        # Set properties from the local path:
        elif local_path is not None:  # We've checked that local_path exists earlier and Failed if it doesn't.
            logger.debug("'local_path' been passed in.")
            self.content_type = mimetypes.guess_type(local_path)
            self.exists = os.path.exists(local_path)
            self.filename = os.path.split(local_path)[-1]
            self.size = os.path.getsize(local_path)
        return

    def __from_raw_attachment__(self, raw_attachment: dict[str, Any]) -> None:
        """
        Load from a raw dict provided by signal.
        :param raw_attachment: dict[str, Any]: The dict to load from.
        :return: None
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__from_raw_attachment__.__name__)
        logger.debug("raw attachment: %s" % str(raw_attachment))
        self.content_type = raw_attachment['contentType']
        # TODO: No 'id' key:
        self.id = raw_attachment['id']
        self.filename = raw_attachment['filename']
        if 'size' in raw_attachment.keys():
            self.size = raw_attachment['size']
        else:
            self.size = None
        if 'id' in raw_attachment.keys():
            self.local_path = os.path.join(self._config_path, 'attachments', raw_attachment['id'])
            self.exists = os.path.exists(self.local_path)
        else:
            self.local_path = None
            self.exists = False
        self.thumbnail = None
        if 'thumbnail' in raw_attachment.keys():
            self.thumbnail = SignalThumbnail(config_path=self._config_path, raw_thumbnail=raw_attachment['thumbnail'])
        return

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to pass to __from_dict__()
        """
        attachment_dict = {
            'contentType': self.content_type,
            'id': self.id,
            'filename': self.filename,
            'size': self.size,
            'localPath': self.local_path,
            'thumbnail': None,
        }
        if self.thumbnail is not None:
            attachment_dict['thumbnail'] = self.thumbnail.__to_dict__()
        return attachment_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__()
        :return: None
        """
        self.content_type = from_dict['contentType']
        self.id = from_dict['id']
        self.filename = from_dict['filename']
        self.size = from_dict['size']
        self.local_path = from_dict['localPath']
        if self.local_path is not None:
            self.exists = os.path.exists(self.local_path)
        else:
            self.exists = False
        self.thumbnail = None
        if from_dict['thumbnail'] is not None:
            self.thumbnail = SignalThumbnail(config_path=self._config_path, from_dict=from_dict['thumbnail'])
        return

    ########################
    # Getters:
    ########################
    def get_local_path(self) -> Optional[str]:
        """
        Get the local path.
        :returns: Optional[str]: The path to the local copy of the file or None.
        """
        return self.local_path

    ########################
    # Methods:
    ########################
    def display(self) -> bool:
        """
        Call xdg-open on the local copy of the attachment if it exists.
        :returns: bool: True if xdg-open was successfully called.
        """
        if self._xdgopen_path is None:
            return False
        if self.local_path is not None and self.exists:
            try:
                check_call([self._xdgopen_path, self.local_path])
                return True
            except CalledProcessError:
                return False
