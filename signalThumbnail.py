#!/usr/bin/env python3

from typing import Optional
import os
from subprocess import check_call, CalledProcessError

from .signalCommon import __type_error__, find_xdg_open


class Thumbnail(object):
    def __init__(self,
                 config_path: str,
                 from_dict: Optional[dict[str, object]] = None,
                 raw_thumbnail: Optional[dict[str, object]] = None,
                 content_type: Optional[str] = None,
                 filename: Optional[str] = None,
                 local_path: Optional[str] = None,
                 size: Optional[int] = None,
                 ) -> None:
        # TODO Argument checks
        # Set internal vars:
        self._config_path: str = config_path
        self._xdgopen_path: Optional[str] = find_xdg_open()
        # Set external properties:
        self.content_type: str = content_type
        self.filename: str = filename
        self.local_path: str = local_path
        self.exists: bool = False
        if local_path is not None:
            self.exists = os.path.exists(local_path)
        self.size: int = size
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw thumbnail:
        elif raw_thumbnail is not None:
            self.__from_raw_thumbnail__(raw_thumbnail)
        return

    ###################
    # Init:
    ###################
    def __from_raw_thumbnail__(self, raw_thumbnail: dict[str, object]) -> None:
        # print(raw_thumbnail)
        self.content_type = raw_thumbnail['content_type']
        self.filename = raw_thumbnail['file_name']
        self.local_path = os.path.join(self._config_path, 'attachments', raw_thumbnail['contact_id'])
        self.exists = os.path.exists(self.local_path)
        self.size = raw_thumbnail['size']
        return

    ############################
    # To / From dict:
    ############################
    def __to_dict__(self) -> dict[str, object]:
        thumbnail_dict = {
            'content_type': self.content_type,
            'file_name': self.filename,
            'local_path': self.local_path,
            'size': self.size,
        }
        return thumbnail_dict

    def __from_dict__(self, fromDict: dict[str, object]) -> None:
        self.content_type = fromDict['content_type']
        self.filename = fromDict['file_name']
        self.local_path = fromDict['local_path']
        self.exists = False
        if self.local_path is not None:
            self.exists = os.path.exists(self.local_path)
        else:
            self.exists = False
        self.size = fromDict['size']
        return

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
