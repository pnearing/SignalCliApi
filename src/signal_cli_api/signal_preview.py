#!/usr/bin/env python3
"""
File: signal_preview.py
Store and handle a preview.
"""
# pylint: disable=R0903, R0912, R0913, R0915, R1732
import logging
from typing import Optional, Any
import urllib.request
import urllib.error
import hashlib
import os
import shutil
from .signal_attachment import SignalAttachment
from .signal_common import __type_error__
from .signal_exceptions import ParameterError

CAN_PREVIEW: bool
try:
    from linkpreview import link_preview
    CAN_PREVIEW = True
except ModuleNotFoundError:
    logging.getLogger(__name__).warning("linkpreview not installed, can't generate previews.")
    CAN_PREVIEW = False


class SignalPreview:
    """Class containing a preview of a link."""

    def __init__(self,
                 config_path: str,
                 from_dict: dict[str, Any] = None,
                 raw_preview: dict[str, Any] = None,
                 generate_preview: bool = False,
                 url: Optional[str] = None,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 image: Optional[SignalAttachment | str] = None,
                 ) -> None:
        """
        Initialize the preview.
        :param config_path: str: The full path to the signal-cli config directory.
        :param from_dict: dict[str, Any]: Load properties from a dict created by __to_dict__().
        :param raw_preview: dict[str, Any]: Load properties from a dict provided by signal.
        :param generate_preview: bool: Should we generate a preview?
            True requires linkpreview to be installed; If linkpreview is not installed, setting
            this to True will cause a RuntimeError to be raised. This is ignored if 'from_dict',
            or 'raw_preview' are defined.
        :param url: Optional[str]: The URL this preview, well, previews.
        :param title: Optional[str]: The title.
        :param description: Optional[str]: The description.
        :param image: Optional[SignalAttachment | str]: The preview image, either an
            SignalAttachment object pointing to a local file, or a str witch is the full path to
            the image file.
        :raises RuntimeError: If generate_preview is True and linkpreview is not installed.
        :raises RuntimeError: If we're not able to make the directory where we store the preview
            images we generate.
        :raises ParameterError: If generate_preview is True and 'url' is not defined.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Check config_path:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        # Check from_dict:
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        # Check raw_preview:
        if raw_preview is not None and not isinstance(raw_preview, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_preview", "dict", raw_preview)
        # Check generate preview:
        if not isinstance(generate_preview, bool):
            logger.critical("Raising TypeError:")
            __type_error__("generate_preview", "bool", generate_preview)
        # Check url:
        if url is not None and not isinstance(url, str):
            logger.critical("Raising TypeError:")
            __type_error__("url", "str", url)
        # Check title:
        if title is not None and not isinstance(title, str):
            logger.critical("Raising TypeError:")
            __type_error__("title", "str", title)
        # Check description:
        if description is not None and not isinstance(description, str):
            logger.critical("Raising TypeError:")
            __type_error__("description", "str", description)
        # Check image:
        if (image is not None and not isinstance(image, SignalAttachment) and
                not isinstance(image, str)):
            logger.critical("Raising TypeError:")
            __type_error__("image", "SignalAttachment | str", image)

        # Parameter checks:
        if generate_preview and url is None:
            error_message: str = "if 'generate_preview' is True, then 'url' must be defined."
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)
        if from_dict is not None and raw_preview is not None:
            error_message: str = "'from_dict' and 'raw_preview' cannot be used together."
            logger.critical("Raising ParameterError(%s).", error_message)
            raise ParameterError(error_message)

        # Set internal Vars:
        self._config_path = config_path
        """The full path to the signal-cli config directory."""
        # Set external properties:
        self.url: Optional[str] = url
        """The url this preview, previews."""
        self.title: Optional[str] = title
        """The title of the page."""
        self.description: Optional[str] = description
        """The description of the page."""
        self.image: Optional[SignalAttachment] = None
        """The preview image."""
        if isinstance(image, SignalAttachment):
            self.image = image
        elif isinstance(image, str):
            self.image = SignalAttachment(config_path=config_path, local_path=image)

        # Create the directory to store preview images if it doesn't exist:
        self._preview_path: str = os.path.join(self._config_path, 'previews')
        """The full path to the preview directory where we store our downloaded files."""
        if not os.path.exists(self._preview_path):
            try:
                os.mkdir(self._preview_path)
            except (OSError, FileNotFoundError, PermissionError) as e:
                error_message: str = (f"Failed to create preview directory "
                                      f"'{self._preview_path}': {str(e.args)}")
                raise RuntimeError(error_message) from e

        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw preview:
        elif raw_preview is not None:
            self.__from_raw_preview__(raw_preview)
        # Generate raw preview from url:
        elif generate_preview:
            if CAN_PREVIEW:
                self.__generate_preview__()
            else:
                error_message: str = "'linkpreview' is not installed, cannot generate preview."
                logger.critical("Raising RuntimeError(%s).", error_message)
                raise RuntimeError(error_message)

    ####################
    # Init:
    ####################
    def __from_raw_preview__(self, raw_preview: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_preview: dict[str, Any]: The dict to load from.
        :return: None
        """
        self.url = raw_preview['url']
        self.title = raw_preview['title']
        self.description = raw_preview['description']
        self.image = None
        if raw_preview['image'] is not None:
            raw_attachment: dict[str, object] = raw_preview['image']
            self.image = SignalAttachment(self._config_path, raw_attachment=raw_attachment)

    def __generate_preview__(self) -> None:
        """
        Generate a preview from a given url.
        :return: None
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__generate_preview__.__name__)
        # Generate preview:
        logger.debug("Generating preview with linkpreview...")
        preview = link_preview(self.url)
        logger.debug("Preview generated.")
        # Set title:
        self.title = preview.title
        # Set description:
        self.description = preview.description

        # Set the image:
        # Create the download filename by hashing the image url, and create the absolute path:
        preview_image_file_name = hashlib.md5(preview.image.encode()).hexdigest()
        preview_image_file_path = os.path.join(self._preview_path, preview_image_file_name)

        # Check if the file exists and create the attachment if it does:
        if os.path.exists(preview_image_file_path):
            self.image = SignalAttachment(self._config_path, local_path=preview_image_file_path)
            return
        # Download the image:
        # Try to open the url:
        try:
            response = urllib.request.urlopen(preview.image)
        except urllib.error.HTTPError as e:
            warning_message: str = (f"HTTPError while opening image "
                                    f"URL: {preview.image}: {str(e.args)}")
            logger.warning(warning_message)
            self.image = None
            return
        except urllib.error.URLError as e:
            warning_message: str = (f"URLError while opening image "
                                    f"URL: {preview.image}: {str(e.args)}")
            logger.warning(warning_message)
            self.image = None
            return

        # Try to open the destination file:
        try:
            file_handle = open(preview_image_file_path, 'wb')
        except (OSError, FileNotFoundError, PermissionError) as e:
            warning_message: str = (f"Failed to open '{preview_image_file_path}' with mode "
                                    f"'wb': {str(e.args)}")
            logger.warning(warning_message)
            self.image = None
            return
        # Copy the data to the file:
        shutil.copyfileobj(response, file_handle)
        file_handle.close()
        # Create the attachment:
        self.image = SignalAttachment(config_path=self._config_path,
                                      local_path=preview_image_file_path)

    ######################
    # To / From Dict:
    ######################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Produce a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__()
        """
        preview_dict: dict[str, Any] = {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "image": None,
        }
        if self.image is not None:
            preview_dict['image'] = self.image.__to_dict__()
        return preview_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        self.url = from_dict['url']
        self.title = from_dict['title']
        self.description = from_dict['description']
        self.image = None
        if from_dict['image'] is not None:
            image_dict: dict[str, Any] = from_dict['image']
            self.image = SignalAttachment(config_path=self._config_path, from_dict=image_dict)
