import time

from marilib.marilib import MarilibEdge
from marilib.communication_adapter import MQTTAdapter, SerialAdapter
from marilib.serial_uart import get_default_port


def on_event(event, event_data):
    """An event handler for the application."""
    # print(".", end="", flush=True)
    pass


def main():
    mari = MarilibEdge(
        on_event,
        serial_interface=SerialAdapter(get_default_port()),
        mqtt_interface=MQTTAdapter("localhost", 1883),
    )
    while True:
        for node in mari.gateway.nodes:
            mari.send_frame(dst=node.address, payload=b"NORMAL_APP_DATA")
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm())
            for node in mari.gateway.nodes
        ]
        # print(f"Stats: {statistics}")
        time.sleep(1)


if __name__ == "__main__":
    main()
