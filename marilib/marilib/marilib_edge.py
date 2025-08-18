import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from rich import print

from marilib.latency import LATENCY_PACKET_MAGIC, LatencyTester
from marilib.mari_protocol import MARI_BROADCAST_ADDRESS, Frame, Header
from marilib.model import (
    EdgeEvent,
    GatewayInfo,
    MariGateway,
    MariNode,
    NodeStatsReply,
    SCHEDULES,
)
from marilib.protocol import ProtocolPayloadParserException
from marilib.communication_adapter import MQTTAdapter, SerialAdapter

LOAD_PACKET_PAYLOAD = b"L"


@dataclass
class MarilibEdge:
    """
    The MarilibEdge class runs in either a computer or a raspberry pi.
    It is used to communicate with:
    - a Mari radio gateway (nRF5340) via serial
    - a Mari cloud instance via MQTT (optional)
    """

    cb_application: Callable[[EdgeEvent, MariNode | Frame], None]
    serial_interface: SerialAdapter
    mqtt_interface: MQTTAdapter | None = None

    logger: Any | None = None
    gateway: MariGateway = field(default_factory=MariGateway)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    latency_tester: LatencyTester | None = None

    started_ts: datetime = field(default_factory=datetime.now)
    last_received_serial_data_ts: datetime = field(default_factory=datetime.now)
    main_file: str | None = None

    def __post_init__(self):
        self.setup_params = {
            "main_file": self.main_file or "unknown",
            "serial_port": self.serial_interface.port,
        }
        self.serial_interface.init(self.on_serial_data_received)
        # NOTE: MQTT interface is initialized only when the network_id is known
        if self.logger:
            self.logger.log_setup_parameters(self.setup_params)

    def update(self):
        with self.lock:
            self.gateway.update()
            if self.logger and self.logger.active:
                self.logger.log_periodic_metrics(self.gateway, self.gateway.nodes)

    def get_max_downlink_rate(self) -> float:
        """Calculate the max downlink packets/sec for a given schedule_id."""
        schedule_params = SCHEDULES.get(self.gateway.info.schedule_id)
        if not schedule_params:
            return 0.0
        d_down = schedule_params["d_down"]
        sf_duration_ms = schedule_params["sf_duration"]
        if sf_duration_ms == 0:
            return 0.0
        return d_down / (sf_duration_ms / 1000.0)
    
    def on_mqtt_data_received(self, data: bytes):
        """Just forwards the data to the serial interface."""
        try:
            event_type = EdgeEvent(data[0])
            if event_type == EdgeEvent.NODE_DATA:
                frame = Frame().from_bytes(data[1:])
                # print(f"Forwarding frame of length {len(frame.payload)} to dst = {frame.header.destination:016X}, payload = {frame.payload.hex()}")
                # reuse the send_frame function to send the frame to the gateway
                self.send_frame(frame.header.destination, frame.payload)
            else:
                print(f"Received unknown event type: {event_type}")
        except (ValueError, ProtocolPayloadParserException) as exc:
            print(f"[red]Error parsing frame: {exc}[/]")
            return

    @property
    def serial_connected(self) -> bool:
        return self.serial_interface is not None

    def on_serial_data_received(self, data: bytes):
        with self.lock:
            if len(data) < 1:
                return
            self.last_received_serial_data_ts = datetime.now()
            event_type = data[0]

            if event_type == EdgeEvent.NODE_JOINED:
                node = self.gateway.add_node(int.from_bytes(data[1:9], "little"))
                if self.logger:
                    self.logger.log_event(node.address, EdgeEvent.NODE_JOINED.name)
                self.cb_application(EdgeEvent.NODE_JOINED, node)
            elif event_type == EdgeEvent.NODE_LEFT:
                if n := self.gateway.remove_node(int.from_bytes(data[1:9], "little")):
                    if self.logger:
                        self.logger.log_event(n.address, EdgeEvent.NODE_LEFT.name)
                    self.cb_application(EdgeEvent.NODE_LEFT, n)
            elif event_type == EdgeEvent.NODE_KEEP_ALIVE:
                self.gateway.update_node_liveness(int.from_bytes(data[1:9], "little"))
            elif event_type == EdgeEvent.GATEWAY_INFO:
                try:
                    self.gateway.set_info(GatewayInfo().from_bytes(data[1:]))
                    if self.mqtt_interface:
                        self.mqtt_interface.init(self.gateway.info.network_id_str, self.on_mqtt_data_received, is_edge=True)
                    self.cb_application(EdgeEvent.GATEWAY_INFO, self.gateway.info)
                    if self.logger and self.setup_params:
                        self.setup_params["schedule_name"] = (
                            self.gateway.info.schedule_name
                        )
                        self.setup_params["schedule_id"] = self.gateway.info.schedule_id
                        self.logger.log_setup_parameters(self.setup_params)
                except (ValueError, ProtocolPayloadParserException):
                    pass
            elif event_type == EdgeEvent.NODE_DATA:
                try:
                    frame = Frame().from_bytes(data[1:])
                    self.gateway.update_node_liveness(frame.header.source)
                    payload = frame.payload
                    node = self.gateway.get_node(frame.header.source)
                    is_test_or_stats_packet = False

                    if payload.startswith(LATENCY_PACKET_MAGIC):
                        is_test_or_stats_packet = True
                        if self.latency_tester:
                            self.latency_tester.handle_response(frame)

                    elif len(payload) == 8:
                        try:
                            stats_reply = NodeStatsReply().from_bytes(payload)

                            if node:
                                if not hasattr(node, "stats_reply_count"):
                                    node.stats_reply_count = 0
                                node.stats_reply_count += 1

                                node.last_reported_rx_count = stats_reply.rx_app_packets
                                node.last_reported_tx_count = stats_reply.tx_app_packets

                                # Calculate PDR Downlink
                                if node.stats.cumulative_sent_non_test > 0:
                                    pdr = (
                                        node.last_reported_rx_count
                                        / node.stats.cumulative_sent_non_test
                                    )
                                    node.pdr_downlink = min(pdr, 1.0)
                                else:
                                    node.pdr_downlink = 1.0

                                # Calculate PDR Uplink
                                if node.last_reported_tx_count > 0:
                                    pdr = (
                                        node.stats_reply_count
                                        / node.last_reported_tx_count
                                    )
                                    node.pdr_uplink = min(pdr, 1.0)

                        except (ValueError, ProtocolPayloadParserException):
                            pass

                    self.gateway.register_received_frame(frame, is_test_or_stats_packet)

                    if not is_test_or_stats_packet:
                        self.cb_application(EdgeEvent.NODE_DATA, frame)

                except (ValueError, ProtocolPayloadParserException):
                    pass

    def send_frame(self, dst: int, payload: bytes):
        """Sends a frame to the gateway via serial."""
        assert self.serial_interface is not None

        mari_frame = Frame(Header(destination=dst), payload=payload)
        is_test = self._is_test_packet(payload)

        with self.lock:
            # Only register statistics for normal data packets, not for test packets.
            self.gateway.register_sent_frame(mari_frame, is_test)
            if dst == MARI_BROADCAST_ADDRESS:
                for n in self.gateway.nodes:
                    n.register_sent_frame(mari_frame, is_test)
            elif n := self.gateway.get_node(dst):
                n.register_sent_frame(mari_frame, is_test)

        # FIXME: instead of prefixing with a magic 0x01 byte, we should use EdgeEvent.NODE_DATA
        self.serial_interface.send_data(b"\x01" + mari_frame.to_bytes())

    def latency_test_enable(self):
        if self.latency_tester is None:
            self.latency_tester = LatencyTester(self)
            self.latency_tester.start()

    def latency_test_disable(self):
        if self.latency_tester is not None:
            self.latency_tester.stop()
            self.latency_tester = None

    def _is_test_packet(self, payload: bytes) -> bool:
        """Determines if a packet is for testing purposes (load or latency)."""
        is_latency = payload.startswith(LATENCY_PACKET_MAGIC)
        is_load = payload == LOAD_PACKET_PAYLOAD
        return is_latency or is_load
