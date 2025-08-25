import time

from marilib.marilib_edge import MarilibEdge, EdgeEvent
from marilib.communication_adapter import MQTTAdapter, SerialAdapter
from marilib.serial_uart import get_default_port


def on_event(event, event_data):
    """An event handler for the application."""
    if event == EdgeEvent.GATEWAY_INFO:
        return
    print(".", end="", flush=True)


def main():
    mari_edge = MarilibEdge(
        on_event,
        serial_interface=SerialAdapter(get_default_port()),
        mqtt_interface=MQTTAdapter("localhost", 1883, is_edge=True),
    )

    while True:
        mari_edge.update()
        if not mari_edge.uses_mqtt:
            # only generate frames if not using MQTT
            for node in mari_edge.nodes:
                mari_edge.send_frame(dst=node.address, payload=b"NORMAL_APP_DATA")
                print(",", end="", flush=True)
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm()) for node in mari_edge.nodes
        ]
        print(f"Stats: {statistics}")
        time.sleep(3)


if __name__ == "__main__":
    main()
