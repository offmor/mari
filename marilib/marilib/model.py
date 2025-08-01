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
class NodeStatsReply(Packet):
    """Dataclass representing the statistics packet sent back by a node."""

    metadata: list[PacketFieldMetadata] = field(
        default_factory=lambda: [
            PacketFieldMetadata(name="rx_app_packets", length=4),
            PacketFieldMetadata(name="tx_app_packets", length=4),
        ]
    )
    rx_app_packets: int = 0
    tx_app_packets: int = 0


@dataclass
class FrameLogEntry:
    frame: Frame
    ts: datetime = field(default_factory=lambda: datetime.now())
    is_test_packet: bool = False


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
    window_seconds: int = 240  # set window duration
    sent: deque[FrameLogEntry] = field(default_factory=deque)
    received: deque[FrameLogEntry] = field(default_factory=deque)
    cumulative_sent: int = 0
    cumulative_received: int = 0
    cumulative_sent_non_test: int = 0
    cumulative_received_non_test: int = 0

    def add_sent(self, frame: Frame, is_test_packet: bool):
        """Adds a sent frame, prunes old entries, and updates counters."""
        self.cumulative_sent += 1

        if not is_test_packet:
            self.cumulative_sent_non_test += 1

            entry = FrameLogEntry(frame=frame, is_test_packet=is_test_packet)
            self.sent.append(entry)
            while (
                self.sent
                and (entry.ts - self.sent[0].ts).total_seconds() > self.window_seconds
            ):
                self.sent.popleft()

    def add_received(self, frame: Frame, is_test_packet: bool):
        """Adds a received frame and prunes old entries."""
        self.cumulative_received += 1

        if not is_test_packet:
            self.cumulative_received_non_test += 1
            entry = FrameLogEntry(frame=frame, is_test_packet=is_test_packet)
            self.received.append(entry)
            while (
                self.received
                and (entry.ts - self.received[0].ts).total_seconds()
                > self.window_seconds
            ):
                self.received.popleft()

    def sent_count(
        self, window_secs: int = 0, include_test_packets: bool = True
    ) -> int:
        if window_secs == 0:
            return (
                self.cumulative_sent
                if include_test_packets
                else self.cumulative_sent_non_test
            )

        now = datetime.now()
        # Windowed count is always for non-test packets.
        entries = [e for e in self.sent if now - e.ts < timedelta(seconds=window_secs)]
        return len(entries)

    def received_count(
        self, window_secs: int = 0, include_test_packets: bool = True
    ) -> int:
        if window_secs == 0:
            return (
                self.cumulative_received
                if include_test_packets
                else self.cumulative_received_non_test
            )

        now = datetime.now()
        entries = [
            e for e in self.received if now - e.ts < timedelta(seconds=window_secs)
        ]
        return len(entries)

    def success_rate(self, window_secs: int = 0) -> float:
        s = self.sent_count(window_secs, include_test_packets=False)
        if s == 0:
            return 1.0
        r = self.received_count(window_secs, include_test_packets=False)
        return min(r / s, 1.0)

    def received_rssi_dbm(self, window_secs: int = 0) -> float:
        if not self.received:
            return 0

        if window_secs == 0:
            return int(self.received[-1].frame.stats.rssi_dbm) if self.received else 0
        n = datetime.now()
        d = [
            e.frame.stats.rssi_dbm
            for e in self.received
            if (n - e.ts < timedelta(seconds=window_secs))
        ]
        return int(sum(d) / len(d) if d else 0)


@dataclass
class MariNode:
    address: int
    last_seen: datetime = field(default_factory=lambda: datetime.now())
    stats: FrameStats = field(default_factory=FrameStats)
    latency_stats: LatencyStats = field(default_factory=LatencyStats)
    last_reported_rx_count: int = 0
    last_reported_tx_count: int = 0
    pdr_downlink: float = 0.0
    pdr_uplink: float = 0.0

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    def register_received_frame(self, frame: Frame, is_test_packet: bool):
        self.stats.add_received(frame, is_test_packet)

    def register_sent_frame(self, frame: Frame, is_test_packet: bool):
        self.stats.add_sent(frame, is_test_packet)


@dataclass
class GatewayInfo(Packet):
    metadata: list[PacketFieldMetadata] = field(
        default_factory=lambda: [
            PacketFieldMetadata(name="address", length=8),
            PacketFieldMetadata(name="network_id", length=2),
            PacketFieldMetadata(name="schedule_id", length=1),
            PacketFieldMetadata(name="schedule_stats", length=4*8), # 4 uint64_t values
        ]
    )
    address: int = 0
    network_id: int = 0
    schedule_id: int = 0
    schedule_stats: bytes = b""

    def repr_schedule_stats(self):
        if not self.schedule_stats:
            return ""
        all_bits = format(self.schedule_stats, f'0{4*8*8}b')
        all_bits = [all_bits[i:i+8] for i in range(0, len(all_bits), 8)]
        all_bits.reverse()
        # print(">>>", reversed(all_bits[0].split("")))
        all_bits = [list(reversed(bits)) for bits in all_bits]
        # now just flatten the list
        all_bits = [item for sublist in all_bits for item in sublist]
        # cut it down to 137 bits
        all_bits = all_bits[8:145]
        return "".join(all_bits)

    @property
    def schedule_name(self) -> str:
        schedule_data = SCHEDULES.get(self.schedule_id)
        return schedule_data["name"] if schedule_data else "unknown"


@dataclass
class MariGateway:
    info: GatewayInfo = field(default_factory=GatewayInfo)
    node_registry: dict[int, MariNode] = field(default_factory=dict)
    stats: FrameStats = field(default_factory=FrameStats)
    latency_stats: LatencyStats = field(default_factory=LatencyStats)

    @property
    def nodes(self) -> list[MariNode]:
        return list(self.node_registry.values())

    def update(self):
        self.node_registry = {
            addr: node for addr, node in self.node_registry.items() if node.is_alive
        }

    def set_info(self, info: GatewayInfo):
        self.info = info

    def get_node(self, a: int) -> MariNode | None:
        return self.node_registry.get(a)

    def add_node(self, a: int) -> MariNode:
        if node := self.get_node(a):
            node.last_seen = datetime.now()
            return node
        node = MariNode(a)
        self.node_registry[a] = node
        return node

    def remove_node(self, a: int) -> MariNode | None:
        return self.node_registry.pop(a, None)

    def update_node_liveness(self, addr: int):
        node = self.get_node(addr)
        if node:
            node.last_seen = datetime.now()
        else:
            self.add_node(addr)

    def register_received_frame(self, frame: Frame, is_test_packet: bool):
        if n := self.get_node(frame.header.source):
            n.register_received_frame(frame, is_test_packet)
        self.stats.add_received(frame, is_test_packet)

    def register_sent_frame(self, frame: Frame, is_test_packet: bool):
        self.stats.add_sent(frame, is_test_packet)
