from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum

from mira_edge.mira_protocol import FrameStats, GatewayInfo, MiraNode


class EdgeEvent(IntEnum):
    """Types of UART packet."""

    NODE_JOINED = 1
    NODE_LEFT = 2
    NODE_DATA = 3
    NODE_KEEP_ALIVE = 4
    GATEWAY_INFO = 5


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

    def add_node(self, address: int) -> MiraNode:
        node = next(
            (node for node in self.nodes if node.address == address), None
        )
        if node:
            node.last_seen = datetime.now()
        else:
            node = MiraNode(address)
            self.nodes.append(node)
        return node

    def remove_node(self, address: int) -> MiraNode | None:
        node = next(
            (node for node in self.nodes if node.address == address), None
        )
        if node:
            self.nodes.remove(node)
            return node
        return None

    def register_received_frame(self, address: int):
        node = next(
            (node for node in self.nodes if node.address == address), None
        )
        if node:
            node.last_seen = datetime.now()
            node.stats.received += 1
            self.stats.received += 1

    def register_sent_frame(self):
        self.stats.sent += 1
