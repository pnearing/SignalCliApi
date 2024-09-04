#!/usr/bin/env python3
"""
File: signal_text_attachment.py
Store a signal Text Attachment.
"""
# pylint: disable=R0903
from typing import Optional, Any

# from .signal_common import __type_error__


class SignalTextAttachment:
    """
    Class to store a 'text attachment' from story messages.
    """
    def __init__(self,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_attachment: Optional[dict[str, Any]] = None,
                 # text: Optional[str] = None,
                 # style: Optional[str] = None,
                 # text_foreground_color: Optional[str] = None,
                 # text_background_color: Optional[str] = None,
                 # background_color: Optional[str] = None,
                 ) -> None:
        """
        Initialize a text attachment.
        :param from_dict: Optional[dict[str, Any]]: Load from a dict created by __to_dict__().
        :param raw_attachment: Optional[dict[str, Any]]: Load from a dict provided by Signal.
        """
        # Set external properties
        # Set text:
        self.text: str = ''
        """The text of the attachment."""
        # Set style:
        self.style: str = ''
        """The text style of the attachment."""
        # Set text bg colour:
        self.text_background_color: str = ''
        """The background colour of the text."""
        # Set text fg colour:
        self.text_foreground_color: str = ''
        """The foreground colour of the text."""
        # Set background colour:
        self.background_color: str = ''
        """The background colour."""

        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw attachment
        elif raw_attachment is not None:
            self.__from_raw_attachment__(raw_attachment)

    ####################
    # Init:
    ####################
    def __from_raw_attachment__(self, raw_attachment: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by Signal.
        :param raw_attachment: dict[str, Any]: The dict provided by Signal.
        :return: None
        """
        self.text = raw_attachment['text']
        self.style = raw_attachment['style']
        self.text_background_color = raw_attachment['textBackgroundColor']
        self.text_foreground_color = raw_attachment['textForegroundColor']
        self.background_color = raw_attachment['backgroundColor']

    ####################
    # To / From dict:
    ####################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict.
        :return: dict[str, Any]: The dict to pass to __from_dict__().
        """
        text_attachment_dict: dict[str, Any] = {
            'text': self.text,
            'style': self.style,
            'textBackgroundColor': self.text_background_color,
            'textForegroundColor': self.text_foreground_color,
            'backgroundColor': self.background_color,
        }
        return text_attachment_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__().
        :return: None
        """
        self.text = from_dict['text']
        self.style = from_dict['style']
        self.text_background_color = from_dict['textBackgroundColor']
        self.text_foreground_color = from_dict['textForegroundColor']
        self.background_color = from_dict['backgroundColor']
