from typing import Callable
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from mira_edge.protocol import Frame, Header, ProtocolPayloadParserException
from mira_edge.serial_adapter import SerialAdapter
from mira_edge.serial_interface import SerialInterfaceException, get_default_port
import serial


class EdgeEvent(IntEnum):
    """Types of UART packet."""
    NODE_JOINED = 1
    NODE_LEFT = 2
    NODE_DATA = 3
    NODE_KEEP_ALIVE = 4


@dataclass
class NodeAddress:
    value: bytes = field(default_factory=lambda: b'\x00' * 8)

    @property
    def value_int(self) -> int:
        return int.from_bytes(self.value, "little")

    @staticmethod
    def from_int(address_int: int) -> "NodeAddress":
        return NodeAddress(address_int.to_bytes(length=8, byteorder="little"))

    def __repr__(self):
        return '0x' + ''.join([f'{b:02X}' for b in reversed(self.value)])


@dataclass
class MiraNode:
    address: NodeAddress
    last_seen: datetime

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    @property
    def address_int(self) -> int:
        return self.address.value_int

    def __repr__(self):
        return f"MiraNode(address={self.address}, last_seen={self.last_seen})"


class MiraEdge:
    def __init__(self, on_event: Callable[[EdgeEvent, MiraNode | Frame], None], port: str | None = None, baudrate: int = 1_000_000):
        self.on_event = on_event
        self.nodes: list[MiraNode] = []
        try:
            if port is None:
                port = get_default_port()
            self._interface = SerialAdapter(
                port, baudrate
            )
        except (
            SerialInterfaceException,
            serial.SerialException,
        ) as exc:
            print(f"Error: {exc}")

    def on_data_received(self, data: bytes):
        event_type = data[0]

        if event_type == EdgeEvent.NODE_JOINED:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_JOINED.name} {address}")
            node = self.add_node(address)
            self.on_event(EdgeEvent.NODE_JOINED, node)

        elif event_type == EdgeEvent.NODE_LEFT:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_LEFT.name} {address}")
            if node := self.remove_node(address):
                self.on_event(EdgeEvent.NODE_LEFT, node)

        elif event_type == EdgeEvent.NODE_KEEP_ALIVE:
            address = NodeAddress(data[1:9])
            # print(f"Event: {EdgeEvent.NODE_KEEP_ALIVE.name} {address}")
            self.add_node(address)

        elif event_type == EdgeEvent.NODE_DATA:
            try:
                frame_bytes = data[1:]
                frame = Frame().from_bytes(frame_bytes)
                # print(f"Event: {EdgeEvent.NODE_DATA.name} {frame.header} {frame.payload.hex()}")
                source_address = NodeAddress.from_int(frame.header.source)
                self.keep_node_alive(source_address)
                self.on_event(EdgeEvent.NODE_DATA, frame)
            except (ValueError, ProtocolPayloadParserException) as exc:
                print(f"Failed to decode frame: {exc}")

        else:
            print(f"Unknown event: {event_type} -- {data}")

    def add_node(self, address: NodeAddress) -> MiraNode:
        node = next((node for node in self.nodes if node.address == address), None)
        if node:
            node.last_seen = datetime.now()
        else:
            node = MiraNode(address, datetime.now())
            self.nodes.append(node)
        return node

    def remove_node(self, address: NodeAddress) -> MiraNode | None:
        node = next((node for node in self.nodes if node.address == address), None)
        if node:
            self.nodes.remove(node)
            return node
        return None

    def keep_node_alive(self, address: NodeAddress):
        node = next((node for node in self.nodes if node.address == address), None)
        if node:
            node.last_seen = datetime.now()

    def connect_to_gateway(self):
        self._interface.init(self.on_data_received)

    def disconnect_from_gateway(self):
        self._interface.close()

    def send_frame(self, dst: int, payload: bytes):
        self._interface.send_data(Frame(Header(destination=dst), payload=payload).to_bytes())
