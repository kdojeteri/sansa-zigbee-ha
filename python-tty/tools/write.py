from serial import Serial
from .serial_capture import Frame


def serial_forward_frame(serial: Serial, frame: Frame):
    checksum = sum(frame.message).to_bytes(2, byteorder='little')[0]

    serial.write(b'\x55')
    serial.write(bytes((len(frame.message),)))
    serial.write(frame.message)
    serial.write(bytes((checksum,)))
