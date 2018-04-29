# -*- coding: utf-8 -*-
"""
    maxcul
    ~~~~~~~~~~~~~~

    Implementation of moritz home automation protocol

    :copyright: (c) 2014 by Markus Ullmann.
    :license: BSD, see LICENSE for more details.
"""
# flake8: noqa

from maxcul._communication import MaxConnection
from maxcul._const import (
    # Events
    EVENT_DEVICE_PAIRED,
    EVENT_DEVICE_REPAIRED,
    EVENT_THERMOSTAT_UPDATE,
    EVENT_SHUTTER_UPDATE,
    EVENT_PUSH_BUTTON_UPDATE,
    # Thermostat modes
    MODE_AUTO, MODE_BOOST, MODE_MANUAL, MODE_TEMPORARY,
    # Temperature constants
    MIN_TEMPERATURE, MAX_TEMPERATURE,
    # Attributes of payloads
    ATTR_DEVICE_ID,
    ATTR_DESIRED_TEMPERATURE,
    ATTR_MEASURED_TEMPERATURE,
    ATTR_MODE,
    ATTR_BATTERY_LOW,
    ATTR_STATE,
)
from maxcul._exceptions import (
    MoritzError,
    UnknownMessageError,
    LengthNotMatchingError,
    MissingPayloadParameterError)

__version__ = "0.1.12"
