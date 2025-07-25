import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum

from marilib.mari_protocol import Frame
from marilib.protocol import Packet, PacketFieldMetadata

SCHEDULES = {
    # schedule_id: {name, max_nodes, d_down, sf_duration_ms}
    0: {"name": "huge", "max_nodes": 101, "d_down": 22, "sf_duration": 223.31},
    1: {"name": "big", "max_nodes": 74, "d_down": 16, "sf_duration": 164.63},
    2: {"name": "medium", "max_nodes": 49, "d_down": 10, "sf_duration": 109.21},
    3: {"name": "small", "max_nodes": 29, "d_down": 6, "sf_duration": 66.83},
    4: {"name": "tiny", "max_nodes": 11, "d_down": 2, "sf_duration": 27.71},
}


@dataclass
class TestState:
    schedule_id: int | None = None
    schedule_name: str | None = None
    rate: int = 0
    load: int = 0


class EdgeEvent(IntEnum):
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
class LatencyStats:
    latencies: deque = field(default_factory=lambda: deque(maxlen=50))

    def add_latency(self, rtt_seconds: float):
        self.latencies.append(rtt_seconds * 1000)

    @property
    def last_ms(self) -> float:
        return self.latencies[-1] if self.latencies else 0.0

    @property
    def avg_ms(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies) if self.latencies else 0.0


@dataclass
class FrameStats:
    sent: list[FrameLogEntry] = field(default_factory=list)
    received: list[FrameLogEntry] = field(default_factory=list)

    def sent_count(self, window_secs: int = 0) -> int:
        if window_secs == 0:
            return len(self.sent)
        n = datetime.now()
        return len([e for e in self.sent if n - e.ts < timedelta(seconds=window_secs)])

    def received_count(self, window_secs: int = 0) -> int:
        if window_secs == 0:
            return len(self.received)
        n = datetime.now()
        return len(
            [e for e in self.received if n - e.ts < timedelta(seconds=window_secs)]
        )

    def success_rate(self, window_secs: int = 0) -> float:
        s = self.sent_count(window_secs)
        if s == 0:
            return 1.0
        return min(self.received_count(window_secs) / s, 1.0)

    def received_rssi_dbm(self, window_secs: int = 0) -> float:
        if not self.received:
            return 0
        if window_secs == 0:
            return int(self.received[-1].frame.stats.rssi_dbm)
        n = datetime.now()
        d = [
            e.frame.stats.rssi_dbm
            for e in self.received
            if n - e.ts < timedelta(seconds=window_secs)
        ]
        return int(sum(d) / len(d) if d else 0)


@dataclass
class MariNode:
    address: int
    last_seen: datetime = field(default_factory=lambda: datetime.now())
    stats: FrameStats = field(default_factory=FrameStats)
    latency_stats: LatencyStats = field(default_factory=LatencyStats)

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    def register_received_frame(self, frame: Frame):
        self.stats.received.append(FrameLogEntry(frame=frame))

    def register_sent_frame(self, frame: Frame):
        self.stats.sent.append(FrameLogEntry(frame=frame))


@dataclass
class GatewayInfo(Packet):
    metadata: list[PacketFieldMetadata] = field(
        default_factory=lambda: [
            PacketFieldMetadata(name="address", length=8),
            PacketFieldMetadata(name="network_id", length=2),
            PacketFieldMetadata(name="schedule_id", length=1),
        ]
    )
    address: int = 0
    network_id: int = 0
    schedule_id: int = 0


@dataclass
class MariGateway:
    info: GatewayInfo = field(default_factory=GatewayInfo)
    nodes: list[MariNode] = field(default_factory=list)
    stats: FrameStats = field(default_factory=FrameStats)
    latency_stats: LatencyStats = field(default_factory=LatencyStats)

    def update(self):
        self.nodes = [n for n in self.nodes if n.is_alive]

    def set_info(self, info: GatewayInfo):
        self.info = info

    def get_node(self, a: int) -> MariNode | None:
        return next((n for n in self.nodes if n.address == a), None)

    def add_node(self, a: int) -> MariNode:
        if node := self.get_node(a):
            node.last_seen = datetime.now()
            return node
        node = MariNode(a)
        self.nodes.append(node)
        return node

    def remove_node(self, a: int) -> MariNode | None:
        if n := self.get_node(a):
            self.nodes.remove(n)
        return n

    def update_node_liveness(self, a: int):
        if n := self.get_node(a):
            n.last_seen = datetime.now()

    def register_received_frame(self, frame: Frame):
        if n := self.get_node(frame.header.source):
            n.register_received_frame(frame)
            self.stats.received.append(FrameLogEntry(frame=frame))

    def register_sent_frame(self, frame: Frame):
        self.stats.sent.append(FrameLogEntry(frame=frame))
