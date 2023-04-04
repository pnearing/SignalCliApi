#!/usr/bin/env python3
"""File: signalProfile.py"""
from typing import TypeVar, Optional
import os
import json
import sys
import socket

from .signalCommon import __type_error__, __socket_receive__, __socket_send__
from .signalTimestamp import Timestamp

DEBUG: bool = False

Self = TypeVar("Self", bound="Profile")


class Profile(object):
    """Class containing the profile for either a contact or the account."""
    def __init__(self,
                 sync_socket: socket.socket,
                 config_path: str,
                 account_id: str,
                 contact_id: str,
                 account_path: Optional[str] = None,
                 from_dict: Optional[dict] = None,
                 raw_profile: Optional[dict] = None,
                 given_name: Optional[str] = None,
                 family_name: Optional[str] = None,
                 about: Optional[str] = None,
                 emoji: Optional[str] = None,
                 coin_address: Optional[str] = None,
                 avatar: Optional[str] = None,
                 last_update: Optional[Timestamp] = None,
                 is_account_profile: bool = False,
                 do_load: bool = False,
                 ) -> None:
        # Check args:
        if not isinstance(sync_socket, socket.socket):
            __type_error__("sync_socket", "socket.socket", sync_socket)
        if not isinstance(config_path, str):
            __type_error__("config_path", "str", config_path)
        if not isinstance(account_id, str):
            __type_error__("account_id", "str", account_id)
        if not isinstance(contact_id, str):
            __type_error__("contact_id", "str", contact_id)
        if account_path is not None and not isinstance(account_path, str):
            __type_error__("account_path", "str", account_path)
        if from_dict is not None and not isinstance(from_dict, dict):
            __type_error__("from_dict", "dict", from_dict)
        if raw_profile is not None and not isinstance(raw_profile, dict):
            __type_error__("raw_profile", "dict", raw_profile)
        if given_name is not None and not isinstance(given_name, str):
            __type_error__("given_name", "str", given_name)
        if family_name is not None and not isinstance(family_name, str):
            __type_error__("family_name", "str", family_name)
        if about is not None and not isinstance(about, str):
            __type_error__("about", "str", about)
        if emoji is not None and not isinstance(emoji, str):
            __type_error__("emoji", "str", emoji)
        if coin_address is not None and not isinstance(coin_address, str):
            __type_error__("coin_address", "str", coin_address)
        if avatar is not None and not isinstance(avatar, str):
            __type_error__("avatar", "str", avatar)
        if last_update is not None and not isinstance(last_update, Timestamp):
            __type_error__("last_update", "Timestamp", last_update)
        if not isinstance(is_account_profile, bool):
            __type_error__("is_account_profile", "bool", is_account_profile)
        if not isinstance(do_load, bool):
            __type_error__("do_load", "bool", do_load)
        # Set internal vars:
        self._sync_socket: socket.socket = sync_socket
        self._config_path: str = config_path
        self._account_id: str = account_id
        self._contact_id: str = contact_id
        self._profile_file_path: Optional[str]
        if account_path is not None:
            self._profile_file_path = os.path.join(account_path, 'profile.json')
        else:
            self._profile_file_path = None
        self._from_signal: bool = False
        self._is_account_profile: bool = is_account_profile
        # Set external vars:
        self.given_name: Optional[str] = given_name
        self.family_name: Optional[str] = family_name
        self.name: str = ''
        self.about: Optional[str] = about
        self.emoji: Optional[str] = emoji
        self.coin_address: Optional[str] = coin_address
        self.avatar: Optional[str] = avatar
        self.last_update: Optional[Timestamp] = last_update
        # Parse from dict:
        if from_dict is not None:
            self.__from_dict__(from_dict)
        # Parse from raw profile:
        elif raw_profile is not None:
            self._from_signal = True
            self.__from_raw_profile__(raw_profile)
        # Do load from file:
        elif do_load:
            try:
                self.__load__()
            except RuntimeError:
                if DEBUG:
                    print("INFO: Creating empty profile for account: %s" % self._account_id, file=sys.stderr)
                self.__save__()
        # Find avatar:
        self.__find_avatar__()
        if self._is_account_profile:
            self.__save__()
        return

    def __from_raw_profile__(self, raw_profile: dict) -> None:
        # print (raw_profile)
        self.given_name = raw_profile['givenName']
        self.family_name = raw_profile['familyName']
        self.__set_name__()
        self.about = raw_profile['about']
        self.emoji = raw_profile['aboutEmoji']
        self.coin_address = raw_profile['mobileCoinAddress']
        if raw_profile['lastUpdateTimestamp'] == 0:
            self.last_update = None
        else:
            self.last_update = Timestamp(timestamp=raw_profile['lastUpdateTimestamp'])
        self.__find_avatar__()
        return

    ######################
    # To / From Dict:
    ######################

    def __to_dict__(self) -> dict:
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

    def __from_dict__(self, from_dict: dict) -> None:
        # Set properties:
        self.given_name = from_dict['givenName']
        self.family_name = from_dict['familyName']
        self.__set_name__()
        self.about = from_dict['about']
        self.emoji = from_dict['emoji']
        self.coin_address = from_dict['coinAddress']
        self.avatar = from_dict['avatar']
        self.__find_avatar__()
        if from_dict['lastUpdate'] is not None:
            self.last_update = Timestamp(from_dict=from_dict['lastUpdate'])
        else:
            self.last_update = from_dict['lastUpdate']
        return

    #####################################
    # Save / Load:
    ####################################
    def __save__(self) -> bool:
        # Checks:
        if not self._is_account_profile:
            if DEBUG:
                errorMessage = "WARNING: Not account profile cannot save."
                print(errorMessage, file=sys.stderr)
            return False
        if self._profile_file_path is None:
            if DEBUG:
                errorMessage = "WARNING: File path not set, cannot save."
                print(errorMessage, file=sys.stderr)
            return False
        # Create json string to save:
        profileDict: dict = self.__to_dict__()
        profileJson: str = json.dumps(profileDict)
        # Open the file:
        try:
            fileHandle = open(self._profile_file_path, 'w')
        except Exception as e:
            errorMessage = "FATAL: Couldn't open '%s' for writing: %s" % (self._profile_file_path, str(e.args))
            raise RuntimeError(errorMessage)
        # Write to the file and close it.
        fileHandle.write(profileJson)
        fileHandle.close()
        return True

    def __load__(self) -> bool:
        # Do checks:
        if self._profile_file_path is None:
            if DEBUG:
                error_message = "WARNING: Profile file path not set, cannot load."
                print(error_message, file=sys.stderr)
            return False
        if not self._is_account_profile:
            if DEBUG:
                error_message = "WARNING: Not account profile, cannot load."
                print(error_message, file=sys.stderr)
            return False
        # Try to open file:
        try:
            file_handle = open(self._profile_file_path, 'r')
        except Exception as e:
            error_message = "FATAL: Couldn't open file '%s' for reading: %s" % (self._profile_file_path, str(e.args))
            raise RuntimeError(error_message)
        # Try to load the json:
        try:
            profile_dict: dict[str, object] = json.loads(file_handle.read())
        except json.JSONDecodeError as e:
            error_message = "FATAL: Couldn't load json from '%s': %s" % (self._profile_file_path, e.msg)
            raise RuntimeError(error_message)
        # Load from dict:
        self.__from_dict__(profile_dict)
        return True

    #######################
    # Helper methods:
    #######################
    def __find_avatar__(self) -> bool:
        if self.avatar is not None:
            if not os.path.exists(self.avatar):
                if DEBUG:
                    errorMessage = "WARNING: Couldn't find avatar: '%s', searching..." % self.avatar
                    print(errorMessage, file=sys.stderr)
                self.avatar = None
        # Try profile avatar:
        if self.avatar is None:
            avatarFileName = 'profile-' + self._contact_id
            avatarFilePath = os.path.join(self._config_path, 'avatars', avatarFileName)
            if os.path.exists(avatarFilePath):
                self.avatar = avatarFilePath
        # Try contact avatar:
        if self.avatar is None:
            avatarFileName = 'contact-' + self._contact_id
            avatarFilePath = os.path.join(self._config_path, 'avatars', avatarFileName)
            if os.path.exists(avatarFilePath):
                self.avatar = avatarFilePath
        if self.avatar is not None:
            return True
        return False

    def __set_name__(self) -> None:
        if self.given_name is None and self.family_name is None:
            self.name = ''
        elif self.given_name is not None and self.family_name is not None:
            self.name = ' '.join([self.given_name, self.family_name])
        elif self.given_name is not None:
            self.name = self.given_name
        elif self.family_name is not None:
            self.name = self.family_name
        return

    def __merge__(self, __o: Self) -> None:
        self.given_name = __o.given_name
        self.family_name = __o.family_name
        self.about = __o.about
        self.emoji = __o.emoji
        self.coin_address = __o.coin_address
        self.last_update = __o.last_update
        if self._is_account_profile:
            self.__save__()
        return

    ###############################
    # Setters:
    ###############################
    def set_given_name(self, value: str) -> bool:
        """
        Set the given name for the account profile.
        :param value: str: The value to set the given name to.
        :returns: bool: True if successfully updated, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.given_name == value:
            return False
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
        json_command_str = json.dumps(set_given_name_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # print(responseObj)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                errorMessage = "DEBUG: Signal error while setting given name. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(errorMessage, file=sys.stderr)
            return False
        # Set the property
        self.given_name = value
        return True

    def set_family_name(self, value: str) -> bool:
        """
        Set the family name for the account profile.
        :param value: str: The value to set the family name to.
        :returns: bool: True if successfully updated, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.family_name == value:
            return False
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
        json_command_str = json.dumps(set_family_name_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "DEBUG: Signal error while setting family name. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(error_message, file=sys.stderr)
            return False
        # Set the property
        self.family_name = value
        return True

    def set_about(self, value: str) -> bool:
        """
        Set the 'about' for the account profile.
        :param value: str: The value to set the 'about' to.
        :returns: bool: True if successfully updated, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.about == value:
            return False
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
        json_command_str = json.dumps(set_about_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "DEBUG: Signal error while setting about. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(error_message, file=sys.stderr)
            return False
        # Set the property
        self.about = value
        return True

    def set_emoji(self, value: str) -> bool:
        """
        Set the emoji for the account profile.
        :param value: str: The value to set the emoji to.
        :returns: bool: True if successfully set, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.emoji == value:
            return False
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
        json_command_str = json.dumps(set_emoji_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "DEBUG: Signal error while setting emoji. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(error_message, file=sys.stderr)
            return False
        # Set the property
        self.emoji = value
        return True

    def set_coin_address(self, value: str) -> bool:
        """
        Set the mobile coin address.
        :param value: str: The value to set the mobile coin address to.
        :returns: bool: True if successfully updated, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.coin_address == value:
            return False
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
        json_command_str = json.dumps(set_coin_address_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "DEBUG: Signal error while setting coin address. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(error_message, file=sys.stderr)
            return False
        # Set the property
        self.coin_address = value
        return True

    def set_avatar(self, value: str) -> bool:
        """
        Set the avatar for the account profile.
        :param value: str: The path to the image to set the avatar to.
        :returns: bool: True if successfully updated, False if not.
        :raises: TypeError: If value is not a string.
        """
        if not isinstance(value, str):
            __type_error__("value", "str", value)
        if not self._is_account_profile:
            return False
        if self.avatar == value:
            return False
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
        json_command_str = json.dumps(set_avatar_command_obj) + '\n'
        # Communicate with signal:
        __socket_send__(self._sync_socket, json_command_str)
        response_str = __socket_receive__(self._sync_socket)
        # Parse response:
        response_obj: dict[str, object] = json.loads(response_str)
        # Check for error:
        if 'error' in response_obj.keys():
            if DEBUG:
                error_message = "DEBUG: Signal error while setting avatar. Code: %i Message: %s" % (
                    response_obj['error']['code'],
                    response_obj['error']['message']
                )
                print(error_message, file=sys.stderr)
            return False
        # Set the property
        self.avatar = value
        return True
