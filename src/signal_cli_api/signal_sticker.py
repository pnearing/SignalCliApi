#!/usr/bin/env python3
"""
File: signal_sticker.py
Handle and manage stickers and sticker packs.
"""
import logging
from typing import Optional, Iterator, Any
import os
import json
from .signal_common import __type_error__, STICKER_MANIFEST_FILENAME
from .signal_exceptions import InvalidDataFile


#############################################################################################
class SignalSticker:
    """
    SignalSticker object.
    """
    def __init__(self,
                 pack_id: str,
                 pack_path: str,
                 from_dict: Optional[dict[str, Any]] = None,
                 from_manifest: Optional[dict[str, str | int]] = None,
                 ) -> None:
        """
        Initialize a SignalSticker object.
        :param pack_id: str: The pack ID.
        :param pack_path: str: The full path to the pack directory.
        :param from_dict: Optional[dict[str, Any]]: Load this sticker from a dict provided
            by __to_dict__().
        :param from_manifest: Optional[dict[str, str]]: Load this sticker from a manifest file.
        :raises TypeError: If any of the properties are of the wrong type.
        :raises FileNotFoundError: If 'pack_path', or 'file_path' does not exist.
        :raises NotADirectoryError: If 'pack_path' is not a directory.
        :raises ValueError: If 'file_path' is not a regular file.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Type checks:
        if not isinstance(pack_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_id", "str", pack_id)
        if not isinstance(pack_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_path", "str", pack_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "Optional[dict[str, Any]]", from_dict)
        if from_manifest is not None and not isinstance(from_manifest, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_manifest", "Optional[dict[str, str]]", from_manifest)

        # Value check params:
        if not os.path.exists(pack_path):
            error_message: str = f"'pack_path': '{pack_path}', does not exist."
            logger.critical("Raising FileNotFoundError(%s).", error_message)
            raise FileNotFoundError(error_message)
        if not os.path.isdir(pack_path):
            error_message: str = f"'pack_path': '{pack_path}', is not a directory."
            logger.critical("Raising NotADirectoryError(%s).", error_message)
            raise NotADirectoryError(error_message)

        # Set internal vars:
        self._pack_id: str = pack_id
        """The pack ID."""
        self._pack_path: str = pack_path
        """The full path to the pack directory."""

        # Set external properties:
        self.id: int = -1
        """This stickers ID."""
        self.emoji: Optional[str] = None
        """The emoji related to this sticker."""
        self.file_path: str = ''
        """The full path to the image file of this sticker."""
        self.content_type: str = ''
        """The Content-Type of the file_path."""

        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from manifest file:
        elif from_manifest is not None:
            self.__from_manifest__(from_manifest)

        # Value check self.file_path
        if not os.path.exists(self.file_path):
            error_message: str = f"'self.file_path': {self.file_path}, does not exist."
            logger.critical("Raising FileNotFoundError(%s).", error_message)
            raise FileNotFoundError(error_message)
        if not os.path.isfile(self.file_path):
            error_message: str = f"'self.file_path': '{self.file_path}', is not a regular file."
            logger.critical("Raising ValueError(%s).", error_message)
            raise ValueError(error_message)

    ##########################
    # Init:
    ##########################
    def __from_manifest__(self, from_manifest: dict[str, str | int]) -> None:
        self.id = from_manifest['id']
        self.emoji = from_manifest['emoji']
        self.file_path = os.path.join(self._pack_path, from_manifest['file'])
        self.content_type = from_manifest['contentType']

    #######################
    # Overrides:
    #######################
    def __eq__(self, other) -> bool:
        """
        Compare equality between two stickers.
        :param other: SignalSticker: The sticker to compare to.
        :return: bool: True if equal, False if not.
        :raises TypeError: If 'other' is not a SignalSticker object.
        """
        if isinstance(other, type(self)):
            if self.id == other.id:
                return True
        return False

    def __str__(self) -> str:
        """
        String representation of the sticker.
        :return: str: The string representation of the sticker.
        """
        return f"{self.pack_id}:{self.id}"

    #######################
    # To / From Dict:
    #######################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Save properties from a JSON friendly dict.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        sticker_dict: dict[str, Any] = {
            "_packId": self._pack_id,
            "contactId": self.id,
            "emoji": self.emoji,
            "filePath": self.file_path,
            "contentType": self.content_type
        }
        return sticker_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        self._pack_id = from_dict['_packId']
        self.id = from_dict['contactId']
        self.emoji = from_dict['emoji']
        self.file_path = from_dict['filePath']
        self.content_type = from_dict['contentType']

    @property
    def pack_id(self) -> str:
        """
        The pack ID.
        Getter.
        :return: str: The pack ID. 
        """
        return self._pack_id


#############################################################################################
class SignalStickerPack:
    """
    SignalSticker Pack object.
    """
    def __init__(self,
                 pack_id: str,
                 pack_path: str,
                 from_dict: Optional[dict[str, Any]] = None,
                 from_manifest: Optional[dict[str, Any]] = None,
                 ) -> None:
        """
        Initialize a SignalStickerPack object.
        :param pack_id: str: The pack ID.
        :param pack_path: st: The full path to the pack directory.
        :param from_dict: Optional[dict[str, Any]]: Load properties from a dict created
            by __to_dict__().
        :param from_manifest: Optional[dict[str, Any]]: Load properties from a manifest
            dict provided by signal.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Argument checks:
        if not isinstance(pack_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_id", "str", pack_id)
        if not isinstance(pack_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_path", "str", pack_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if from_manifest is not None and not isinstance(from_manifest, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_manifest", "dict", from_manifest)

        # Set internal Vars:
        self._pack_path: str = pack_path
        """The full path to the pack directory."""

        # Set external properties:
        self.pack_id: str = pack_id
        """The pack ID of this pack."""
        self.title: str = ''
        """The title of this pack."""
        self.author: str = ''
        """The author of the sticker pack."""
        self.cover: Optional[SignalSticker] = None
        """The cover SignalSticker object."""
        self.stickers: list[SignalSticker] = []

        # Parse from_dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from Manifest:
        elif from_manifest is not None:
            self.__from_manifest__(from_manifest)

    ########################
    # Init:
    ########################
    def __from_manifest__(self, manifest_dict: dict[str, Any]) -> None:
        """
        Load properties from a manifest dict.
        :param manifest_dict: dict[str, Any]: The dict to load from.
        :return: None
        """
        self.title = manifest_dict['title']
        self.author = manifest_dict['author']
        self.stickers = []
        for sticker_manifest in manifest_dict['stickers']:
            sticker = SignalSticker(pack_id=self.pack_id, pack_path=self._pack_path,
                                    from_manifest=sticker_manifest)
            self.stickers.append(sticker)
        self.cover = self.get_by_id(manifest_dict['cover']['id'])

    #####################
    # Overrides:
    #####################
    def __getitem__(self, index: str | int) -> SignalSticker:
        """
        Index the SignalStickerPack with square brackets.
        :param index: int | str: If index is of type str, then the emoji property is searched,
            otherwise if index is of type int, then the SignalStickerPack is indexed as a list.
        :raises IndexError: If index is of type str, then the emoji was not found, otherwise, if
            index is of type int, the index is out of range.
        :return: SignalSticker: The sicker found.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__getitem__.__name__)
        # If index is a str, search emoji:
        if isinstance(index, str):
            for sticker in self.stickers:
                if sticker.emoji == index:
                    return sticker
            raise IndexError(f"index {index} not found")
        # Otherwise, if index is an int, index as a list:
        if isinstance(index, int):
            return self.stickers[index]
        # Wrong index type:
        error_message: str = "index must be of type str or int"
        logger.critical("Raising TypeError(%s).", error_message)
        raise TypeError(error_message)

    def __iter__(self) -> Iterator[SignalSticker]:
        """
        Iterate over the stickers.
        :return: Iterator[SignalSticker]: The iterator.
        """
        return iter(self.stickers)

    def __len__(self) -> int:
        """
        The len of the stickers.
        :return: int: The number of stickers.
        """
        return len(self.stickers)

    ####################
    # To / From Dict:
    ####################
    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict for this sticker pack.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        sticker_pack_dict: dict[str, Any] = {
            'packId': self.pack_id,
            'title': self.title,
            'author': self.author,
            'cover': None,
            'stickers': [],
        }
        if self.cover is not None:
            sticker_pack_dict['cover'] = self.cover.id
        for sticker in self.stickers:
            sticker_pack_dict['stickers'].append(sticker.__to_dict__())
        return sticker_pack_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict provided by __to_dict__().
        :return: None
        """
        self.pack_id = from_dict['packId']
        self.title = from_dict['title']
        self.author = from_dict['author']
        self.stickers = []
        for sticker_dict in from_dict['stickers']:
            self.stickers.append(SignalSticker(pack_id=self.pack_id, pack_path=self._pack_path,
                                               from_dict=sticker_dict))
        if from_dict['cover'] is not None:
            self.cover = self.get_by_id(from_dict['cover'])

    #######################
    # Getters:
    #######################
    def get_by_id(self, sticker_id: int) -> Optional[SignalSticker]:
        """
        Get a sticker given the sticker id.
        :param sticker_id: int: The sticker id to get.
        :returns: Optional[SignalSticker]: The sticker, or None if not found.
        :raises: TypeError: If sticker_id not an int.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_by_id.__name__)
        # Type checks:
        if not isinstance(sticker_id, int):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_id", "int", sticker_id)
        # Search for sticker and return it.
        for sticker in self.stickers:
            if sticker.id == sticker_id:
                return sticker
        # No sticker found:
        return None


#############################################################################################
class SignalStickerPacks:
    """
    Object for storing multiple sticker packs.
    """
    def __init__(self,
                 config_path: str,
                 ) -> None:
        """
        Initialize the SignalStickerPacks object.
        :param config_path: str: The full path to the signal-cli config directory.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)

        # Argument check:
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)

        # Set internal vars:
        self._stickers_path = os.path.join(config_path, 'stickers')
        """The full path to the stickers directory."""

        # Set external properties:
        self.packs: list[SignalStickerPack] = []
        """A list of known SignalStickerPacks."""

        # Load Known sticker packs:
        self.__load__()
        if len(self.packs) == 0:
            warning_message: str = ("No stickers loaded, sending stickers will be disabled"
                                    "until they are received.")
            logger.warning(warning_message)

    ##################
    # Helper methods:
    ##################
    def __check_sticker_path__(self) -> tuple[bool, str]:
        """
        Check to see if the self._sticker_path exists, and is a directory.
        :return: tuple[bool, str]: The first element is True or False, based on success or failure.
            The second element is either the string "SUCCESS" on success or an error message
            on failure.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__check_sticker_path__.__name__)

        # Verify stickers' path exists:
        if not os.path.exists(self._stickers_path):
            warning_message: str = f"SignalSticker path '{self._stickers_path}', does not exist."
            logger.warning(warning_message)
            return False, warning_message

        # Verify stickers' path is a directory:
        if not os.path.isdir(self._stickers_path):
            warning_message: str = f"Stickers path '{self._stickers_path}', is not a directory."
            logger.warning(warning_message)
            return False, warning_message

        # Everything is okay:
        return True, 'SUCCESS'

    def __load_manifest_file__(self, manifest_path: str) -> Optional[dict[str, Any]]:
        """
        load a manifest file returning the manifest dict.
        :param manifest_path: str: The full path to the manifest file.
        :return: dict[str, Any]: The manifest dict.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' +
                                                   self.__load_manifest_file__.__name__)
        # Try to load the file:
        try:
            with open(manifest_path, 'r', encoding='utf-8') as file_handle:
                manifest_dict: dict[str, Any] = json.loads(file_handle.read())
        except (OSError, FileNotFoundError, PermissionError) as e:
            warning_message: str = f"Failed to open '{manifest_path}' for reading: {str(e.args)}"
            logger.warning(warning_message)
            return None
        except json.JSONDecodeError as e:
            error_message: str = f"couldn't load JSON from '{manifest_path}': {e.msg}"
            logger.critical("Raising InvalidDataFile(%s).", error_message)
            raise InvalidDataFile(error_message, e, manifest_path) from e
        return manifest_dict

    ##################
    # Load:
    ##################
    def __load__(self) -> bool:
        """
        Load the sticker packs from disk
        :return: bool: True stickers were loaded, False they were not.
        :raises InvalidDataFile: On error loading JSON from a manifest file.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__load__.__name__)

        # Verify the stickers' path:
        valid, message = self.__check_sticker_path__()
        if not valid:
            logger.warning("Stickers path is not valid: %s", message)
            return False

        # Get the pack contact_id's and verify len is not 0:
        pack_ids: list[str] = os.listdir(self._stickers_path)
        if len(pack_ids) == 0:
            warning_message: str = "No stickers synchronized."
            logger.warning(warning_message)
            return False

        # Load the manifest files from the sticker packs:
        self.packs = []
        for pack_id in pack_ids:
            # Build the manifest path:
            pack_path: str = os.path.join(self._stickers_path, pack_id)
            manifest_path: str = os.path.join(pack_path, STICKER_MANIFEST_FILENAME)

            # Load the manifest file:
            manifest_dict: Optional[dict[str, Any]] = self.__load_manifest_file__(manifest_path)
            if manifest_dict is None:
                warning_message: str = f"failed to load '{manifest_path}', skipping."
                logger.warning(warning_message)
                continue

            # Create the pack, and store it:
            pack = SignalStickerPack(pack_id=pack_id, pack_path=pack_path,
                                     from_manifest=manifest_dict)
            self.packs.append(pack)
        return True

    ###########################
    # Helpers:
    ###########################
    def __update__(self) -> bool:
        """
        Update the SignalSticker Packs from disk.
        :return: bool: True, new sticker packs were loaded, False no new sticker packs.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__update__.__name__)

        # Verify the stickers' path:
        valid, message = self.__check_sticker_path__()
        if not valid:
            logger.warning("Stickers path is not valid: %s", message)
            return False

        # Get the pack_id's and verify len is not 0:
        pack_ids: list[str] = os.listdir(self._stickers_path)
        if len(pack_ids) == 0:
            warning_message: str = "no stickers synchronized"
            logger.warning(warning_message)
            return False

        # Check to see if there is a new pack_id:
        known_pack_ids = [pack.pack_id for pack in self.packs]  # Gather current pack_id's
        for pack_id in pack_ids:
            if pack_id not in known_pack_ids:
                pack_path = os.path.join(self._stickers_path, pack_id)
                manifest_path = os.path.join(pack_path, STICKER_MANIFEST_FILENAME)
                # Try to load the file:
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as file_handle:
                        manifest_dict: dict[str, Any] = json.loads(file_handle.read())
                except (OSError, FileNotFoundError, PermissionError) as e:
                    warning_message: str = (f"Failed to open '{manifest_path}' for "
                                            f"reading: {str(e.args)}")
                    logger.warning(warning_message)
                    continue
                except json.JSONDecodeError as e:
                    error_message: str = f"Failed to load JSON from '{manifest_path}': {e.msg}"
                    logger.critical("Raising InvalidDataFile(%s).", error_message)
                    raise InvalidDataFile(error_message, e, manifest_path) from e

                # Load the pack and store it:
                pack = SignalStickerPack(pack_id=pack_id, pack_path=pack_path,
                                         from_manifest=manifest_dict)
                self.packs.append(pack)
        return True

    ########################
    # Getters:
    ########################
    def get_pack_by_name(self, name: str) -> Optional[SignalStickerPack]:
        """
        Get sticker pack by name.
        :param: str: name: The name to search for.
        :returns: Optional[SignalStickerPack]: The sticker pack, or None if not found.
        :raises: TypeError: If name not a string.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_pack_by_name.__name__)

        # Type check name:
        if not isinstance(name, str):
            logger.critical("Raising TypeError:")
            __type_error__("name", "str", name)

        # Search for pack and return it:
        for pack in self.packs:
            if pack.title == name:
                return pack

        # The pack wasn't found:
        return None

    def get_pack_by_id(self, pack_id: str) -> Optional[SignalStickerPack]:
        """
        Get sticker pack by pack id.
        :param: str: pack_id: The pack id to search for.
        :returns: Optional[SignalStickerPack]
        :raises: TypeError: If pack_id is not a string.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_pack_by_id.__name__)

        # Type check pack_id:
        if not isinstance(pack_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_id", "str", pack_id)

        # Search for the pack and return it:
        for pack in self.packs:
            if pack.pack_id == pack_id:
                return pack

        # The pack wasn't found:
        return None

    def get_sticker(self, pack_id: str, sticker_id: int) -> Optional[SignalSticker]:
        """
        Get a sticker, given pack id, and sticker id.
        :param: str: pack_id: The pack id of the sticker.
        :param: int: sticker_id: The sticker id of the sticker.
        :returns: Optional[SignalSticker]: The sticker, or None if not found.
        :raises: TypeError: If pack_id is not a string, or if sticker_id is not an int.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.get_sticker.__name__)

        # Type check arguments:
        if not isinstance(pack_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("pack_id", "str", pack_id)
        if not isinstance(sticker_id, int):
            logger.critical("Raising TypeError:")
            __type_error__("sticker_id", "int", sticker_id)

        # Search for the sticker pack, and return None if not found:
        pack = self.get_pack_by_id(pack_id)
        if pack is None:
            return None

        # Search for and return the sticker, returns None if not found.
        return pack.get_by_id(sticker_id)
