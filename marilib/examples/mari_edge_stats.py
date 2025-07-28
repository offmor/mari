import sys
import threading
import time

import click
from marilib.logger import MetricsLogger
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame
from marilib.marilib import MariLib
from marilib.model import EdgeEvent, MariNode, SCHEDULES, TestState
from marilib.serial_uart import get_default_port
from marilib.tui import MariLibTUI

LOAD_PACKET_PAYLOAD = b"L"
NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"

SCHEDULE_NAME_TO_ID = {
    schedule["name"]: schedule_id for schedule_id, schedule in SCHEDULES.items()
}


class LoadTester(threading.Thread):
    def __init__(
        self,
        mari: MariLib,
        test_state: TestState,
        stop_event: threading.Event,
    ):
        super().__init__(daemon=True)
        self.mari = mari
        self.test_state = test_state
        self._stop_event = stop_event

    def run(self):
        if self.test_state.load == 0:
            return
        max_rate = self.mari.get_max_downlink_rate(self.test_state.schedule_id)
        if max_rate == 0:
            sys.stderr.write(
                f"Error: Invalid schedule_id '{self.test_state.schedule_id}'.\n"
            )
            return
        self.test_state.rate = int(max_rate)
        packets_per_second = max_rate * (self.test_state.load / 100.0)
        delay = 1.0 / packets_per_second if packets_per_second > 0 else float("inf")
        while not self._stop_event.is_set():
            with self.mari.lock:
                nodes_exist = bool(self.mari.gateway.nodes)

            if nodes_exist:
                self.mari.send_frame(MARI_BROADCAST_ADDRESS, LOAD_PACKET_PAYLOAD)
            self._stop_event.wait(delay)


def on_event(event: EdgeEvent, event_data: MariNode | Frame):
    """A simple event handler for the application."""
    if event == EdgeEvent.NODE_DATA:
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
@click.option(
    "--log-dir",
    default="logs_latency",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(port: str | None, schedule: str, load: int, log_dir: str):
    if not (0 <= load <= 100):
        sys.stderr.write("Error: --load must be between 0 and 100.\n")
        return

    mari = MariLib(on_event, port)
    logger = MetricsLogger(log_dir_base=log_dir)

    schedule_id = SCHEDULE_NAME_TO_ID[schedule.lower()]
    test_state = TestState(
        schedule_id=schedule_id,
        schedule_name=schedule.lower(),
        load=load,
    )

    tui = MariLibTUI(test_state=test_state)
    stop_event = threading.Event()

    mari.latency_test_enable()

    load_tester = LoadTester(mari, test_state, stop_event)
    if load > 0:
        load_tester.start()

    try:
        normal_traffic_interval = 0.5
        last_normal_send_time = time.monotonic()

        while not stop_event.is_set():
            with mari.lock:
                mari.gateway.update()

                if logger.active:
                    logger.log_gateway_metrics(mari.gateway)
                    logger.log_all_nodes_metrics(
                        list(mari.gateway.node_registry.values())
                    )

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
        mari.latency_test_disable()
        if load_tester.is_alive():
            load_tester.join()
        tui.close()
        logger.close()


if __name__ == "__main__":
    main()
