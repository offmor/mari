import time

import click
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, MARI_NET_ID_DEFAULT, Frame
from marilib.marilib_cloud import MarilibCloud
from marilib.model import EdgeEvent, GatewayInfo, MariNode
from marilib.communication_adapter import MQTTAdapter
from marilib.tui_cloud import MarilibTUICloud

NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"


def on_event(event: EdgeEvent, event_data: MariNode | Frame | GatewayInfo):
    """An event handler for the application."""
    pass


@click.command()
@click.option(
    "--mqtt-host",
    "-m",
    type=str,
    default="localhost:1883",
    show_default=True,
    help="MQTT broker to use",
)
@click.option(
    "--network-id",
    "-n",
    type=lambda x: int(x, 16),
    default=MARI_NET_ID_DEFAULT,
    help=f"Network ID to use [default: 0x{MARI_NET_ID_DEFAULT:04X}]",
)
@click.option(
    "--log-dir",
    default="logs",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(mqtt_host: str, network_id: int, log_dir: str):
    """A basic example of using the MariLibCloud library."""

    mari = MarilibCloud(
        on_event,
        mqtt_interface=MQTTAdapter.from_host_port(mqtt_host, is_edge=False),
        # logger=TBD, TODO: add logger to MarilibCloud
        network_id=network_id,
        tui=MarilibTUICloud(),
        main_file=__file__,
    )

    try:
        while True:
            mari.update()
            if mari.nodes:
                mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)
            mari.render_tui()
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        mari.close_tui()


if __name__ == "__main__":
    main()
