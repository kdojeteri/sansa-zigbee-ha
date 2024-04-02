from .serial_capture import Message


def buffer_from_message(frame: Message):
    checksum = sum(frame.message).to_bytes(2, byteorder='little')[0]
    return bytes((
        0x55,
        len(frame.message),
        *frame.message,
        checksum
    ))
