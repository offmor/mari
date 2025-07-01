from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum

from mira_edge.mira_protocol import Frame
from mira_edge.protocol import Packet, PacketFieldMetadata


class EdgeEvent(IntEnum):
    """Types of UART packet."""

    NODE_JOINED = 1
    NODE_LEFT = 2
    NODE_DATA = 3
    NODE_KEEP_ALIVE = 4
    GATEWAY_INFO = 5


@dataclass
class FrameLog:
    ts: datetime
    frame: Frame


@dataclass
class FrameStats:
    sent: int = 0
    received: int = 0

    @property
    def success_rate(self) -> float:
        if self.received == 0:
            return 0
        return self.received / self.sent


@dataclass
class MiraNode:
    address: int
    last_seen: datetime = field(default_factory=lambda: datetime.now())
    stats: FrameStats = field(default_factory=FrameStats)

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    @property
    def address_bytes(self) -> bytes:
        return self.address.to_bytes(8, "little")

    def register_received_frame(self):
        self.stats.received += 1

    def register_sent_frame(self):
        self.stats.sent += 1

    def __repr__(self):
        return f"MiraNode(address=0x{self.address_bytes.hex()}, last_seen={self.last_seen})"


@dataclass
class GatewayInfo(Packet):
    metadata: list[PacketFieldMetadata] = field(
        default_factory=lambda: [
            PacketFieldMetadata(name="address", disp="addr", length=8),
            PacketFieldMetadata(name="network_id", disp="net", length=2),
            PacketFieldMetadata(name="schedule_id", disp="sch", length=1),
        ]
    )

    address: int = 0
    network_id: int = 0
    schedule_id: int = 0


@dataclass
class MiraGateway:
    info: GatewayInfo = field(default_factory=GatewayInfo)
    nodes: list[MiraNode] = field(default_factory=list)
    stats: FrameStats = field(default_factory=FrameStats)

    def __repr__(self):
        return (
            f"MiraGateway(info={self.info}, number of nodes: {len(self.nodes)}"
        )

    def set_info(self, info: GatewayInfo):
        self.info = info

    def get_node(self, address: int) -> MiraNode | None:
        return next(
            (node for node in self.nodes if node.address == address), None
        )

    def add_node(self, address: int) -> MiraNode:
        node = self.get_node(address)
        if node:
            node.last_seen = datetime.now()
        else:
            node = MiraNode(address)
            self.nodes.append(node)
        return node

    def remove_node(self, address: int) -> MiraNode | None:
        node = self.get_node(address)
        if node:
            self.nodes.remove(node)
            return node
        return None

    def register_received_frame(self, address: int):
        node = self.get_node(address)
        if node:
            node.last_seen = datetime.now()
            node.register_received_frame()
            self.stats.received += 1

    def register_sent_frame(self):
        self.stats.sent += 1
