import time

from marilib.serial_hdlc import (
    HDLCDecodeException,
    HDLCHandler,
    HDLCState,
    hdlc_encode,
)
from marilib.serial_uart import SerialInterface

BAUDRATE = 1000000
# BAUDRATE = 115200

hdlc_handler = HDLCHandler()


def on_byte_received(byte):
    # print(f"Received byte: {byte}")
    hdlc_handler.handle_byte(byte)
    if hdlc_handler.state == HDLCState.READY:
        try:
            payload = hdlc_handler.payload
            print(f"Received payload: {payload.hex()}")
        except HDLCDecodeException as e:
            print(f"Error decoding payload: {e}")


serial_interface = SerialInterface("/dev/ttyACM0", BAUDRATE, on_byte_received)


while True:
    time.sleep(1)
    payload = b"AAA"
    print(f"Sending payload: {payload.hex()}")
    serial_interface.write(hdlc_encode(payload))
