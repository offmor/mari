import sys
import threading
import time

import click
from marilib.latency import LatencyTester
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame
from marilib.marilib import MariLib
from marilib.model import EdgeEvent, MariNode, SCHEDULES
from marilib.serial_uart import get_default_port
from marilib.tui import MariLibTUI

# Define payloads for different traffic types
LOAD_PACKET_PAYLOAD = b"L"
NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"

# Create a mapping from schedule name (e.g., "big") to its ID (e.g., 1)
SCHEDULE_NAME_TO_ID = {
    schedule["name"]: schedule_id for schedule_id, schedule in SCHEDULES.items()
}


class LoadTester(threading.Thread):
    def __init__(
        self,
        mari: MariLib,
        schedule_id: int,
        load: int,
        stop_event: threading.Event,
    ):
        super().__init__(daemon=True)
        self.mari = mari
        self.schedule_id = schedule_id
        self.load = load
        self._stop_event = stop_event

    def run(self):
        if self.load == 0:
            return
        max_rate = self.mari.get_max_downlink_rate(self.schedule_id)
        if max_rate == 0:
            sys.stderr.write(f"Error: Invalid schedule_id '{self.schedule_id}'.\n")
            return
        self.mari.test_rate = int(max_rate)
        packets_per_second = max_rate * (self.load / 100.0)
        delay = 1.0 / packets_per_second if packets_per_second > 0 else float("inf")

        while not self._stop_event.is_set():
            with self.mari.lock:
                nodes_exist = bool(self.mari.gateway.nodes)

            if nodes_exist:
                self.mari.send_frame(MARI_BROADCAST_ADDRESS, LOAD_PACKET_PAYLOAD)
            self._stop_event.wait(delay)


SERIAL_PORT_DEFAULT = get_default_port()
latency_tester = None  # type: LatencyTester | None


def on_event(event: EdgeEvent, event_data: MariNode | Frame):
    """Directs latency data to the LatencyTester instance."""
    if event == EdgeEvent.LATENCY_DATA and latency_tester:
        latency_tester.handle_response(event_data)


@click.command()
@click.option(
    "--port",
    "-p",
    type=str,
    default=SERIAL_PORT_DEFAULT,
    show_default=True,
    help="Serial port to use (e.g., /dev/ttyACM0)",
)
@click.option(
    "--schedule",
    type=click.Choice(SCHEDULE_NAME_TO_ID.keys(), case_sensitive=False),
    required=True,
    help="Name of the schedule to test.",
)
@click.option(
    "--load",
    type=int,
    default=0,
    show_default=True,
    help="Load percentage to apply (0–100)",
)
def main(port: str | None, schedule: str, load: int):
    """Main application entry point."""
    if not (0 <= load <= 100):
        sys.stderr.write("Error: --load must be between 0 and 100.\n")
        return

    mari = MariLib(on_event, port)
    schedule_id = SCHEDULE_NAME_TO_ID[schedule.lower()]
    mari.test_schedule_id = schedule_id
    mari.test_schedule_name = schedule.lower()
    mari.test_load = load

    tui = MariLibTUI()
    stop_event = threading.Event()

    global latency_tester
    latency_tester = LatencyTester(mari)
    latency_tester.start()

    load_tester = LoadTester(mari, schedule_id, load, stop_event)
    if load > 0:
        load_tester.start()

    try:
        normal_traffic_interval = 0.5  # seconds
        last_normal_send_time = time.monotonic()

        while not stop_event.is_set():
            with mari.lock:
                mari.gateway.update()
                tui.render(mari)

            current_time = time.monotonic()
            if current_time - last_normal_send_time >= normal_traffic_interval:
                with mari.lock:
                    nodes_exist = bool(mari.gateway.nodes)
                if nodes_exist:
                    mari.send_frame(MARI_BROADCAST_ADDRESS, NORMAL_DATA_PAYLOAD)
                last_normal_send_time = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        if latency_tester:
            latency_tester.stop()
        if load_tester.is_alive():
            load_tester.join()
        tui.close()


if __name__ == "__main__":
    main()
