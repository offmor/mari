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
class FrameLogEntry:
    frame: Frame
    ts: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class FrameStats:
    sent: list[FrameLogEntry] = field(default_factory=list)
    received: list[FrameLogEntry] = field(default_factory=list)

    def sent_count(self, window_secs: int = 0) -> int:
        if window_secs == 0:
            return len(self.sent)
        else:
            # return the number of sent frames in the last window_secs seconds
            now = datetime.now()
            return len(
                [
                    entry
                    for entry in self.sent
                    if now - entry.ts < timedelta(seconds=window_secs)
                ]
            )

    def received_count(self, window_secs: int = 0) -> int:
        if window_secs == 0:
            return len(self.received)
        else:
            # return the number of received frames in the last window_secs seconds
            now = datetime.now()
            return len(
                [
                    entry
                    for entry in self.received
                    if now - entry.ts < timedelta(seconds=window_secs)
                ]
            )

    def success_rate(self, window_secs: int = 0) -> float:
        if self.sent_count() == 0:
            return 0
        rate = None
        if window_secs == 0:
            rate = self.received_count() / self.sent_count()
        else:
            rate = self.received_count(window_secs) / self.sent_count(window_secs)
        # this is a hack, because of the way we count, sometimes
        # received_count is greater than sent_count so we cap the rate at 1
        return min(rate, 1)


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

    def register_received_frame(self, frame: Frame):
        self.stats.received.append(FrameLogEntry(frame=frame))

    def register_sent_frame(self, frame: Frame):
        self.stats.sent.append(FrameLogEntry(frame=frame))

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
        return f"MiraGateway(info={self.info}, number of nodes: {len(self.nodes)}"

    def set_info(self, info: GatewayInfo):
        self.info = info

    def get_node(self, address: int) -> MiraNode | None:
        return next((node for node in self.nodes if node.address == address), None)

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

    def register_received_frame(self, frame: Frame):
        node = self.get_node(frame.header.source)
        if node:
            node.last_seen = datetime.now()
            node.register_received_frame(frame)
            self.stats.received.append(FrameLogEntry(frame=frame))

    def register_sent_frame(self, frame: Frame):
        self.stats.sent.append(FrameLogEntry(frame=frame))
