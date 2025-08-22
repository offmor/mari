import time

from marilib.marilib_cloud import MarilibCloud
from marilib.communication_adapter import MQTTAdapter
from marilib.model import EdgeEvent


def on_event(event, event_data):
    """An event handler for the application."""
    if event == EdgeEvent.GATEWAY_INFO:
        return
    print(".", end="", flush=True)


def main():
    mari_cloud = MarilibCloud(
        on_event,
        mqtt_interface=MQTTAdapter("localhost", 1883, is_edge=False),
        network_id=0xA0,
    )

    while True:
        mari_cloud.update()
        for node in mari_cloud.nodes:
            print(f"Sending frame to {node.address:016X}")
            mari_cloud.send_frame(dst=node.address, payload=b"NORMAL_APP_DATA")
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm())
            for node in mari_cloud.nodes
        ]
        print(f"Network statistics: {statistics}")
        time.sleep(3)


if __name__ == "__main__":
    main()
