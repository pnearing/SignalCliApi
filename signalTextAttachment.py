#!/usr/bin/env python3

from typing import Optional

from signalCommon import __typeError__

class TextAttachment(object):
    def __init__(self,
                        fromDict: Optional[dict[str, object]] = None,
                        rawAttachment: Optional[dict[str, object]] = None,
                        text: Optional[str] = None,
                        style: Optional[str] = None,
                        textForegroundColor: Optional[str] = None,
                        textBackgroundColor: Optional[str] = None,
                        backgroudColor: Optional[str] = None,
                    ) -> None:
# Argument checks:
    # Check text:
        if (text != None and isinstance(text, str) == False):
            __typeError__("text", "str", text)
    # Check style:
        if (style != None and isinstance(style, str) == False):
            __typeError__("style", "str", style)
    # check text fg colour:
        if (textForegroundColor != None and isinstance(textForegroundColor, str) == False):
            __typeError__("textForegroundColor", "str", textForegroundColor)
    # Check text bg colour:
        if (textBackgroundColor != None and isinstance(textBackgroundColor, str) == False):
            __typeError__("textBackgroundColor", "str", textBackgroundColor)
    # Check bg Colour:
        if (backgroudColor != None and isinstance(backgroudColor, str) == False):
            __typeError__("backgroundColor", "str", backgroudColor)
# Set external properties
    # Set text:
        self.text: str = text
    # Set style:
        self.style: str = style
    # Set text bg colour:
        self.textBackgroundColor = textBackgroundColor
    # Set text fg colour:
        self.textForegroundColor = textForegroundColor
    # Set background colour:
        self.backgroundColor = backgroudColor

    # Parse fromdict:
        if (fromDict != None):
            self.__fromDict__(fromDict)
    # Parse raw attachment
        elif (rawAttachment != None):
            self.__fromRawAttachment__(rawAttachment)
        return

####################
# Init:
####################
    def __fromRawAttachment__(self, rawAttachment:dict[str,object]) -> None:
    # Load text:    
        self.text = rawAttachment['text']
        self.style = rawAttachment['style']
        self.textBackgroundColor = rawAttachment['textBackgroundColor']
        self.textForegroundColor = rawAttachment['textForegroundColor']
        self.backgroundColor = rawAttachment['backgroundColor']
        return


####################
# To / From dict:
####################
    def __toDict__(self) -> dict[str, object]:
        textAttachmentDict = {
            'text': self.text,
            'style': self.style,
            'textBackgroundColor': self.textBackgroundColor,
            'textForegroundColor': self.textForegroundColor,
            'backgroundColor': self.backgroundColor,
        }
        return textAttachmentDict

    def __fromDict__(self, fromDict:dict[str, object]) -> None:
    # Load text:
        self.text = fromDict['text']
    # Load style:
        self.style = fromDict['style']
    # Load text bg colour:
        self.textBackgroundColor = fromDict['textBackgroundColor']
    # Load text fg colour:
        self.textForegroundColor = fromDict['textForegroundColor']
    # Load background colour:
        self.backgroundColor = fromDict['backgroundColor']
        return