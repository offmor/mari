from typing import Callable
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from mira_edge.model import EdgeEvent, MiraGateway, MiraNode, NodeAddress
from mira_edge.protocol import Frame, Header, ProtocolPayloadParserException
from mira_edge.serial_adapter import SerialAdapter
from mira_edge.serial_interface import SerialInterfaceException, get_default_port
import serial


@dataclass
class MiraEdge:
    on_event: Callable[[EdgeEvent, MiraNode | Frame], None] = field(default_factory=lambda: lambda *args: None)
    port: str | None = None
    baudrate: int = 1_000_000
    gateway: MiraGateway = field(default_factory=MiraGateway)
    serial_interface: SerialAdapter | None = None

    def __post_init__(self):
        try:
            if self.port is None:
                self.port = get_default_port()
            self.serial_interface = SerialAdapter(
                self.port, self.baudrate
            )
        except (
            SerialInterfaceException,
            serial.SerialException,
        ) as exc:
            print(f"Error: {exc}")

    def on_data_received(self, data: bytes):
        if len(data) < 1:
            return

        event_type = data[0]

        if event_type == EdgeEvent.NODE_JOINED:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_JOINED.name} {address}")
            node = self.gateway.add_node(address)
            self.on_event(EdgeEvent.NODE_JOINED, node)

        elif event_type == EdgeEvent.NODE_LEFT:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_LEFT.name} {address}")
            if node := self.gateway.remove_node(address):
                self.on_event(EdgeEvent.NODE_LEFT, node)

        elif event_type == EdgeEvent.NODE_KEEP_ALIVE:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_KEEP_ALIVE.name} {address}")
            self.gateway.add_node(address)

        elif event_type == EdgeEvent.NODE_DATA:
            try:
                frame_bytes = data[1:]
                frame = Frame().from_bytes(frame_bytes)
                # print(f"Event: {EdgeEvent.NODE_DATA.name} {frame.header} {frame.payload.hex()}")
                source_address = NodeAddress.from_int(frame.header.source)
                self.gateway.keep_node_alive(source_address)
                self.on_event(EdgeEvent.NODE_DATA, frame)
            except (ValueError, ProtocolPayloadParserException) as exc:
                print(f"Failed to decode frame: {exc}")

        else:
            # print(f"Unknown event: {event_type} -- {data}")
            print("?", end="", flush=True)

    def connect_to_gateway(self):
        assert self.serial_interface is not None
        self.serial_interface.init(self.on_data_received)

    def disconnect_from_gateway(self):
        assert self.serial_interface is not None
        self.serial_interface.close()

    def send_frame(self, dst: int, payload: bytes):
        assert self.serial_interface is not None
        self.serial_interface.send_data(Frame(Header(destination=dst), payload=payload).to_bytes())
