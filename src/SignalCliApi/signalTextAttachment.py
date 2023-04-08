#!/usr/bin/env python3
"""File: signalTextAttachment.py"""
from typing import Optional

from .signalCommon import __type_error__
DEBUG: bool = False


class TextAttachment(object):
    """Class to store a 'text attachment' from story messages."""
    def __init__(self,
                 from_dict: Optional[dict[str, object]] = None,
                 raw_attachment: Optional[dict[str, object]] = None,
                 text: Optional[str] = None,
                 style: Optional[str] = None,
                 text_foreground_color: Optional[str] = None,
                 text_background_color: Optional[str] = None,
                 background_color: Optional[str] = None,
                 ) -> None:
        # Argument checks:
        # Check text:
        if text is not None and not isinstance(text, str):
            __type_error__("text", "str", text)
        # Check style:
        if style is not None and not isinstance(style, str):
            __type_error__("style", "str", style)
        # check text fg colour:
        if text_foreground_color is not None and not isinstance(text_foreground_color, str):
            __type_error__("text_foreground_color", "str", text_foreground_color)
        # Check text bg colour:
        if text_background_color is not None and not isinstance(text_background_color, str):
            __type_error__("text_background_color", "str", text_background_color)
        # Check bg Colour:
        if background_color is not None and not isinstance(background_color, str):
            __type_error__("background_color", "str", background_color)
        # Set external properties
        # Set text:
        self.text: str = text
        # Set style:
        self.style: str = style
        # Set text bg colour:
        self.text_background_color = text_background_color
        # Set text fg colour:
        self.text_foreground_color = text_foreground_color
        # Set background colour:
        self.background_color = background_color
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse raw attachment
        elif raw_attachment is not None:
            self.__from_raw_attachment__(raw_attachment)
        return

    ####################
    # Init:
    ####################
    def __from_raw_attachment__(self, raw_attachment: dict[str, object]) -> None:
        # Load text:
        self.text = raw_attachment['text']
        self.style = raw_attachment['style']
        self.text_background_color = raw_attachment['textBackgroundColor']
        self.text_foreground_color = raw_attachment['textForegroundColor']
        self.background_color = raw_attachment['backgroundColor']
        return

    ####################
    # To / From dict:
    ####################
    def __to_dict__(self) -> dict[str, object]:
        textAttachmentDict = {
            'text': self.text,
            'style': self.style,
            'textBackgroundColor': self.text_background_color,
            'textForegroundColor': self.text_foreground_color,
            'backgroundColor': self.background_color,
        }
        return textAttachmentDict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        # Load text:
        self.text = from_dict['text']
        # Load style:
        self.style = from_dict['style']
        # Load text bg colour:
        self.text_background_color = from_dict['textBackgroundColor']
        # Load text fg colour:
        self.text_foreground_color = from_dict['textForegroundColor']
        # Load background colour:
        self.background_color = from_dict['backgroundColor']
        return
