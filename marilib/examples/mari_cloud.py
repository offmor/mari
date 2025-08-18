import time

import click
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame
from marilib.marilib import MariLibCloud
from marilib.model import EdgeEvent, GatewayInfo, MariNode
from marilib.communication_adapter import MQTTAdapter

NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"


def on_event(event: EdgeEvent, event_data: MariNode | Frame | GatewayInfo):
    """An event handler for the application."""
    if event == EdgeEvent.GATEWAY_INFO:
        print(f"\nGateway info: {event_data}")
    else:
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
    "--log-dir",
    default="logs",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(mqtt_host: str, log_dir: str):
    """A basic example of using the MariLibCloud library."""

    mqtt_interface = MQTTAdapter(*mqtt_host.split(":"))

    mari = MariLibCloud(on_event, mqtt_interface=mqtt_interface, main_file=__file__)

    try:
        while True:
            mari.update()

            if mari.gateway.nodes:
                mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)

            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
