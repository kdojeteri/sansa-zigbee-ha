#!/usr/bin/env python3
import argparse
from queue import Queue
from sys import stdout

from tools import SerialCapture, Message

binary_translation = str.maketrans("01", "·■")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="frames.py")
    arg_parser.add_argument("tty")
    args = arg_parser.parse_args()

    queue = Queue()
    cap = SerialCapture(serial_name=args.tty, msg_queue=queue)
    try:
        cap.start()

        while True:
            frame: Message = queue.get()
            queue.task_done()
            ts, serial_name, message = frame
            print(
                f"{ts:06.02f}s [{len(message):2d}]:",                         # 020.12s [ 8]
                *(f"{c:02x}" for c in message),                               # 81 01 ab f1 00 0b 00 e0
                *(f"{c:08b}".translate(binary_translation) for c in message)  # ■······■ ·······■ ■·■·■·■■ ■■■■···■
            )
            stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        cap.close()
        print("total:", cap.total_frame_count)
