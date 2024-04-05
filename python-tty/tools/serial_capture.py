import enum
from collections import namedtuple
from queue import Queue
from threading import Thread
from time import time
from typing import Callable

from serial import Serial
from serial.serialutil import SerialException

DEFAULT_RECENTS_LIFETIME = 3.0

Message = namedtuple('Message', ['ts', 'serial_name', 'message'])

# TODO send reason for end of capture
EndOfCapture = namedtuple('EndOfCapture', ['code'])
EndCode = enum.Enum('EndCode', ['CLOSED', 'DISCONNECTED'])

# TODO unpack frame using struct
frame_format = '<BpB'
Frame = namedtuple("Frame", ['preamble', 'message', 'checksum'])


class SerialCapture(Thread):
    def __init__(self,
                 serial_name: str,
                 msg_queue: Queue,
                 unknown_callback: Callable[[bytes], None] | None = None,
                 start_timestamp=None,
                 recents_lifetime=DEFAULT_RECENTS_LIFETIME):
        Thread.__init__(self)
        self.unknown_callback = unknown_callback
        self.total_frame_count: int = 0
        self.serial_port: Serial | None = None
        self.start_timestamp: float | None = start_timestamp
        self.recent_messages: set = set()
        self.serial_name = serial_name
        self.msg_queue = msg_queue
        self.recents_lifetime = recents_lifetime

    def run(self):
        # if member property not set, default to current time
        if self.start_timestamp is None:
            self.start_timestamp = time()

        with Serial(self.serial_name) as f:
            self.serial_port = f
            self.total_frame_count = 0

            try:
                while f.is_open and (byte := f.read(1)):
                    self._invalidate_recents()

                    if byte == b'\x55':
                        # new frame start
                        self._process_message()
                    elif self.unknown_callback is not None:
                        self.unknown_callback(byte)
            except OSError:
                # TODO can't open serial port
                return
            except TypeError:
                if not f.is_open:
                    # TODO report serial port was closed
                    return
            except SerialException:
                # TODO report serial port was disconnected
                return
            except BaseException:
                raise

    def close(self):
        if self.serial_port is not None:
            self.serial_port.close()
            self.serial_port = None
        self.join()

    def _invalidate_recents(self):
        expired = (
            message
            for message in self.recent_messages.copy() if
            (expires_at := message.ts + self.recents_lifetime + self.start_timestamp)
            and time() > expires_at
        )

        self.recent_messages.difference_update(expired)

    def _process_message(self):
        frame_length = self.serial_port.read(1)[0]
        message = self.serial_port.read(frame_length)
        cc = self.serial_port.read(1)[0]

        checksum = sum(message).to_bytes(2, byteorder='little')[0]

        if cc != checksum and self.unknown_callback is not None:
            self.unknown_callback(bytes((frame_length, *message, cc)))
            return

        self.total_frame_count += 1

        if message in (f.message for f in self.recent_messages):
            return

        frame = Message(
            time() - self.start_timestamp,
            self.serial_name,
            message
        )

        self.recent_messages.add(frame)
        self.msg_queue.put(frame)
