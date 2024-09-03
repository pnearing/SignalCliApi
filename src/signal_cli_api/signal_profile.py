#!/usr/bin/env python3
"""
File: signal_profile.py
Store and maintain a signal profile.
"""
# pylint: disable=R0902, R0912, R0913, R0915
import logging
from typing import TypeVar, Optional, Any, Final
import os
import json
import socket

from .signal_common import (__type_error__, __socket_receive_blocking__, __socket_send__,
                            __parse_signal_response__, __check_response_for_error__)
from .signal_timestamp import SignalTimestamp
from .signal_exceptions import InvalidDataFile

# Define Self:
Self = TypeVar("Self", bound="SignalProfile")

# Constants:
NOT_ACCOUNT_PROFILE_MESSAGE: Final[str] = 'this is not the account profile, not setting property'
VALUE_ALREADY_SET_MESSAGE: Final[str] = "property already set to value"
SUCCESS_MESSAGE: Final[str] = "SUCCESS"

# Non-fatal error codes to ignore while setting properties:
NON_FATAL_ERROR_CODES: Final[list[int]] = []


class SignalProfile:
    """Class containing the profile for either a contact or the account."""

    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 contact_id: str,
                 account_path: Optional[str] = None,
                 from_dict: Optional[dict[str, Any]] = None,
                 raw_profile: Optional[dict[str, Any]] = None,
                 is_account_profile: bool = False,
                 do_load: bool = False,
                 ) -> None:
        """
        Initialize a profile object.
        :param sync_socket: socket.socket: The socket to run sync operations on.
        :param config_path: str: The full path to the signal-cli config directory.
        :param account_id: str: This account's ID.
        :param contact_id: str: The contact ID for the account that this profile is for.
        :param account_path: str: The path to this account's data directory.
        :param from_dict: Optional[dict[str, Any]]: The dict provided by __to_dict__().
        :param raw_profile: Optional[dict[str, Any]]: The dict provided by signal.
        :param is_account_profile: bool: Is this the profile for this account?
        :param do_load: bool: Try and load from disk.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__init__.__name__)
        # Check args:
        if not isinstance(sync_socket, socket.socket):
            logger.critical("Raising TypeError:")
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(config_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_id", "str", account_id)
        if not isinstance(contact_id, str):
            logger.critical("Raising TypeError:")
            __type_error__("contact_id", "str", contact_id)
        if account_path is not None and not isinstance(account_path, str):
            logger.critical("Raising TypeError:")
            __type_error__("account_path", "str", account_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            logger.critical("Raising TypeError:")
            __type_error__("from_dict", "dict", from_dict)
        if raw_profile is not None and not isinstance(raw_profile, dict):
            logger.critical("Raising TypeError:")
            __type_error__("raw_profile", "dict", raw_profile)
        if not isinstance(is_account_profile, bool):
            logger.critical("Raising TypeError:")
            __type_error__("is_account_profile", "bool", is_account_profile)
        if not isinstance(do_load, bool):
            logger.critical("Raising TypeError:")
            __type_error__("do_load", "bool", do_load)

        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        """The socket to preform sync operations on."""
        self._config_path: str = config_path
        """The full path to the signal-cli config directory."""
        self._account_id: str = account_id
        """This account's ID."""
        self._contact_id: str = contact_id
        """The contact ID of this profile, needed for locating avatar."""
        self._profile_file_path: Optional[str]
        """The full path to this profile if stored on disk. NOTE: Only the account profile is
        saved on disk."""
        if account_path is not None:
            self._profile_file_path = os.path.join(account_path, 'profile.json')
        else:
            self._profile_file_path = None
        self._from_signal: bool = False
        self._is_account_profile: bool = is_account_profile
        # Set external vars:
        self.given_name: Optional[str] = None
        self.family_name: Optional[str] = None
        self.name: str = ''
        self.about: Optional[str] = None
        self.emoji: Optional[str] = None
        self.coin_address: Optional[str] = None
        self.avatar: Optional[str] = None
        self.last_update: Optional[SignalTimestamp] = None

        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw profile:
        elif raw_profile is not None:
            self._from_signal = True
            self.__from_raw_profile__(raw_profile)
        # Do load from file:
        elif do_load:
            if os.path.exists(self._profile_file_path):
                self.__load__()
            else:
                logger.warning("Saving empty profile to disk.")
                self.__save__()
        # Find avatar:
        self.__find_avatar__()
        if self._is_account_profile:
            self.__save__()

    def __from_raw_profile__(self, raw_profile: dict[str, Any]) -> None:
        """
        Load properties from a dict provided by signal.
        :param raw_profile: dict[str, Any]: The dict to load from.
        :return: None
        """
        self.given_name = raw_profile['givenName']
        self.family_name = raw_profile['familyName']
        self.__set_name_()
        self.about = raw_profile['about']
        self.emoji = raw_profile['aboutEmoji']
        self.coin_address = raw_profile['mobileCoinAddress']
        if raw_profile['lastUpdateTimestamp'] == 0:
            self.last_update = None
        else:
            self.last_update = SignalTimestamp(timestamp=raw_profile['lastUpdateTimestamp'])
        self.__find_avatar__()

    ######################
    # To / From Dict:
    ######################

    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict for this profile.
        :return: dict[str, Any]: The dict to provide to __from_dict__().
        """
        profile_dict = {
            'givenName': self.given_name,
            'familyName': self.family_name,
            'about': self.about,
            'emoji': self.emoji,
            'coinAddress': self.coin_address,
            'avatar': self.avatar,
            'lastUpdate': None,
        }
        if self.last_update is not None:
            profile_dict['lastUpdate'] = self.last_update.__to_dict__()
        return profile_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load properties from a JSON friendly dict.
        :param from_dict: dict[str, Any]: The dict created by __to_dict__()
        :return: None
        """
        # Set properties:
        self.given_name = from_dict['givenName']
        self.family_name = from_dict['familyName']
        self.__set_name_()
        self.about = from_dict['about']
        self.emoji = from_dict['emoji']
        self.coin_address = from_dict['coinAddress']
        self.avatar = from_dict['avatar']
        self.__find_avatar__()
        if from_dict['lastUpdate'] is not None:
            self.last_update = SignalTimestamp(from_dict=from_dict['lastUpdate'])
        else:
            self.last_update = from_dict['lastUpdate']

    #####################################
    # Save / Load:
    ####################################
    def __save__(self) -> bool:
        """
        Save this profile to disk.
        :return: bool: True if successfully saved, False if not.
        :raises RuntimeError: On error opening the profile json file.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__save__.__name__)
        # Checks:
        if not self._is_account_profile:
            warning_message: str = "This isn't the account profile, not saving."
            logger.warning(warning_message)
            return False
        if self._profile_file_path is None:
            warning_message: str = "'self._profile_file_path' is None, not saving."
            logger.warning(warning_message)
            return False
        # Create json string to save:
        profile_dict: dict[str, Any] = self.__to_dict__()
        profile_json: str = json.dumps(profile_dict, indent=4)
        # Open the file:
        try:
            with open(self._profile_file_path, 'w', encoding='utf-8') as file_handle:
                file_handle.write(profile_json)
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message: str = (f"Couldn't open '{self._profile_file_path}' for "
                                  f"writing: {str(e.args)}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message) from e
        return True

    def __load__(self) -> bool:
        """
        Load this profile from disk.
        :return: bool: True this was successfully loaded, False it was not.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__load__.__name__)

        # Do checks:
        if not self._is_account_profile:
            warning_message: str = "This is not the account profile, not loading."
            logger.warning(warning_message)
            return False
        if self._profile_file_path is None:
            warning_message: str = "'self._profile_file_path' is None, not loading."
            logger.warning(warning_message)
            return False
        # Try to open file:
        try:
            with open(self._profile_file_path, 'r', encoding='utf-8') as file_handle:
                profile_dict: dict[str, object] = json.loads(file_handle.read())
        except (OSError, FileNotFoundError, PermissionError) as e:
            error_message: str = (f"Couldn't open file '{self._profile_file_path}' for "
                                  f"reading: {str(e.args)}")
            logger.critical("Raising RuntimeError(%s).", error_message)
            raise RuntimeError(error_message) from e
        except json.JSONDecodeError as e:
            error_message: str = f"Couldn't load json from '{self._profile_file_path}': {e.msg}"
            logger.critical("Raising InvalidDataFile(%s).", error_message)
            raise InvalidDataFile(error_message, e, self._profile_file_path) from e
        # Load from dict:
        self.__from_dict__(profile_dict)
        return True

    #######################
    # Helper methods:
    #######################
    def __find_avatar__(self) -> bool:
        """
        Find the avatar file for this profile.
        :return: bool: True if the avatar was found, False if not.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.__find_avatar__.__name__)

        # Check if avatar already exists:
        if self.avatar is not None:
            if os.path.exists(self.avatar):
                return True
            warning_message: str = ("Current avatar points to non-existent file, searching "
                                    "for new avatar.")
            logger.warning(warning_message)
            self.avatar = None

        # Try profile avatar:
        avatar_filename = 'profile-' + self._contact_id
        avatar_file_path = os.path.join(self._config_path, 'avatars', avatar_filename)
        if os.path.exists(avatar_file_path):
            self.avatar = avatar_file_path
            return True

        # Try contact avatar:
        avatar_filename = 'contact-' + self._contact_id
        avatar_file_path = os.path.join(self._config_path, 'avatars', avatar_filename)
        if os.path.exists(avatar_file_path):
            self.avatar = avatar_file_path
            return True
        # Avatar was not found:
        return False

    def __set_name_(self) -> None:
        """
        Set the name property from the given name and family name properties.
        :return: None
        """
        if self.given_name is None and self.family_name is None:
            self.name = ''
        elif self.given_name is not None and self.family_name is not None:
            self.name = ' '.join([self.given_name, self.family_name])
        elif self.given_name is not None:
            self.name = self.given_name
        elif self.family_name is not None:
            self.name = self.family_name

    def __update__(self, other: Self) -> None:
        """
        Update this profile from another given profile.
        :param other: SignalProfile: The profile to update from.
        :return: None
        """
        # If other is older than self, do nothing.
        if other.last_update is not None and self.last_update is not None:
            if other.last_update < self.last_update:
                return
        self.given_name = other.given_name
        self.family_name = other.family_name
        self.about = other.about
        self.emoji = other.emoji
        self.coin_address = other.coin_address
        if other.last_update is not None:
            self.last_update = other.last_update
        if self._is_account_profile:
            self.__save__()

    ###############################
    # Setters:
    ###############################
    def set_given_name(self, value: str) -> tuple[bool, str]:
        """
        Set the given name for the account profile.
        :param value: str: The value to set the given name to.
        :returns: tuple[bool, str]: The first element is True if successfully set, False if not.
            The second element is the string "SUCCESS" if successfully set, otherwise it will
            contain an error message stating what went wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If Signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_given_name.__name__)
        # Type check value:
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this isn't the account profile, we can't update, so do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE

        # If given name is already set, do nothing:
        if self.given_name == value:
            return False, VALUE_ALREADY_SET_MESSAGE

        # Create set given name object and json command string:
        set_given_name_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "given_name": value,
            }
        }

        json_command_str: str = json.dumps(set_given_name_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal error while setting profile given name. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.given_name = value
        return True, SUCCESS_MESSAGE

    def set_family_name(self, value: str) -> tuple[bool, str]:
        """
        Set the family name for the account profile.
        :param value: str: The value to set the family name to.
        :returns: tuple[bool, str]: The first element is True or False for success or failure.
            The second element will be the string "SUCCESS" on success, or a message describing
            what went wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If Signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_family_name.__name__)
        # Type check value:
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this isn't the account profile, do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE
        if self.family_name == value:
            return False, VALUE_ALREADY_SET_MESSAGE
        # Create command object and json command string:
        set_family_name_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "family_name": value,
            }
        }
        json_command_str: str = json.dumps(set_family_name_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal error while setting profile family name. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.family_name = value
        return True, SUCCESS_MESSAGE

    def set_about(self, value: str) -> tuple[bool, str]:
        """
        Set the 'about' for the account profile.
        :param value: str: The value to set the 'about' to.
        :returns: tuple[bool, str]: The first element is True or False for success or failure.
            The second element is either the string "SUCCESS" on success or a message stating what
            went wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_about.__name__)
        # Type check value:
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this is not the account profile, do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE
        # If about is already set to value, do nothing:
        if self.about == value:
            return False, VALUE_ALREADY_SET_MESSAGE
        # Create command object and json command string:
        set_about_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "about": value,
            }
        }
        json_command_str: str = json.dumps(set_about_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal error while setting profile about. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.about = value
        return True, SUCCESS_MESSAGE

    def set_emoji(self, value: str) -> tuple[bool, str]:
        """
        Set the emoji for the account profile.
        :param value: str: The value to set the emoji to.
        :returns: tuple[bool, str]: The first element is True or False for success or failure.
            The second element is the string "SUCCESS" on success or a message stating what went
            wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_emoji.__name__)
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this is not the account profile, do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE
        # If emoji is already set to value, do nothing:
        if self.emoji == value:
            return False, VALUE_ALREADY_SET_MESSAGE

        # Create command object and json command string:
        set_emoji_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "aboutEmoji": value,
            }
        }
        json_command_str: str = json.dumps(set_emoji_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal returned an error while setting profile emoji. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.emoji = value
        return True, SUCCESS_MESSAGE

    def set_coin_address(self, value: str) -> tuple[bool, str]:
        """
        Set the mobile coin address.
        :param value: str: The value to set the mobile coin address to.
        :returns: tuple[bool, str]: The first element is True or False for success or failure.
            The second element is either the string "SUCCESS" if successful, or a message stating
            what went wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_coin_address.__name__)
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this isn't the account profile, do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE
        # If the value is already set, do nothing:
        if self.coin_address == value:
            return False, VALUE_ALREADY_SET_MESSAGE

        # Create command object and json command string:
        set_coin_address_command_obj = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "mobileCoinAddress": value,
            }
        }
        json_command_str: str = json.dumps(set_coin_address_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal error occurred while setting profile coin address. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.coin_address = value
        return True, SUCCESS_MESSAGE

    def set_avatar(self, value: str) -> tuple[bool, str]:
        """
        Set the avatar for the account profile.
        :param value: str: The path to the image to set the avatar to.
        :returns: tuple[bool, str]: The first element is True or False for success or failure.
            The second element is either the string "SUCCESS" on success or a message stating
            what went wrong.
        :raises TypeError: If value is not a string.
        :raises SignalError: If Signal returns an error.
        """
        # Setup logging:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.set_avatar.__name__)
        # Type check value:
        if not isinstance(value, str):
            logger.critical("Raising TypeError:")
            __type_error__("value", "str", value)
        # If this isn't the account profile, do nothing:
        if not self._is_account_profile:
            return False, NOT_ACCOUNT_PROFILE_MESSAGE
        # If avatar already set to value, do nothing:
        if self.avatar == value:
            return False, VALUE_ALREADY_SET_MESSAGE
        # Create command object and json command string:
        set_avatar_command_obj = {
            "jsonrpc": "2.0",
            "contact_id": 2,
            "method": "updateProfile",
            "params": {
                "account": self._account_id,
                "avatar": value,
            }
        }
        json_command_str: str = json.dumps(set_avatar_command_obj) + '\n'

        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str: str = __socket_receive_blocking__(self._sync_socket)
        response_obj: dict[str, Any] = __parse_signal_response__(response_str)

        # Check for error:
        error_occurred, signal_code, signal_message = __check_response_for_error__(
            response_obj, NON_FATAL_ERROR_CODES)
        if error_occurred:
            error_message: str = (f"signal error while setting profile avatar. "
                                  f"Code: {signal_code}, Message: {signal_message}")
            logger.warning(error_message)
            return False, error_message

        # Set the property
        self.avatar = value
        return True, SUCCESS_MESSAGE
