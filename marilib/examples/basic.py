import time

import click
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame
from marilib.marilib import MariLib
from marilib.model import EdgeEvent, MariNode
from marilib.serial_uart import get_default_port
from marilib.tui import MariLibTUI

SERIAL_PORT_DEFAULT = get_default_port()
NORMAL_DATA_PAYLOAD = b"A" * 224


def on_event(event: EdgeEvent, event_data: MariNode | Frame):
    if event == EdgeEvent.NODE_JOINED:
        # print(f"Node {event_data} joined")
        # print("#", end="", flush=True)
        pass
    elif event == EdgeEvent.NODE_LEFT:
        # print(f"Node {event_data} left")
        # print("0", end="", flush=True)
        pass
    elif event == EdgeEvent.NODE_DATA:
        # print(f"Got frame from 0x{event_data.header.source:016x}: {event_data.payload.hex()}, rssi: {event_data.stats.rssi_dbm}")
        # print(".", end="", flush=True)
        pass


@click.command()
@click.option(
    "--port",
    "-p",
    type=str,
    default=SERIAL_PORT_DEFAULT,
    show_default=True,
    help="Serial port to use (e.g., /dev/ttyACM0)",
)
def main(port: str | None):
    """A basic example of using the MariLib library."""
    mari = MariLib(on_event, port)
    tui = MariLibTUI()

    try:
        while True:
            with mari.lock:
                mari.gateway.update()

            with mari.lock:
                nodes_exist = bool(mari.gateway.nodes)
            if nodes_exist:
                mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)

            with mari.lock:
                tui.render(mari)

            time.sleep(0.3)

    except KeyboardInterrupt:
        pass
    finally:
        tui.close()


if __name__ == "__main__":
    main()
