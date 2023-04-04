#!/usr/bin/env python3

from typing import TypeVar, Optional
import mimetypes
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, find_xdgopen
from .signalThumbnail import Thumbnail

Self = TypeVar("Self", bound="Attachment")

DEBUG: bool = False


class Attachment(object):
    """
    Class to store an attachment.
    """

    def __init__(self,
                 config_path: str,
                 from_dict: Optional[dict] = None,
                 raw_attachment: Optional[dict] = None,
                 content_type: Optional[str] = None,
                 file_name: Optional[str] = None,
                 size: Optional[int] = None,
                 local_path: Optional[str] = None,
                 thumbnail: Optional[Thumbnail] = None,
                 ) -> None:
        # Check config_path:
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        # Check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict[str, object]", from_dict)
        # Check raw Attachment:
        if raw_attachment is not None and not isinstance(raw_attachment, dict):
            __type_error__("raw_attachment", "dict[str, object]", raw_attachment)
        # Check content type:
        if content_type is not None and not isinstance(content_type, str):
            __type_error__("content_type", "str", content_type)
        # Check filename:
        if file_name is not None and not isinstance(file_name, str):
            __type_error__("filename", "str", file_name)
        # Check size:
        if size is not None and not isinstance(size, int):
            __type_error__("size", "int", size)
        # Check local_path:
        if local_path is not None and not isinstance(local_path, str):
            __type_error__("local_path", "str", local_path)
        # Check thumbnail:
        if thumbnail is not None and not isinstance(thumbnail, Thumbnail):
            __type_error__("thumbnail", "Thumbnail", thumbnail)

        # Set internal vars:
        self._config_path: str = config_path
        self._xdgopen_path: Optional[str] = find_xdgopen()
        # Set external vars:
        self.content_type: Optional[str] = content_type
        self.filename: Optional[str] = file_name
        self.size: Optional[int] = size
        self.local_path: Optional[str] = local_path
        self.exists: bool = False
        if local_path is not None:
            self.exists = os.path.exists(local_path)
        self.thumbnail: Thumbnail = thumbnail
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw Attachment
        elif raw_attachment is not None:
            self.__from_raw_attachment__(raw_attachment)
        # Set properties from local path:
        else:
            if self.local_path is not None:
                self.exists = os.path.exists(self.local_path)
                if self.exists:
                    self.content_type = mimetypes.guess_type(local_path)
                    self.filename = os.path.split(local_path)[-1]
                    self.size = os.path.getsize(local_path)
            else:
                self.exists = False
        return

    def __from_raw_attachment__(self, raw_attachment: dict) -> None:
        self.content_type = raw_attachment['contentType']
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
            self.thumbnail = Thumbnail(config_path=self._config_path, raw_thumbnail=raw_attachment['thumbnail'])
        return

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict:
        attachment_dict = {
            'content_type': self.content_type,
            'id': self.id,
            'filename': self.filename,
            'size': self.size,
            'localPath': self.local_path,
            'thumbnail': None,
        }
        if self.thumbnail is not None:
            attachment_dict['thumbnail'] = self.thumbnail.__to_dict__()
        return attachment_dict

    def __from_dict__(self, from_dict: dict) -> None:
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
            self.thumbnail = Thumbnail(config_path=self._config_path, from_dict=from_dict['thumbnail'])
        return

    ########################
    # Getters:
    ########################
    def get_file_path(self) -> Optional[str]:
        """
        Get the local path.
        :returns: Optional[str]: The path to the local copy of the file, if not found, and a thumbnail exists it will
                                    return the path to the local thumbnail file, otherwise it will return None.
        """
        if self.local_path is not None:
            return self.local_path
        if self.thumbnail is not None and self.thumbnail.local_path is not None:
            return self.thumbnail.local_path
        return None

    ########################
    # Methods:
    ########################
    def display(self) -> bool:
        """
        Call xdg-open on the local copy of the attachment if it exists, if it doesn't exist and a thumbnail does, it
            will try to call xdg-open on the thumbnail.
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
        elif self.thumbnail is not None:
            return self.thumbnail.display()
        return False
