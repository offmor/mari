import time

import click
from marilib.logger import MetricsLogger
from marilib.mari_protocol import Frame, MARI_BROADCAST_ADDRESS
from marilib.model import EdgeEvent, MariNode
from marilib.communication_adapter import SerialAdapter, MQTTAdapter
from marilib.serial_uart import get_default_port
from marilib.tui_edge import MarilibTUIEdge
from marilib.marilib_edge import MarilibEdge

NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"


def on_event(event: EdgeEvent, event_data: MariNode | Frame):
    """An event handler for the application."""
    pass


@click.command()
@click.option(
    "--port",
    "-p",
    type=str,
    default=get_default_port(),
    show_default=True,
    help="Serial port to use (e.g., /dev/ttyACM0)",
)
@click.option(
    "--mqtt-host",
    "-m",
    type=str,
    default="",
    show_default=True,
    help="MQTT broker to use (default: empty, no cloud)",
)
@click.option(
    "--log-dir",
    default="logs",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(port: str | None, mqtt_host: str, log_dir: str):
    """A basic example of using the MarilibEdge library."""
    tui = MarilibTUIEdge()
    logger = MetricsLogger(
        log_dir_base=log_dir, rotation_interval_minutes=1440, log_interval_seconds=1.0
    )
    serial_interface = SerialAdapter(port)
    mqtt_interface = MQTTAdapter.from_host_port(mqtt_host, is_edge=True) if mqtt_host else None

    mari = MarilibEdge(on_event, serial_interface=serial_interface, mqtt_interface=mqtt_interface, logger=logger, main_file=__file__)

    try:
        while True:
            mari.update()
            if not mari.uses_mqtt and mari.nodes:
                mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)
            tui.render(mari)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        tui.close()
        logger.close()


if __name__ == "__main__":
    main()
