# -*- coding: utf-8 -*-
"""
    maxcul.messages
    ~~~~~~~~~~~~~~~~~~~~~~~

    Definition of known messages, based on IDs from FHEM plugin

    :copyright: (c) 2014 by Markus Ullmann.
    :license: BSD, see LICENSE for more details.
"""

# environment constants

# python imports
from datetime import datetime
import struct

# environment imports

# custom imports
from maxcul._exceptions import (
    LengthNotMatchingError,
    MissingPayloadParameterError, UnknownMessageError
)
from maxcul._const import (
    CUBE, DEVICE_TYPES, DEVICE_TYPES_BY_NAME,
    MODE_IDS, BOOST_DURATION, DECALC_DAYS,
    SHUTTER_STATES
)


class MoritzMessage(object):
    """Represents (de)coded message as seen on Moritz Wire"""
    counter = 0
    sender_id = 0
    receiver_id = 0
    group_id = 0
    flag = 0
    length = 0
    raw_payload = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value

    @staticmethod
    def decode_payload(payload):
        raise NotImplementedError()

    def is_broadcast(self):
        return self.receiver_id == 0

    @staticmethod
    def decode_message(input_string):
        """Decodes given message and returns content in matching message class"""

        if input_string.startswith("Zs"):
            # outgoing messages can be parsed too, just cut the Z off as it
            # doesn't matter
            input_string = input_string[1:]

        # Split MAX message
        length = int(input_string[1:3], base=16)
        counter = int(input_string[3:5], base=16)
        flag = int(input_string[5:7], base=16)
        msgtype = int(input_string[7:9], base=16)
        sender_id = int(input_string[9:15], base=16)
        receiver_id = int(input_string[15:21], base=16)
        group_id = int(input_string[21:23], base=16)

        # Length: strlen(input_string) / 2 as HEX encoding, +3 for Z and length
        # count
        if (len(input_string) - 3) != length * 2:
            # For some reason there are two methods... and I've seen both with culfw 1.67...
            # Some say the additional character(s) are some kind of CRC,
            # currently investigating.
            if (len(input_string) - 5) == length * 2:
                input_string = input_string[:-2]
            else:
                raise LengthNotMatchingError(
                    "Message length %i not matching indicated length %i" %
                    ((len(input_string) - 3) / 2, length))

        payload = input_string[23:]

        try:
            message_class = MORITZ_MESSAGE_IDS[msgtype]
        except KeyError:
            raise UnknownMessageError(
                "Unknown message with id %x found" %
                msgtype)

        attributes = dict(
            length=length,
            counter=counter,
            flag=flag,
            group_id=group_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            raw_payload=payload
        )
        attributes.update(message_class.decode_payload(payload))

        return message_class(**attributes)

    def encode_message(self):
        """Prepare message to be sent on wire"""

        msg_ids = dict((v, k) for k, v in MORITZ_MESSAGE_IDS.items())
        msg_id = msg_ids[self.__class__]

        message = ""
        for (var, length) in ((self.counter, 2), (self.flag, 2), (msg_id, 2),
                              (self.sender_id, 6), (self.receiver_id, 6), (self.group_id, 2)):
            content = "%X".upper() % var
            message += content.zfill(length)

        payload = self.encode_payload()
        if payload:
            message += payload

        length = "%X".upper() % int(len(message) / 2)
        message = "Zs" + length.zfill(2) + message
        return message

    def encode_payload(self):
        return None

    def respond_with(self, klass, **kwargs):
        resp_params = dict(counter=self.counter + 1,
                           sender_id=self.receiver_id,
                           receiver_id=self.sender_id,
                           group_id=self.group_id,
                           flag=self.flag)
        params = {**resp_params, **kwargs}
        return klass(**params)

    def __repr__(self):
        s = "<{}".format(self.__class__.__name__)
        for key in self.__dict__:
            value = self.__dict__[key]
            if isinstance(value, int):
                s += " {}:{:x}".format(key, value)
            else:
                s += " {}:{:}".format(key, value)
        return s + ">"


class PairPingMessage(MoritzMessage):
    """Thermostats send this request on long boost keypress"""
    firmware_version = 0
    device_type = None
    selftest_result = None
    device_serial = None

    @staticmethod
    def decode_payload(payload):
        firmware_version, device_type, selftest_result = struct.unpack(
            ">bBB", bytearray.fromhex(payload[:6]))
        device_serial = bytearray.fromhex(payload[6:]).decode()
        result = {
            'firmware_version': "V%i.%i" % (firmware_version / 0x10,
                                            firmware_version % 0x10),
            'device_type': DEVICE_TYPES[device_type],
            'selftest_result': selftest_result,
            'device_serial': device_serial,
        }
        return result


class PairPongMessage(MoritzMessage):
    """Awaited after PairPingMessage is sent by component"""
    device_type = CUBE

    @staticmethod
    def decode_payload(payload):
        return {'device_type': DEVICE_TYPES[int(payload)]}

    def encode_payload(self):
        return str(DEVICE_TYPES_BY_NAME[self.devicetype]).zfill(2)


class AckMessage(MoritzMessage):
    """Last command received and acknowledged.
           Occasionally if the communication is ongoing, this might get lost.
           So don't rely on it but check state afterwards instead"""
    state = ''
    # fields for a thermostat state
    mode = None
    dstsetting = None
    langateway = None
    is_locked = None
    rferror = None
    battery_low = None
    desired_temperature = None
    measured_temperature = None
    valve_position = None

    @staticmethod
    def decode_payload(payload):
        result = {}
        if payload.startswith("01"):
            result["state"] = "ok"
        elif payload.startswith("81"):
            result["state"] = "invalid_command"
        elif payload.startswith("00"):
            result["state"] = "ignore"
        if len(payload) == 8:
            # FIXME: temporarily accepting the fact that we only handle
            # Thermostat results
            result.update(ThermostatStateMessage.decode_status(payload[2:]))
        return result

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0


class TimeInformationMessage(MoritzMessage):
    """Current time is either requested or encoded. Request simply is empty payload"""
    datetime = None

    @staticmethod
    def decode_payload(payload):
        if len(payload) == 0:
            return {'datetime': None}
        (years_since_2000, day, hour, month_minute, month_sec) = struct.unpack(
            ">BBBBB", bytearray.fromhex(payload[:12]))
        d = datetime(
            year=years_since_2000 + 2000,
            minute=month_minute & 0x3F,
            month=((month_minute & 0xC0) >> 4) | ((month_sec & 0xC0) >> 6),
            day=day,
            hour=hour & 0x3F,
            second=month_sec & 0x3F
        )
        return {'datetime': d}

    @property
    def flag(self):
        return 0x0A if self.datetime is None else 0x04

    def encode_payload(self):
        # may contain empty payload to ask for timeinformation
        if self.datetime is None:
            return ""
        encoded_payload = str("%X" % (self.datetime.year - 2000)).zfill(2)
        encoded_payload += str("%X" % self.datetime.day).zfill(2)
        encoded_payload += str("%X" % self.datetime.hour).zfill(2)
        encoded_payload += str("%X" % (self.datetime.minute |
                                       ((self.datetime.month & 0x0C) << 4))).zfill(2)
        encoded_payload += str("%X" % (self.datetime.second |
                                       ((self.datetime.month & 0x03) << 6))).zfill(2)
        return encoded_payload


class ConfigWeekProfileMessage(MoritzMessage):
    pass


class ConfigTemperaturesMessage(MoritzMessage):
    """Sets temperatur config"""
    comfort_Temperature = 0
    eco_Temperature = 0
    max_Temperature = 0
    min_Temperature = 0
    measurement_Offset = 0
    window_open_Temperature = 0
    window_Open_Duration = 0

    @staticmethod
    def decode_payload(payload):
        (comfort,
         eco,
         max,
         min,
         offset,
         window_Open_Temperature,
         window_Open_Duration) = struct.unpack(">BBBBBBB",
                                               bytearray.fromhex(payload[:14]))

        result = {
            'comfort_Temperature': comfort / 2,
            'eco_Temperature': eco / 2,
            'max_Temperature': max / 2,
            'min_Temperature': min / 2,
            'measurement_Offset': (offset / 2) - 3.5,
            'window_Open_Temperature': window_Open_Temperature / 2,
            'window_Open_Duration': window_Open_Duration * 5
        }

        return result

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.comfort_Temperature is None:
            raise MissingPayloadParameterError(
                "Missing comfort_Temperature in payload")
        if self.eco_Temperature is None:
            raise MissingPayloadParameterError(
                "Missing eco_Temperature in payload")
        if self.max_Temperature is None:
            raise MissingPayloadParameterError(
                "Missing max_Temperature in payload")
        if self.min_Temperature is None:
            raise MissingPayloadParameterError(
                "Missing min_Temperature in payload")
        if self.measurement_Offset is None:
            raise MissingPayloadParameterError(
                "Missing measurement_Offset in payload")
        if self.window_Open_Temperatur is None:
            raise MissingPayloadParameterError(
                "Missing window_Open_Temperatur in payload")
        if self.window_Open_Duration is None:
            raise MissingPayloadParameterError(
                "Missing window_Open_Duration in payload")

        comfort_Temperature = "%0.2X" % int(self.comfort_Temperature * 2)
        eco_Temperature = "%0.2X" % int(self.eco_Temperature * 2)
        max_Temperature = "%0.2X" % int(self.max_Temperature * 2)
        min_Temperature = "%0.2X" % int(self.min_Temperature * 2)
        measurement_Offset = "%0.2X" % int((self.measurement_Offset + 3.5) * 2)
        window_Open_Temperature = "%0.2X" % int(
            self.window_Open_Temperature * 2)
        window_Open_Duration = "%0.2X" % int(self.window_Open_Duration / 5)

        content = comfort_Temperature + eco_Temperature + max_Temperature + \
            min_Temperature + measurement_Offset + window_Open_Temperature + window_Open_Duration
        return content


class ConfigValveMessage(MoritzMessage):
    """Sets valve config"""
    boost_duration = None
    boost_valve_position = None
    decalc_day = None
    decalc_hour = None
    max_valve_position = None
    valve_offset = None

    @staticmethod
    def decode_payload(payload):
        pass

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.boost_duration is None:
            raise MissingPayloadParameterError(
                "Missing boost duration in payload")
        if self.boost_valve_position is None:
            raise MissingPayloadParameterError(
                "Missing boost valve position in payload")
        if self.decalc_day is None:
            raise MissingPayloadParameterError("Missing decalc day in payload")
        if self.decalc_hour is None:
            raise MissingPayloadParameterError(
                "Missing decalc hour in payload")
        if self.max_valve_position is None:
            raise MissingPayloadParameterError(
                "Missing max valve position in payload")
        if self.valve_offset is None:
            raise MissingPayloadParameterError(
                "Missing valve offset in payload")

        boost = "%0.2X" % ((BOOST_DURATION[self.boost_duration] << 5) | int(
            self.boost_valve_position / 5))
        decalc = "%0.2X" % (
            (DECALC_DAYS[self.decalc_day] << 5) | self.decalc_hour)
        max_valve_position = "%0.2X" % int(self.max_valve_position * 255 / 100)
        valve_offset = "%0.2X" % int(self.valve_offset * 255 / 100)
        content = boost + decalc + max_valve_position + valve_offset
        return content


class AddLinkPartnerMessage(MoritzMessage):

    assocDevice = None
    assocDeviceType = None

    @staticmethod
    def decode_payload(payload):
        pass

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.assocDevice is None:
            raise MissingPayloadParameterError(
                "Missing assocDevice in payload")
        if self.assocDeviceType is None:
            raise MissingPayloadParameterError(
                "Missing assocDeviceType in payload")

        assocDevice = "%0.6X" % int(self.assocDevice)
        assocDeviceType = "%0.2X" % list(
            DEVICE_TYPES.keys())[
            list(
                DEVICE_TYPES.values()).index(
                self.assocDeviceType)]
        return assocDevice + assocDeviceType


class RemoveLinkPartnerMessage(MoritzMessage):

    assocDevice = None
    assocDeviceType = None

    @staticmethod
    def decode_payload(payload):
        pass

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.assocDevice is None:
            raise MissingPayloadParameterError(
                "Missing assocDevice in payload")
        if self.assocDeviceType is None:
            raise MissingPayloadParameterError(
                "Missing assocDeviceType in payload")

        assocDevice = self.assocDevice
        assocDeviceType = "%0.2X" % DEVICE_TYPES[self.assocDeviceType]
        return assocDevice + assocDeviceType


class SetGroupIdMessage(MoritzMessage):

    new_group_id = None

    @staticmethod
    def decode_payload(payload):
        return {'group_id': int(payload[0], 16)}

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.new_group_id is None:
            raise MissingPayloadParameterError("Missing group id in payload")

        groupId = "%0.2X" % self.new_group_id
        return groupId


class RemoveGroupIdMessage(MoritzMessage):

    @staticmethod
    def decode_payload(payload):
        pass

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        overrideGroupId = "00"
        return overrideGroupId


class ShutterContactStateMessage(MoritzMessage):

    state = None
    unkbits = None
    rferror = None
    battery_low = None

    @staticmethod
    def decode_status(payload):
        status_bits = bin(int(payload, 16))[2:].zfill(8)
        state = int(status_bits[6:], 2)
        unkbits = int(status_bits[2:6], 2)
        rferror = int(status_bits[1], 2)
        battery_low = int(status_bits[0], 2)
        result = {
            "state": SHUTTER_STATES[state],
            "unkbits": unkbits,
            "rferror": bool(rferror),
            "battery_low": bool(battery_low)
        }
        return result

    @staticmethod
    def decode_payload(payload):
        result = ShutterContactStateMessage.decode_status(payload)
        return result


class SetTemperatureMessage(MoritzMessage):
    """Sets temperature for manual mode as well as mode switch between manual, auto and boost"""

    desired_temperature = None
    mode = None

    @staticmethod
    def decode_payload(payload):
        payload = struct.unpack(">B", bytearray.fromhex(payload[0:4]))
        return {
            'desired_temperature': ((payload[0] & 0x3F) / 2.0),
            'mode': MODE_IDS[payload[0] >> 6]
        }

    @property
    def flag(self):
        return 0x4 if self.group_id else 0x0

    def encode_payload(self):
        if self.desired_temperature is None:
            raise MissingPayloadParameterError(
                "Missing desired_temperature in payload")
        if self.mode is None:
            raise MissingPayloadParameterError("Missing mode in payload")

        if self.desired_temperature > 30.5:
            desired_temperature = 30.5  # "ON"
        elif self.desired_temperature < 4.5:
            desired_temperature = 4.5  # "OFF"
        else:
            # always round to nearest 0.5 first
            desired_temperature = round(self.desired_temperature * 2) / 2.0
        int_temperature = int(desired_temperature * 2)

        modes = dict((v, k) for (k, v) in MODE_IDS.items())
        mode = modes[self.mode]

        # TODO: you can add a until time for chort changes
        # from fhem
        # $until = sprintf("%06x",MAX_DateTime2Internal($args[2]." ".$args[3]));
        # $payload .= $until if(defined($until));
        content = "%X".upper() % ((mode << 6) | int_temperature)
        return content.zfill(2)


class WallThermostatControlMessage(MoritzMessage):

    desired_temperature = None
    temperature = None

    @staticmethod
    def decode_status(payload):
        rawTemperatures = bin(int(payload, 16))[2:].zfill(16)

        result = {
            "desired_temperature": int(rawTemperatures[1:8], 2) / 2,
            "temperature": ((int(rawTemperatures[0], 2) << 8) + int(rawTemperatures[8:], 2)) / 10
        }
        return result

    @staticmethod
    def decode_payload(payload):
        result = WallThermostatControlMessage.decode_status(payload)
        return result


class SetComfortTemperatureMessage(MoritzMessage):
    pass


class SetEcoTemperatureMessage(MoritzMessage):
    pass


class PushButtonStateMessage(MoritzMessage):

    state = None
    is_paired = None
    battery_low = None
    rferror = None

    @staticmethod
    def decode_payload(payload):
        payload = bytes.fromhex(payload)
        higher = payload[1]
        lower = payload[0]
        return {
            'state': bool(higher & (1 << 0)),
            'is_paired': bool(lower & (1 << 4)),
            'rferror': bool(lower & (1 << 6)),
            'battery_low': bool(lower & (1 << 7))
        }

class ThermostatStateMessage(MoritzMessage):
    """Non-reculary sent by Thermostats to report when valve was moved or command received."""

    mode = None
    dstsetting = None
    langateway = None
    is_locked = None
    rferror = None
    battery_low = None
    desired_temperature = None
    measured_temperature = None
    valve_position = None

    @staticmethod
    def decode_status(payload):
        status_bits, valve_position, desired_temperature = struct.unpack(
            ">bBB", bytearray.fromhex(payload[0:6]))
        mode = status_bits & 0x3
        dstsetting = status_bits & 0x04
        langateway = status_bits & 0x08
        status_bits = status_bits >> 9
        is_locked = status_bits & 0x1
        rferror = status_bits & 0x2
        battery_low = status_bits & 0x4
        desired_temperature = (desired_temperature & 0x7F) / 2.0
        result = {
            "mode": MODE_IDS[mode],
            "dstsetting": bool(dstsetting),
            "langateway": bool(langateway),
            "is_locked": bool(is_locked),
            "rferror": bool(rferror),
            "battery_low": bool(battery_low),
            "desired_temperature": desired_temperature,
            "valve_position": valve_position,
        }
        return result

    @staticmethod
    def decode_payload(payload):
        result = ThermostatStateMessage.decode_status(payload)
        if len(payload) > 6:
            pending_payload = bytearray.fromhex(payload[6:])
            if len(pending_payload) == 3:
                # TODO handle date string
                pass
            elif len(pending_payload) == 2 and result['mode'] != 'temporary':
                result["measured_temperature"] = (
                    ((pending_payload[0] & 0x1) << 8) + pending_payload[1]) / 10.0
            else:
                # unknown....
                pass
        return result


class WallThermostatStateMessage(MoritzMessage):
    """Non-reculary sent by Thermostats to report when valve was moved or command received."""

    mode = None
    dstsetting = None
    langateway = None
    is_locked = None
    rferror = None
    battery_low = None
    desired_temperature = None
    display_actual_temperature = None
    temperature = None
    until_str = None

    @staticmethod
    def decode_status(payload):
        status_bits = bin(int(payload[:2], 16))[2:].zfill(8)
        mode = int(status_bits[:2], 2)
        dstsetting = int(status_bits[2:3], 2)
        langateway = int(status_bits[3:4], 2)
        is_locked = int(status_bits[4:5], 2)
        rferror = int(status_bits[5:6], 2)
        battery_low = int(status_bits[6:7], 2)
        display_actual_temperature = bool(int(payload[2:4], 16))
        desired_temperature_raw = bin(int(payload[4:6], 16))[2:].zfill(8)
        desired_temperature = int(desired_temperature_raw[1:8], 2) / 2
        heater_temperature = ""

        null1 = False
        if len(payload) > 6:
            null1 = payload[6:8]

        if len(payload) > 8:
            heater_temperature = payload[8:10]

        null2 = False
        if len(payload) > 10:
            null2 = payload[10:12]

        if len(payload) > 12:
            temperature = (
                (int(desired_temperature_raw[0], 2) << 8) + int(payload[12:], 16)) / 10

        until_str = ""
        if null1 and null2:
            until_str = parseDateTime(null1, heater_temperature, null2)
        else:
            temperature = int(heater_temperature, 16) / 10

        result = {
            "mode": MODE_IDS[mode],
            "dstsetting": bool(dstsetting),
            "langateway": bool(langateway),
            "is_locked": bool(is_locked),
            "rferror": bool(rferror),
            "battery_low": bool(battery_low),
            "desired_temperature": desired_temperature,
            "display_actual_temperature": display_actual_temperature,
            "temperature": temperature,
            "until_str": until_str
        }
        return result

    @staticmethod
    def decode_payload(payload):
        result = WallThermostatStateMessage.decode_status(payload)
        return result


def parseDateTime(byte1, byte2, byte3):
    day = int(byte1, 16) & 0x1F
    month = ((int(byte1, 16) & 0xE0) >> 4) | (int(byte2, 16) >> 7)
    year = int(byte2, 16) & 0x3F
    time = int(byte3, 16) & 0x3F
    if time % 2:
        time = int(time / 2) + ':30'
    else:
        time = int(time / 2) + ":00"

    return {
        "day": day,
        "month": month,
        "year": year,
        "time": time
    }


class SetDisplayActualTemperatureMessage(MoritzMessage):
    pass


class WakeUpMessage(MoritzMessage):
    pass


class ResetMessage(MoritzMessage):
    """Perform a factory reset on given device"""

    pass


# Define at bottom so we can use the class types right away
# Based on FHEM CUL_MAX module
MORITZ_MESSAGE_IDS = {
    0x00: PairPingMessage,
    0x01: PairPongMessage,
    0x02: AckMessage,
    0x03: TimeInformationMessage,

    0x10: ConfigWeekProfileMessage,
    0x11: ConfigTemperaturesMessage,
    0x12: ConfigValveMessage,

    0x20: AddLinkPartnerMessage,
    0x21: RemoveLinkPartnerMessage,
    0x22: SetGroupIdMessage,
    0x23: RemoveGroupIdMessage,

    0x30: ShutterContactStateMessage,

    0x40: SetTemperatureMessage,
    # 0x41: SetPointTemperature,
    0x42: WallThermostatControlMessage,
    0x43: SetComfortTemperatureMessage,
    0x44: SetEcoTemperatureMessage,
    # 0x45: CurrentTemperatureAndHumidity,

    0x50: PushButtonStateMessage,

    0x60: ThermostatStateMessage,

    0x70: WallThermostatStateMessage,

    # 0x80: LockManualControls,
    # 0x81: DaylightSavingTimeMode,
    0x82: SetDisplayActualTemperatureMessage,

    0xF1: WakeUpMessage,
    0xF0: ResetMessage,
    # 0xFF: TestMessage,
}
