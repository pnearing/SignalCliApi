#!/usr/bin/env python3

from typing import Optional, Iterator, Iterable
import sys
import os
import json
from .signalCommon import __type_error__

DEBUG: bool = False


#############################################################################################
class Sticker(object):
    """Sticker object."""

    def __init__(self,
                 pack_id: str,
                 pack_path: str,
                 from_dict: Optional[dict[str, object]] = None,
                 from_manifest: Optional[dict[str, str]] = None,
                 sticker_id: Optional[int] = None,
                 emoji: Optional[str] = None,
                 file_path: Optional[str] = None,
                 content_type: Optional[str] = None,
                 ) -> None:
        # Argument checks:
        if not isinstance(pack_id, str):
            __type_error__("pack_id", "str", pack_id)
        if not isinstance(pack_path, str):
            __type_error__("pack_path", "str", pack_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        if from_manifest is not None and not isinstance(from_manifest, dict):
            __type_error__("from_manifest", "dict", from_manifest)
        if emoji is not None and not isinstance(emoji, str):
            __type_error__("emoji", "str", emoji)
        if file_path is not None and not isinstance(file_path, str):
            __type_error__("file_path", "str", file_path)
        if content_type is not None and not isinstance(content_type, str):
            __type_error__("content_type", "str", content_type)
        # Set internal vars:
        self._pack_id: str = pack_id
        self._pack_path: str = pack_path
        # Set external properties:
        self.id: int = sticker_id
        self.emoji: str = emoji
        self.file_path: str = file_path
        self.content_type: str = content_type
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from manifest file:
        elif from_manifest is not None:
            self.__from_manifest__(from_manifest)
        return

    ##########################
    # Init:
    ##########################
    def __from_manifest__(self, from_manifest: dict[str, str]) -> None:
        self.id = from_manifest['id']
        self.emoji = from_manifest['emoji']
        file_name = from_manifest['file']
        self.file_path = os.path.join(self._pack_path, file_name)
        self.content_type = from_manifest['contentType']
        return

    #######################
    # Overrides:
    #######################
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Sticker):
            if self.id is not None and __o.id is not None:
                if self.id == __o.id:
                    return True
        return False

    def __str__(self) -> str:
        sticker_string = "%s:%i" % (self._pack_id, self.id)
        return sticker_string

    #######################
    # To / From Dict:
    #######################
    def __to_dict__(self) -> dict[str, object]:
        sticker_dict = {
            "_packId": self._pack_id,
            "contactId": self.id,
            "emoji": self.emoji,
            "filePath": self.file_path,
            "contentType": self.content_type
        }
        return sticker_dict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        self._pack_id = from_dict['_packId']
        self.id = from_dict['contactId']
        self.emoji = from_dict['emoji']
        self.file_path = from_dict['filePath']
        self.content_type = from_dict['contentType']
        return


#############################################################################################
class StickerPack(object):
    """Sticker Pack object."""

    def __init__(self,
                 pack_id: str,
                 pack_path: str,
                 from_dict: Optional[dict[str, object]] = None,
                 from_manifest: Optional[dict[str, object]] = None,
                 title: Optional[str] = None,
                 author: Optional[str] = None,
                 cover: Optional[Sticker] = None,
                 stickers: Optional[Iterable[Sticker]] = None,
                 ) -> None:
        # Argument checks:
        if isinstance(pack_id, str):
            __type_error__("pack_id", "str", pack_id)
        if isinstance(pack_path, str):
            __type_error__("pack_path", "str", pack_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        if from_manifest is not None and not isinstance(from_manifest, dict):
            __type_error__("from_manifest", "dict", from_manifest)
        if title is not None and not isinstance(title, str):
            __type_error__("title", "str", title)
        if author is not None and not isinstance(author, str):
            __type_error__("author", "str", author)
        if cover is not None and not isinstance(cover, Sticker):
            __type_error__("cover", "Sticker", cover)
        sticker_list: list[Sticker] = []
        if stickers is not None and not isinstance(stickers, Iterable):
            __type_error__("stickers", "Iterable[Sticker]", stickers)
        elif stickers is not None:
            for i, sticker in enumerate(stickers):
                if not isinstance(sticker, Sticker):
                    __type_error__("stickers[%i]" % i, "Sticker", sticker)
                sticker_list.append(sticker)
        # Set internal Vars:
        self._pack_path: str = pack_path
        # Set external properties:
        self.pack_id: str = pack_id
        self.title: str = title
        self.author: str = author
        self.cover: Sticker = cover
        self.stickers: list[Sticker] = sticker_list
        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from Manifest:
        elif from_manifest is not None:
            self.__from_manifest__(from_manifest)
        return

    ########################
    # Init:
    ########################
    def __from_manifest__(self, manifest_dict: dict[str, object]) -> None:
        self.title = manifest_dict['title']
        self.author = manifest_dict['author']
        self.cover = Sticker(pack_id=self.pack_id, pack_path=self._pack_path, from_manifest=manifest_dict['cover'])
        self.stickers = []
        for sticker_dict in manifest_dict['stickers']:
            sticker = Sticker(pack_id=self.pack_id, pack_path=self._pack_path, from_manifest=sticker_dict)
            self.stickers.append(sticker)
        return

    #####################
    # Overrides:
    #####################
    def __getitem__(self, index: str | int) -> Sticker:
        if isinstance(index, str):
            for sticker in self.stickers:
                if sticker.emoji == index:
                    return sticker
            raise IndexError("index %s not found" % index)
        elif isinstance(index, int):
            return self.stickers[index]
        else:
            raise TypeError("index must be of type str or int")

    def __iter__(self) -> Iterator[Sticker]:
        return iter(self.stickers)

    ####################
    # To / From Dict:
    ####################
    def __to_dict__(self) -> dict:
        sticker_pack_dict = {
            'packId': self.pack_id,
            'title': self.title,
            'author': self.author,
            'cover': None,
            'stickers': [],
        }
        if self.cover is not None:
            sticker_pack_dict['cover'] = self.cover.__to_dict__()
        for sticker in self.stickers:
            sticker_pack_dict['stickers'].append(sticker.__to_dict__())
        return sticker_pack_dict

    def __from_dict__(self, from_dict: dict[str, object]) -> None:
        self.pack_id = from_dict['packId']
        self.title = from_dict['title']
        self.author = from_dict['author']
        if from_dict['cover'] is not None:
            self.cover = Sticker(pack_id=self.pack_id, pack_path=self._pack_path, from_dict=from_dict['cover'])
        else:
            self.cover = None
        self.stickers = []
        for stickerDict in from_dict['stickers']:
            self.stickers.append(Sticker(pack_id=self.pack_id, pack_path=self._pack_path, from_dict=stickerDict))
        return

    #######################
    # Getters:
    #######################
    def get_by_id(self, sticker_id: int) -> Optional[Sticker]:
        """
        Get a sticker given the sticker id.
        :param sticker_id: int: The sticker id to get.
        :returns: Optional[Sticker]: The sticker, or None if not found.
        :raises: TypeError: If sticker_id not an int.
        """
        if not isinstance(sticker_id, int):
            __type_error__("sticker_id", "int", sticker_id)
        for sticker in self.stickers:
            if sticker.id == sticker_id:
                return sticker
        return None


#############################################################################################
class StickerPacks(object):
    """Object for sticker packs."""

    def __init__(self,
                 config_path: str,
                 ) -> None:
        # Argument check:
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        # Set internal vars:
        self._config_path = config_path
        # Set external properties:
        self.packs: list[StickerPack] = []
        # Load Known sticker packs:
        self.__load__()
        if DEBUG and len(self.packs) == 0:
            warningMessage = "WARNING: No stickers loaded, sending stickers will be disabled until they are received."
            print(warningMessage, file=sys.stderr)
        return

    ##################
    # Load:
    ##################
    def __load__(self) -> None:
        # Verify stickers path exists:
        stickers_path = os.path.join(self._config_path, 'stickers')
        if not os.path.exists(stickers_path):
            if DEBUG:
                error_message = "FATAL: sticker path '%s' doesn't exist." % stickers_path
                print(error_message, file=sys.stderr)
            return
        # Get the pack contact_id's and verify len is not 0:
        pack_ids: list[str] = os.listdir(stickers_path)
        if len(pack_ids) == 0:
            if DEBUG:
                error_message = "FATAL: no stickers syncronized."
                print(error_message, file=sys.stderr)
            return
        # Load the manifest files from the sticker packs:
        self.packs = []
        for pack_id in pack_ids:
            pack_path = os.path.join(stickers_path, pack_id)
            manifest_path = os.path.join(pack_path, 'manifest.json')
            # Try to open the file:
            try:
                fileHandle = open(manifest_path, 'r')
            except Exception as err:
                if DEBUG:
                    error_message = "FATAL: Unable to open manifest file '%s' for reading: %s" % (
                        manifest_path, str(err.args))
                    print(error_message, file=sys.stderr)
                continue
            # Try to load the json from the file:
            try:
                manifest_dict: dict[str, object] = json.loads(fileHandle.read())
            except json.JSONDecodeError as err:
                if DEBUG:
                    error_message = "FATAL: Couldn't load json from '%s': %s" % (manifest_path, err.msg)
                    print(error_message, file=sys.stderr)
                continue
            # Close the file and load the pack:
            fileHandle.close()
            pack = StickerPack(pack_id=pack_id, pack_path=pack_path, from_manifest=manifest_dict)
            self.packs.append(pack)
        return

    ###########################
    # Helpers:
    ###########################
    def __update__(self) -> None:
        # Verify stickers path exists:
        stickers_path = os.path.join(self._config_path, 'stickers')
        if not os.path.exists(stickers_path):
            if DEBUG:
                error_message = "DEBUG: sticker path '%s' doesn't exist." % stickers_path
                print(error_message, file=sys.stderr)
            return
        # Get the pack contact_id's and verify len is not 0:
        pack_ids: list[str] = os.listdir(stickers_path)
        if len(pack_ids) == 0:
            error_message = "FATAL: no stickers synchronized"
            raise RuntimeError(error_message)
        # Check to see if there is a new contact_id:
        known_pack_ids = [pack.pack_id for pack in self.packs]  # Gather old contact_id's
        for pack_id in pack_ids:
            if pack_id not in known_pack_ids:
                pack_path = os.path.join(stickers_path, pack_id)
                manifest_path = os.path.join(pack_path, 'manifest.json')
                # Try to open the file:
                try:
                    fileHandle = open(manifest_path, 'r')
                except Exception as err:
                    if DEBUG:
                        error_message = "DEBUG: Unable to open manifest file '%s' for reading: %s" % (
                            manifest_path, str(err.args))
                        print(error_message, file=sys.stderr)
                    continue
                # Try to load the json from the file:
                try:
                    manifestDict: dict[str, object] = json.loads(fileHandle.read())
                except json.JSONDecodeError as err:
                    if DEBUG:
                        error_message = "DEBUG: Couldn't load json from '%s': %s" % (manifest_path, err.msg)
                        print(error_message, file=sys.stderr)
                    continue
                # Close the file and load the pack:
                fileHandle.close()
                pack = StickerPack(pack_id=pack_id, pack_path=pack_path, from_manifest=manifestDict)
                self.packs.append(pack)
        return

    ########################
    # Getters:
    ########################
    def get_pack_by_name(self, name: str) -> Optional[StickerPack]:
        """
        Get sticker pack by name.
        :param: str: name: The name to search for.
        :returns: Optional[StickerPack]: The sticker pack, or None if not found.
        :raises: TypeError: If name not a string.
        """
        if not isinstance(name, str):
            __type_error__("name", "str", name)
        for pack in self.packs:
            if pack.title == name:
                return pack
        return None

    def get_pack_by_id(self, pack_id: str) -> Optional[StickerPack]:
        """
        Get sticker pack by pack id.
        :param: str: pack_id: The pack id to search for.
        :returns: Optional[StickerPack]
        :raises: TypeError: If pack_id is not a string.
        """
        if not isinstance(pack_id, str):
            __type_error__("pack_id", "str", pack_id)
        for pack in self.packs:
            if pack.pack_id == pack_id:
                return pack
        return None

    def get_sticker(self, pack_id: str, sticker_id: int) -> Optional[Sticker]:
        """
        Get a sticker, given pack id, and sticker id.
        :param: str: pack_id: The pack id of the sticker.
        :param: int: sticker_id: The sticker id of the sticker.
        :returns: Optional[Sticker]
        :raises: TypeError: If pack_id not a string, or if sticker_id not an int.
        """
        if not isinstance(pack_id, str):
            __type_error__("pack_id", "str", pack_id)
        if not isinstance(sticker_id, int):
            __type_error__("sticker_id", "int", sticker_id)
        pack = self.get_pack_by_id(pack_id)
        if pack is None:
            return None
        return pack.get_by_id(sticker_id)

