#!/usr/bin/env python3

from typing import TypeVar, Optional
import mimetypes
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, find_xdg_open
from .signalThumbnail import Thumbnail

Self = TypeVar("Self", bound="Attachment")


class Attachment(object):
    def __init__(self,
                 config_path: str,
                 from_dict: Optional[dict] = None,
                 raw_attachment: Optional[dict] = None,
                 content_type: Optional[str] = None,
                 filename: Optional[str] = None,
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
        if raw_attachment is not None and  not isinstance(raw_attachment, dict):
            __type_error__("raw_attachment", "dict[str, object]", raw_attachment)
        # Check content type:
        if content_type is not None and not isinstance(content_type, str):
            __type_error__("content_type", "str", content_type)
        # Check filename:
        if filename is not None and not isinstance(filename, str):
            __type_error__("filename", "str", filename)
        # Check size:
        if size is not None and  not isinstance(size, int):
            __type_error__("size", "int", size)
        # Check local_path:
        if local_path is not None and not isinstance(local_path, str):
            __type_error__("local_path", "str", local_path)
        # Check thumbnail:
        if thumbnail is not None and not isinstance(thumbnail, Thumbnail):
            __type_error__("thumbnail", "Thumbnail", thumbnail)

        # Set internal vars:
        self._config_path: str = config_path
        self._xdgopen_path: Optional[str] = find_xdg_open()
        # Set external vars:
        self.content_type: Optional[str] = content_type
        self.file_name: Optional[str] = filename
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
                    self.file_name = os.path.split(local_path)[-1]
                    self.size = os.path.getsize(local_path)
            else:
                self.exists = False
        return

    def __from_raw_attachment__(self, raw_attachment: dict) -> None:
        print(raw_attachment.keys())
        # raise NotImplemented
        self.content_type = raw_attachment['content_type']
        self.file_name = raw_attachment['filename']
        if 'size' in raw_attachment.keys():
            self.size = raw_attachment['size']
        else:
            self.size = None
        if 'contact_id' in raw_attachment.keys():
            self.local_path = os.path.join(self._config_path, 'attachments', raw_attachment['contact_id'])
            self.exists = os.path.exists(self.local_path)
        else:
            self.local_path = None
            self.exists = False
        self.thumbnail = None
        if 'thumbnail' in raw_attachment.keys():
            self.thumbnail = Thumbnail(configPath=self._config_path, rawThumbnail=raw_attachment['thumbnail'])
        return

    #########################
    # To / From Dict:
    #########################
    def __to_dict__(self) -> dict:
        attachment_dict = {
            'content_type': self.content_type,
            'file_name': self.file_name,
            'size': self.size,
            'local_path': self.local_path,
            'thumbnail': None,
        }
        if self.thumbnail is not None:
            attachment_dict['thumbnail'] = self.thumbnail.__toDict__()
        return attachment_dict

    def __from_dict__(self, from_dict: dict) -> None:
        self.content_type = from_dict['content_type']
        self.id = from_dict['contact_id']
        self.file_name = from_dict['file_name']
        self.size = from_dict['size']
        self.local_path = from_dict['local_path']
        if self.local_path is not None:
            self.exists = os.path.exists(self.local_path)
        else:
            self.exists = False
        self.thumbnail = None
        if from_dict['thumbnail'] is not None:
            self.thumbnail = Thumbnail(configPath=self._config_path, fromDict=from_dict['thumbnail'])
        return

    ########################
    # Getters:
    ########################
    def get_file_path(self) -> Optional[str]:
        """
        Get the local path.
        """
        if self.local_path is not None:
            return self.local_path
        if self.thumbnail is not None and self.thumbnail.localPath is not None:
            return self.thumbnail.localPath
        return None

    ########################
    # Methods:
    ########################
    def display(self) -> bool:
        """
        call xdg open on the local file.
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
