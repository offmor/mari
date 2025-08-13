import sys
import threading
import time

import click
from marilib.logger import MetricsLogger
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame
from marilib.marilib import MariLib
from marilib.model import EdgeEvent, GatewayInfo, MariNode, TestState
from marilib.serial_uart import get_default_port
from marilib.tui_edge import MariLibTUIEdge

LOAD_PACKET_PAYLOAD = b"L"
NORMAL_DATA_PAYLOAD = b"NORMAL_APP_DATA"


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
        self.has_rate = False
        self.delay = None

    def run(self):
        while not self._stop_event.is_set():
            # wait for gateway schedule to be available and try to compute rate
            if not self.has_rate:
                self.set_rate()
            if self.delay is None:
                self._stop_event.wait(
                    0.1
                )  # fixed, waiting for gateway schedule to be available
                continue

            # once we have rate, send packets at that rate
            with self.mari.lock:
                nodes_exist = bool(self.mari.gateway.nodes)

            if nodes_exist:
                self.mari.send_frame(MARI_BROADCAST_ADDRESS, LOAD_PACKET_PAYLOAD)
            self._stop_event.wait(self.delay)

    def set_rate(self):
        if self.test_state.load == 0:
            return
        max_rate = self.mari.get_max_downlink_rate()
        if max_rate == 0:
            sys.stderr.write("Error computing max rate")
            return
        self.test_state.rate = int(max_rate)
        packets_per_second = max_rate * (self.test_state.load / 100.0)
        self.delay = (
            1.0 / packets_per_second if packets_per_second > 0 else float("inf")
        )
        self.has_rate = True


def on_event(event: EdgeEvent, event_data: MariNode | Frame | GatewayInfo):
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
    "--load",
    type=int,
    default=0,
    show_default=True,
    help="Load percentage to apply (0–100)",
)
@click.option(
    "--log-dir",
    default="logs_metrics",
    show_default=True,
    help="Directory to save metric log files.",
    type=click.Path(),
)
def main(port: str | None, load: int, log_dir: str):
    if not (0 <= load <= 100):
        sys.stderr.write("Error: --load must be between 0 and 100.\n")
        return

    setup_params = {
        "script_name": "mari_edge_stats.py",
        "port": port,
        "load_percentage": load,
    }
    logger = MetricsLogger(log_dir_base=log_dir, rotation_interval_minutes=1440)

    mari = MariLib(on_event, port, logger=logger, setup_params=setup_params)

    test_state = TestState(
        load=load,
    )

    tui = MariLibTUIEdge(test_state=test_state)
    stop_event = threading.Event()

    mari.latency_test_enable()

    load_tester = LoadTester(mari, test_state, stop_event)
    if load > 0:
        load_tester.start()

    try:
        normal_traffic_interval = 0.5
        last_normal_send_time = 0

        while not stop_event.is_set():
            current_time = time.monotonic()

            mari.update()

            with mari.lock:
                tui.render(mari)

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
        mari.logger.close()


if __name__ == "__main__":
    main()
