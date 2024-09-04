#!/usr/bin/env python3
"""
File: signal_recipient.py
    Handle and store a recipient of a message. SignalContact and SignalGroup are valid recipients.
"""
from typing import TypeVar, Any, Optional
import uuid
from signal_cli_api.signal_common import RecipientTypes, __type_error__
from signal_cli_api.signal_timestamp import SignalTimestamp

Self = TypeVar("Self", bound="SignalRecipient")


class SignalRecipient:
    """
    Handle and store a recipient of a message. SignalContact and SignalGroup are valid recipients.
    """
    def __init__(self,
                 from_dict: Optional[dict[str, Any]] = None,
                 recipient_type: RecipientTypes = RecipientTypes.NOT_SET,
                 ) -> None:
        """
        Initialize the recipient.
        :param from_dict: dict[str, Any]: Load from a dict provided by __to_dict__().
        :param recipient_type: RecipientTypes: The recipient type.
        """
        if not isinstance(recipient_type, RecipientTypes):
            __type_error__('recipient_type', 'RecipientTypes', recipient_type)
        self._recipient_type: RecipientTypes = recipient_type
        self._recipient_id = str(uuid.uuid4())
        self._timestamp: SignalTimestamp = SignalTimestamp(now=True)
        if from_dict is not None:
            self.__from_dict__(from_dict)
        if self._recipient_type == RecipientTypes.NOT_SET:
            raise RuntimeError("Invalid Recipient type. type = NOT_SET")

    def __eq__(self, other: Self) -> bool:
        """
        Compare 2 recipients:
        :param other: recipient.
        :return: bool: True if they are equal, False if they are not.
        """
        if isinstance(other, SignalRecipient):
            return self._recipient_id == other._recipient_id
        return False

    def __to_dict__(self) -> dict[str, Any]:
        """
        Create a JSON friendly dict of this recipient.
        :return: dict[str, Any]: The dict to provide to __from_dict__()
        """
        recipient_dict: dict[str, Any] = {
            'recipientType': self._recipient_type.value,
            'recipientId': self._recipient_id,
            'recipientTimestamp': self._timestamp.__to_dict__()
        }
        return recipient_dict

    def __from_dict__(self, from_dict: dict[str, Any]) -> None:
        """
        Load from a JSON friendly dict.
        :param from_dict: The dict provided by __to_dict__().
        :return: None
        """
        self._recipient_type = RecipientTypes(from_dict['recipientType'])
        self._recipient_id = from_dict['recipientId']
        self._timestamp = SignalTimestamp(from_dict=from_dict['recipientTimestamp'])

    def __update__(self, other: Self) -> None:
        """
        Update one recipient from another.
        :param other: SignalRecipient: The other recipient to update from.
        :return: None.
        """
        if self._timestamp > other.timestamp:
            if self._recipient_type == other.recipient_type:
                self._timestamp = other.timestamp
                self._recipient_id = other.recipient_id

###########################################
# Properties:
###########################################
    @property
    def recipient_type(self) -> RecipientTypes:
        """
        The type of recipient.
        :return: RecipientTypes
        """
        return self._recipient_type

    @property
    def recipient_id(self) -> str:
        """
        The uuid of this recipient.
        :return: str
        """
        return self._recipient_id

    @property
    def timestamp(self) -> SignalTimestamp:
        """
        The time this recipient was made.
        :return: SignalTimestamp
        """
        return self._timestamp
