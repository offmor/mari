from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta


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
class NetworkId:
    value: bytes = field(default_factory=lambda: b'\x00' * 2)

    def __repr__(self):
        return '0x' + ''.join([f'{b:02X}' for b in reversed(self.value)])


@dataclass
class FrameStats:
    sent: int = 0
    received: int = 0


@dataclass
class MiraNode:
    address: NodeAddress
    last_seen: datetime
    stats: FrameStats = field(default_factory=FrameStats)

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    @property
    def address_int(self) -> int:
        return self.address.value_int

    def __repr__(self):
        return f"MiraNode(address={self.address}, last_seen={self.last_seen})"

@dataclass
class MiraGateway:
    address: NodeAddress = field(default_factory=lambda: NodeAddress(b'\x00' * 8))
    network_id: NetworkId = field(default_factory=lambda: NetworkId(b'\x00' * 2))
    schedule_id: int = 0
    nodes: list[MiraNode] = field(default_factory=list)

    def __repr__(self):
        return f"MiraGateway(address={self.address}, network_id={self.network_id}, schedule_id={self.schedule_id}), number of nodes: {len(self.nodes)}"

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
