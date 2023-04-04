#!/usr/bin/env python3
"""File: signalPreview.py"""
from typing import Optional, Iterable
import urllib.request
import hashlib
import os
import shutil
import sys

CAN_PREVIEW: bool = False
DEBUG: bool = False
try:
    from linkpreview import link_preview

    CAN_PREVIEW = True
except ModuleNotFoundError:
    if DEBUG:
        print("Cannot preview links, linkpreview is not installed.")
        print("This can be installed using pip3 install linkpreview.")

from .signalAttachment import Attachment
from .signalCommon import __type_error__


class Preview(object):
    """Class containing a preview of a link."""
    def __init__(self,
                 config_path: str,
                 from_dict: dict[str, object] = None,
                 raw_preview: dict[str, object] = None,
                 generate_preview: bool = False,
                 url: Optional[str] = None,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 image: Optional[Attachment | str] = None,
                 ) -> None:
        # Check config_path:
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        # Check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        # Check raw_preview:
        if raw_preview is not None and not isinstance(raw_preview, dict):
            __type_error__("raw_preview", "dict", raw_preview)
        # Check generate preview:
        if not isinstance(generate_preview, bool):
            __type_error__("generate_preview", "bool", generate_preview)
        # Check url:
        if url is not None and not isinstance(url, str):
            __type_error__("url", "str", url)
        # Check title:
        if title is not None and not isinstance(title, str):
            __type_error__("title", "str", title)
        # Check description:
        if description is not None and not isinstance(description, str):
            __type_error__("description", "str", description)
        # Check image:
        if image is not None and not isinstance(image, Attachment) and not isinstance(image, str):
            __type_error__("image", "Attachment | str", image)
        # Set internal Vars:
        self._config_path = config_path
        # Set external properties:
        self.url: Optional[str] = url
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.image: Attachment
        if isinstance(image, Attachment):
            self.image = image
        elif isinstance(image, str):
            self.image = Attachment(config_path=config_path, local_path=image)
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw preview:
        elif raw_preview is not None:
            self.__from_raw_preview__(raw_preview)
        # Generate raw preview from url:
        elif generate_preview:
            if self.url is None:
                error_message = "If generate_preview is True, url must be defined."
                raise RuntimeError(error_message)
            if CAN_PREVIEW:
                self.__generate_preview__()
        return

    ####################
    # Init:
    ####################
    def __from_raw_preview__(self, raw_preview: dict[str, object]) -> None:
        # print(raw_preview)
        self.url = raw_preview['url']
        self.title = raw_preview['title']
        self.description = raw_preview['description']
        self.image = None
        if raw_preview['image'] is not None:
            raw_attachment: dict[str, object] = raw_preview['image']
            self.image = Attachment(self._config_path, raw_attachment=raw_attachment)
        return

    def __generate_preview__(self) -> None:
        # Generate preview:
        preview = link_preview(self.url)
        # Set title:
        self.title = preview.title
        # Set description:
        self.description = preview.description
        # Create the directory to store preview images if it doesn't exist:
        preview_path = os.path.join(self._config_path, 'previews')
        if not os.path.exists(preview_path):
            try:
                os.mkdir(preview_path)
            except Exception as e:
                error_message = "FATAL: Failed to create preview directory '%s': %s" % (preview_path, str(e.args))
                raise RuntimeError(error_message)
        # Create the filename by hashing the url, and create the absolute path:
        hash_result = hashlib.md5(preview.image.encode())
        preview_image_file_name = hash_result.hexdigest()
        preview_image_file_path = os.path.join(preview_path, preview_image_file_name)
        # Check if the file exists and create the attachment:
        if os.path.exists(preview_image_file_path):
            self.image = Attachment(self._config_path, local_path=preview_image_file_path)
            return
        # Download the image:
        # Try to open the url:
        try:
            response = urllib.request.urlopen(preview.image)
        except Exception as e:
            if DEBUG:
                error_message = "Failed to open url: '%s': %s" % (preview.image, str(e.args))
                print(error_message, file=sys.stderr)
            self.image = None
            return
        # Try to open the destination file:
        try:
            fileHandle = open(preview_image_file_path, 'wb')
        except Exception as e:
            if DEBUG:
                error_message = "Failed to open file '%s' for writing(binary): %s" % (
                preview_image_file_path, str(e.args))
                print(error_message, file=sys.stderr)
            self.image = None
            return
        # Copy the data to the file:
        shutil.copyfileobj(response, fileHandle)
        fileHandle.close()
        # Create the attachment:
        self.image = Attachment(config_path=self._config_path, local_path=preview_image_file_path)
        return

    ######################
    # To / From Dict:
    ######################
    def __to_dict__(self) -> dict[str, object]:
        preview_dict = {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "image": None,
        }
        if self.image is not None:
            preview_dict['image'] = self.image.__to_dict__()
        return preview_dict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        self.url = from_dict['url']
        self.title = from_dict['title']
        self.description = from_dict['description']
        self.image = None
        if from_dict['image'] is not None:
            image_dict: dict[str, object] = from_dict['image']
            self.image = Attachment(config_path=self._config_path, from_dict=image_dict)
        return
