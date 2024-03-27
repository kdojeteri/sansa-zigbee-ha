#!/usr/bin/env python3
import argparse
from queue import Queue
from sys import stdout

from tools import SerialCapture, Frame, serial_forward_frame

binary_translation = str.maketrans("01", "·■")

if __name__=="__main__":
    arg_parser = argparse.ArgumentParser(prog="frames.py")
    arg_parser.add_argument("tty1")
    arg_parser.add_argument("tty2")
    args = arg_parser.parse_args()

    queue = Queue()
    cap1 = SerialCapture(serial_name=args.tty1, msg_queue=queue)
    cap2 = SerialCapture(serial_name=args.tty2, msg_queue=queue)
    cap1.start()
    cap2.start()
    try:
        frame: Frame
        for frame in queue.get():
            other = cap1 if frame.serial_name == cap2.serial_name else cap2
            serial_forward_frame(other.serial_port, frame)

            ts, serial_name, message = frame
            print(f"{serial_name} {ts:06.02f}s [{len(message):2d}]:", *(f"{c:02x}" for c in message), *(f"{c:08b}".translate(binary_translation) for c in message))
            stdout.flush()
    finally:
        cap1.close()
        cap2.close()
        print("totals:", cap1.total_frame_count, cap2.total_frame_count)


