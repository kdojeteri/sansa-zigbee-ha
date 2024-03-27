from time import time
from collections import deque, namedtuple
from queue import Queue
from serial import Serial
from threading import Thread


DEFAULT_RECENTS_LIFETIME = 3.0

Frame = namedtuple('Frame', ['ts', 'serial_name', 'message'])
EndOfFile = namedtuple('EndOfFile', ['total_frame_count', 'serial_name'])


class SerialCapture:
    def __init__(self, serial_name: str, msg_queue: Queue, recents_lifetime=DEFAULT_RECENTS_LIFETIME):
        self.total_frame_count: int = 0
        self.serial_port: Serial | None = None
        self._thread: Thread | None = None
        self.start_timestamp: float | None = None
        self.recent_frames: deque[Frame] = deque()
        self.serial_name = serial_name
        self.msg_queue = msg_queue
        self.recents_lifetime = recents_lifetime

    def start(self, start_timestamp: float = None):
        # if arg is set, set member property
        if start_timestamp is not None:
            self.start_timestamp = start_timestamp

        # if member property not set, default to current time
        if self.start_timestamp is None:
            self.start_timestamp = time()

        with Serial(self.serial_name) as f:
            self.serial_port = f
            self.total_frame_count = 0
            self._thread = Thread(target=self._read_frames, args=(f,))

    def close(self):
        if self.serial_port is not None:
            self.serial_port.close()
        if self._thread is not None:
            self._thread.join()

    def _read_frames(self, f: Serial):
        while byte := f.read(1):
            self._invalidate_recents()

            if byte == b'\x55':
                # new frame start
                self.total_frame_count += 1
                frame_length = f.read(1)[0]
                message = f.read(frame_length)
                cc = f.read(1)[0]
                checksum = sum(message).to_bytes(2, byteorder='little')[0]

                if cc != checksum:
                    raise ValueError("checksum invalid")

                if message in self.recent_frames:
                    continue

                frame = Frame(
                    time() - self.start_timestamp,
                    self.serial_name,
                    message
                )

                self.recent_frames.append(frame)
                self.msg_queue.put(frame)

    def _invalidate_recents(self):
        while len(self.recent_frames) and self.recent_frames[0].ts + self.recents_lifetime + self.start_timestamp < time():
            self.recent_frames.popleft()

