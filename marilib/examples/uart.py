import time

from mira_edge.serial_uart import SerialInterface


def on_byte_received(byte):
    print(f"Received byte: {byte}")


serial_interface = SerialInterface("/dev/ttyACM0", 1000000, on_byte_received)

while True:
    time.sleep(1)
    serial_interface.write(b"Hello, world!")
