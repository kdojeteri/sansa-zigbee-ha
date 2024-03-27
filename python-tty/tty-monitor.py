#!/usr/bin/env python3
from collections import namedtuple, deque
from typing import BinaryIO
from sys import stdout
from serial import Serial
from time import time
import argparse

RECENTS_LIFETIME = 3.0

Frame = namedtuple('Frame', ['ts', 'index', 'message'])
EndOfFile = namedtuple('EndOfFile', ['total_frame_count'])
binary_translation = str.maketrans("01", "·■")

def read_frames(f: BinaryIO) -> Frame | EndOfFile:
    start_time = 1711316607.0
    recent_frames = deque()
    index = 0
    total_frame_count = 0
    while (byte := f.read(1)):
        while len(recent_frames) and recent_frames[0].ts + RECENTS_LIFETIME + start_time < time():
            recent_frames.popleft()

        if byte == b'\x55':
            # new frame start
            total_frame_count += 1

            frame_length = f.read(1)[0]
            message = f.read(frame_length)
            cc = f.read(1)[0]

            checksum = sum(message).to_bytes(2, byteorder='little')[0]
            if cc != checksum:
                raise ValueError("checksum invalid")

            if message not in set(frame.message for frame in recent_frames):
                frame = Frame(time() - start_time, index, message)
                recent_frames.append(frame)
                yield frame
        index += 1

    yield EndOfFile(total_frame_count=total_frame_count)

def main(f: BinaryIO):
    for frame_or_end in read_frames(f):
        if isinstance(frame_or_end, Frame):
            ts, index, message = frame_or_end
            print(f"{ts:06.02f}s #{index:04d} [{len(message):2d}]:", *(f"{c:02x}" for c in message), *(f"{c:08b}".translate(binary_translation) for c in message))
            stdout.flush()
        elif isinstance(frame_or_end, EndOfFile):
            print("total:", frame_or_end.total_frame_count)

if __name__=="__main__":
    arg_parser = argparse.ArgumentParser(prog="frames.py")
    arg_parser.add_argument("tty")
    args = arg_parser.parse_args()

    with Serial(args.tty) as f:
        main(f)
