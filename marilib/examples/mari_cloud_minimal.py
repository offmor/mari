import time

from marilib.marilib_cloud import MarilibCloud
from marilib.communication_adapter import MQTTAdapter


def on_event(event, event_data):
    """An event handler for the application."""
    print(".", end="", flush=True)


def main():
    mqtt_interface = MQTTAdapter("localhost", 1883)

    mari_cloud = MarilibCloud(
        on_event,
        mqtt_interface=mqtt_interface,
    )

    while True:
        for node in mari_cloud.nodes:
            mari_cloud.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm())
            for node in mari_cloud.nodes
        ]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)


if __name__ == "__main__":
    main()
