import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from marilib.latency import LatencyTester
from marilib.mari_protocol import Frame, Header
from marilib.model import (
    EdgeEvent,
    GatewayInfo,
    MariGateway,
    MariNode,
    NodeInfoCloud,
)
from marilib.protocol import ProtocolPayloadParserException
from marilib.communication_adapter import MQTTAdapter

LOAD_PACKET_PAYLOAD = b"L"


@dataclass
class MarilibCloud:
    """
    The MarilibCloud class runs in a computer.
    It is used to communicate with a Mari radio gateway (nRF5340) via MQTT.
    """

    cb_application: Callable[[EdgeEvent, MariNode | Frame | GatewayInfo], None]
    mqtt_interface: MQTTAdapter
    network_id: int

    logger: Any | None = None
    gateways: dict[int, MariGateway] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    latency_tester: LatencyTester | None = None

    started_ts: datetime = field(default_factory=datetime.now)
    last_received_mqtt_data_ts: datetime = field(default_factory=datetime.now)
    main_file: str | None = None

    def __post_init__(self):
        self.setup_params = {
            "main_file": self.main_file or "unknown",
            "mqtt_host": self.mqtt_interface.host,
            "mqtt_port": self.mqtt_interface.port,
            "network_id": self.network_id,
        }
        self.mqtt_interface.set_network_id(self.network_id_str)
        self.mqtt_interface.set_on_data_received(self.on_mqtt_data_received)
        self.mqtt_interface.init()
        if self.logger:
            self.logger.log_setup_parameters(self.setup_params)

    def update(self):
        pass

    def get_max_downlink_rate(self) -> float:
        """Calculate the max downlink packets/sec for a given schedule_id."""
        raise NotImplementedError("Not implemented")

    @property
    def nodes(self) -> list[MariNode]:
        return [node for gateway in self.gateways.values() for node in gateway.nodes]

    @property
    def network_id_str(self) -> str:
        return f"{self.network_id:04X}"

    # def on_mqtt_data_received(self, data: bytes):
    #     """Just forwards the data to the serial interface."""
    #     try:
    #         event_type = EdgeEvent(data[0])
    #         if event_type == EdgeEvent.NODE_DATA:
    #             frame = Frame().from_bytes(data[1:])
    #             # print(f"Forwarding frame of length {len(frame.payload)} to dst = {frame.header.destination:016X}, payload = {frame.payload.hex()}")
    #             # reuse the send_frame function to send the frame to the gateway
    #             self.send_frame(frame.header.destination, frame.payload)
    #         else:
    #             print(f"Received unknown event type: {event_type}")
    #     except (ValueError, ProtocolPayloadParserException) as exc:
    #         print(f"[red]Error parsing frame: {exc}[/]")
    #         return

    def on_mqtt_data_received(self, data: bytes):
        with self.lock:
            if len(data) < 1:
                return
            self.last_received_mqtt_data_ts = datetime.now()
            event_type = data[0]

            if event_type == EdgeEvent.NODE_JOINED:
                # NOTE: the serial protocol still needs to be changed to also send the gateway address
                node_info = NodeInfoCloud().from_bytes(data[1:])
                gateway = self.gateways.get(node_info.gateway_address)
                if gateway:
                    node = gateway.add_node(node_info.address)
                    if self.logger:
                        self.logger.log_event(node.gateway_address, node.address, EdgeEvent.NODE_JOINED.name)
                    self.cb_application(EdgeEvent.NODE_JOINED, (gateway, node))

            elif event_type == EdgeEvent.NODE_LEFT:
                # FIXME: the serial protocol still needs to be changed to also send the gateway address
                node_info = NodeInfoCloud().from_bytes(data[1:])
                gateway = self.gateways.get(node_info.gateway_address)
                if gateway and node_info.address in gateway.nodes_addresses:
                    node = gateway.remove_node(node_info.address)
                    if node and self.logger:
                        self.logger.log_event(node.gateway_address, node.address, EdgeEvent.NODE_LEFT.name)
                    self.cb_application(EdgeEvent.NODE_LEFT, (gateway, node))

            elif event_type == EdgeEvent.NODE_KEEP_ALIVE:
                node_info = NodeInfoCloud().from_bytes(data[1:])
                gateway = self.gateways.get(node_info.gateway_address)
                if gateway:
                    gateway.update_node_liveness(node_info.address)

            elif event_type == EdgeEvent.GATEWAY_INFO:
                try:
                    gateway_info = GatewayInfo().from_bytes(data[1:])
                    gateway = self.gateways.get(gateway_info.address)
                    if not gateway:
                        # TODO: modify and have a timeout-based mechanism to remove the gateway if it disappears
                        gateway = MariGateway(info=gateway_info)
                        self.gateways[gateway.info.address] = gateway
                    else:
                        gateway.set_info(gateway_info)
                    self.cb_application(EdgeEvent.GATEWAY_INFO, gateway_info)
                    if self.logger and self.setup_params:
                        # TODO: update the logging system to support more than one gateway
                        pass
                except (ValueError, ProtocolPayloadParserException):
                    pass

            elif event_type == EdgeEvent.NODE_DATA:
                try:
                    frame = Frame().from_bytes(data[1:])
                    gateway_address = frame.header.destination
                    node_address = frame.header.source
                    gateway = self.gateways.get(gateway_address)
                    if not gateway:
                        return

                    node = gateway.get_node(node_address)
                    if not node:
                        return

                    gateway.update_node_liveness(node_address)
                    self.cb_application(EdgeEvent.NODE_DATA, frame)

                    # NOTE: review stats stuff later
            #         payload = frame.payload
            #         node = self.gateways.get_node(frame.header.source)
            #         is_test_or_stats_packet = False

            #         if payload.startswith(LATENCY_PACKET_MAGIC):
            #             is_test_or_stats_packet = True
            #             if self.latency_tester:
            #                 self.latency_tester.handle_response(frame)

            #         elif len(payload) == 8:
            #             try:
            #                 stats_reply = NodeStatsReply().from_bytes(payload)

            #                 if node:
            #                     if not hasattr(node, "stats_reply_count"):
            #                         node.stats_reply_count = 0
            #                     node.stats_reply_count += 1

            #                     node.last_reported_rx_count = stats_reply.rx_app_packets
            #                     node.last_reported_tx_count = stats_reply.tx_app_packets

            #                     # Calculate PDR Downlink
            #                     if node.stats.cumulative_sent_non_test > 0:
            #                         pdr = (
            #                             node.last_reported_rx_count
            #                             / node.stats.cumulative_sent_non_test
            #                         )
            #                         node.pdr_downlink = min(pdr, 1.0)
            #                     else:
            #                         node.pdr_downlink = 1.0

            #                     # Calculate PDR Uplink
            #                     if node.last_reported_tx_count > 0:
            #                         pdr = (
            #                             node.stats_reply_count
            #                             / node.last_reported_tx_count
            #                         )
            #                         node.pdr_uplink = min(pdr, 1.0)

            #             except (ValueError, ProtocolPayloadParserException):
            #                 pass

            #         self.gateways.register_received_frame(frame, is_test_or_stats_packet)

            #         if not is_test_or_stats_packet:
            #             self.cb_application(EdgeEvent.NODE_DATA, frame)

                except (ValueError, ProtocolPayloadParserException):
                    pass

    def send_frame(self, dst: int, payload: bytes):
        """
        Sends a frame to a gateway via mqtt.
        Consists in publishing a message to the /mari/{network_id}/to_edge topic.
        """
        mari_frame = Frame(Header(destination=dst), payload=payload)

        self.mqtt_interface.send_data_to_edge(EdgeEvent.to_bytes(EdgeEvent.NODE_DATA) + mari_frame.to_bytes())
