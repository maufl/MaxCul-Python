""" This module implements the low level logic of talking to the serial CUL device"""
import queue
from collections import deque
import threading
import time
import logging
from serial import Serial, SerialException

LOGGER = logging.getLogger(__name__)

MAX_QUEUED_COMMANDS = 10
READLINE_TIMEOUT = 0.0

COMMAND_REQUEST_BUDGET = 'X'

MIN_REQUIRED_BUDGET = 1500


class CulIoThread(threading.Thread):
    """Low-level serial communication thread base"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, device_path, baudrate, sent_callback=None):
        super().__init__()
        self.read_queue = queue.Queue()
        self._send_queue = deque([], MAX_QUEUED_COMMANDS)
        self._device_path = device_path
        self._baudrate = baudrate
        self._stop_requested = threading.Event()
        self._cul_version = None
        self._com_port = None
        self._remaining_budget = 0
        self._sent_callback = sent_callback
        self._last_serial_reopen = time.monotonic()

    @property
    def cul_version(self):
        """Returns the version reported from the CUL stick"""
        return self._cul_version

    @property
    def has_send_budget(self):
        """Ask CUL if we have enough budget of the 1 percent rule left"""
        return self._remaining_budget >= MIN_REQUIRED_BUDGET

    def enqueue_command(self, command):
        """Pushes a new command to be sent to the CUL stick onto the queue"""
        self._send_queue.appendleft(command)

    def stop(self, timeout=None):
        """Stops the loop of this thread and waits for it to exit"""
        self._stop_requested.set()
        self.join(timeout)

    def run(self):
        self._init_cul()
        while not self._stop_requested.isSet():
            self._loop()

    def _loop(self):
        self._receive_messages()
        self._send_pending_message()
        if self._remaining_budget < MIN_REQUIRED_BUDGET:
            LOGGER.debug("Unable to send messages, budget to low.")
            while self._remaining_budget < MIN_REQUIRED_BUDGET:
                self._writeline(COMMAND_REQUEST_BUDGET)
                for _ in range(50):
                    self._receive_messages()
                    time.sleep(1)
        if (time.monotonic() - self._last_serial_reopen) > 24 * 60 * 60:
            LOGGER.debug("Reopening serial device")
            self._reopen_serial_device()
            self._last_serial_reopen = time.monotonic()
        time.sleep(0.2)

    def _receive_messages(self):
        while self._receive_message():
            next

    def _receive_message(self):
        # Process pending received messages (if any)
        line = self._readline()
        if line is not None:
            if line.startswith("21"):
                self._remaining_budget = int(line[3:].strip()) * 10 or 1
                LOGGER.debug(
                    "Got pending budget: %sms", self._remaining_budget)
            elif line.startswith("ZERR"):
                LOGGER.warning(
                    "Received error message from CUL stick: '%s'",
                    line
                )
            elif line.startswith("Z"):
                LOGGER.debug(
                    "Received new moritz message: %s", line)
                self.read_queue.put(line)
            else:
                LOGGER.debug("Got unhandled response from CUL: '%s'", line)
        return line is not None

    def _send_pending_message(self):
        try:
            pending_message = self._send_queue.pop()
        except IndexError:
            return
        try:
            command = pending_message.encode_message()
            if self._remaining_budget > len(command) * 10:
                self._writeline(command)
                if self._sent_callback:
                    self._sent_callback(pending_message)
            else:
                self._send_queue.append(pending_message)
                self._writeline(COMMAND_REQUEST_BUDGET)
        except Exception as err:
            LOGGER.error(
                "Exception <%s> was raised while encoding message %s. Please consider reporting this as a bug.",
                err,
                pending_message)

    def _init_cul(self):
        if not self._open_serial_device():
            self._stop_requested.set()
            return

        if self._com_port is None:
            LOGGER.error("No version from CUL, cannot communicate")
            self._stop_requested.set()

    def _open_serial_device(self):
        try:
            self._com_port = Serial(
                self._device_path,
                self._baudrate,
                timeout=READLINE_TIMEOUT)
        except SerialException as err:
            LOGGER.error("Unable to open serial device <%s>", err)
            return False
        # was required for my nanoCUL
        time.sleep(2)
        # get CUL FW version
        for _ in range(10):
            self._writeline("V")
            time.sleep(1)
            self._cul_version = self._readline() or None
            if self._cul_version is not None:
                LOGGER.debug("CUL reported version %s", self._cul_version)
                break
            else:
                LOGGER.info("No version from CUL reported?")
        if self._cul_version is None:
            self._com_port.close()
            self._com_port = None
            return False
        # enable reporting of message strength
        self._writeline("X21")
        time.sleep(0.3)
        # receive Moritz messages
        self._writeline("Zr")
        time.sleep(0.3)
        # disable FHT mode by setting station to 0000
        self._writeline("T01")
        time.sleep(0.3)
        return True

    def _reopen_serial_device(self):
        if self._com_port:
            try:
                self._com_port.close()
            except Exception:
                pass
            self._com_port = None
        self._remaining_budget = 0

        for timeout in [5, 10, 20, 40]:
            if self._open_serial_device():
                return True
            time.sleep(timeout)
        return False

    def _writeline(self, command):
        """Sends given command to CUL. Invalidates has_send_budget if command starts with Zs"""
        if not command == COMMAND_REQUEST_BUDGET:
            LOGGER.debug("Writing command %s", command)
        if command.startswith("Zs"):
            self._remaining_budget = 0
        try:
            self._com_port.write((command + "\r\n").encode())
        except SerialException as err:
            LOGGER.error(
                "Error writing to serial device <%s>. Try reopening it.", err)
            if self._reopen_serial_device():
                self._writeline(command)
            else:
                LOGGER.error("Unable to reopen serial device, quitting")
                self._stop_requested.set()

    def _readline(self):
        try:
            line = self._com_port.readline()
            line = line.decode('utf-8')[:-2]
            if line:
                return line
            return None
        except SerialException as err:
            LOGGER.error(
                "Error reading from serial device <%s>. Try reopening it.", err)
            if self._reopen_serial_device():
                self._readline()
            else:
                LOGGER.error("Unable to reopen serial device, quitting")
                self._stop_requested.set()
