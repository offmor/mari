import time

import click
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, MARI_NET_ID_DEFAULT, Frame
from marilib.marilib_cloud import MarilibCloud
from marilib.model import EdgeEvent, GatewayInfo, MariNode
from marilib.communication_adapter import MQTTAdapter

NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"


def on_event(event: EdgeEvent, event_data: MariNode | Frame | GatewayInfo):
    """An event handler for the application."""
    if event == EdgeEvent.GATEWAY_INFO:
        return
    print(".", end="", flush=True)


@click.command()
@click.option(
    "--mqtt-host",
    "-m",
    type=str,
    default="localhost:1883",
    show_default=True,
    help="MQTT broker to use (default: localhost:1883)",
)
@click.option(
    "--network-id",
    "-n",
    type=str,
    default=MARI_NET_ID_DEFAULT,
    show_default=True,
    help="Network ID to use (default: 0x0001)",
)
@click.option(
    "--log-dir",
    default="logs",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(mqtt_host: str, network_id: str, log_dir: str):
    """A basic example of using the MariLibCloud library."""

    mari = MarilibCloud(
        on_event,
        mqtt_interface=MQTTAdapter.from_host_port(mqtt_host, is_edge=False),
        network_id=int(network_id, 16),
        main_file=__file__,
    )

    try:
        while True:
            mari.update()

            if mari.nodes:
                print(f"Sending frame to broadcast address {MARI_BROADCAST_ADDRESS:016X}")
                mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)

            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
