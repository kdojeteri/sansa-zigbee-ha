#!/usr/bin/env python3
import argparse
import time
from queue import Queue
from sys import stdout

from tools import SerialCapture, Message, buffer_from_message

binary_translation = str.maketrans("01", "·■")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="frames.py")
    arg_parser.add_argument("tty1")
    arg_parser.add_argument("tty2")
    args = arg_parser.parse_args()

    start_timestamp = time.time()
    queue = Queue()
    cap1 = SerialCapture(serial_name=args.tty1, msg_queue=queue, start_timestamp=start_timestamp, recents_lifetime=0.0)
    cap2 = SerialCapture(serial_name=args.tty2, msg_queue=queue, start_timestamp=start_timestamp, recents_lifetime=0.0)
    cap1.unknown_callback = lambda buffer: cap2.serial_port.write(buffer)
    cap2.unknown_callback = lambda buffer: cap1.serial_port.write(buffer)
    cap1.start()
    cap2.start()
    try:
        while True:
            msg: Message = queue.get()
            ts, serial_name, message = msg

            if serial_name == cap1.serial_name:
                cap2.serial_port.write(buffer_from_message(msg))
            else:
                cap1.serial_port.write(buffer_from_message(msg))

            print(
                f"{serial_name} {ts:06.02f}s [{len(message):2d}]:",           # /dev/ttyUSB0 020.12s [ 8]
                *(f"{c:02x}" for c in message),                               # 81 01 ab f1 00 0b 00 e0
                *(f"{c:08b}".translate(binary_translation) for c in message)  # ■······■ ·······■ ■·■·■·■■ ■■■■···■
            )
            stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        cap1.close()
        cap2.close()
        print("totals:", cap1.total_frame_count, cap2.total_frame_count)
