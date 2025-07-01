import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from mira_edge.protocol import Packet, PacketFieldMetadata, PacketType

MIRA_PROTOCOL_VERSION = 2
MIRA_BROADCAST_ADDRESS = 0xFFFFFFFFFFFFFFFF
MIRA_NET_ID_DEFAULT = 0x0001


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
class Header(Packet):
    """Dataclass that holds MAC header fields."""

    metadata: list[PacketFieldMetadata] = dataclasses.field(
        default_factory=lambda: [
            PacketFieldMetadata(name="version", disp="ver.", length=1),
            PacketFieldMetadata(name="type_", disp="type", length=1),
            PacketFieldMetadata(name="network_id", disp="net", length=2),
            PacketFieldMetadata(name="destination", disp="dst", length=8),
            PacketFieldMetadata(name="source", disp="src", length=8),
        ]
    )
    version: int = MIRA_PROTOCOL_VERSION
    type_: int = PacketType.DATA
    network_id: int = MIRA_NET_ID_DEFAULT
    destination: int = MIRA_BROADCAST_ADDRESS
    source: int = 0x0000000000000000

    def __repr__(self):
        type_ = PacketType(self.type_).name
        return f"Header(version={self.version}, type_={type_}, network_id=0x{self.network_id:04x}, destination=0x{self.destination:016x}, source=0x{self.source:016x})"


@dataclass
class Frame:
    """Data class that holds a payload packet."""

    header: Header = None
    payload: bytes = b""

    def from_bytes(self, bytes_):
        self.header = Header().from_bytes(bytes_[0:20])
        if len(bytes_) > 20:
            self.payload = bytes_[20:]
        return self

    def to_bytes(self, byteorder="little") -> bytes:
        header_bytes = self.header.to_bytes(byteorder)
        return header_bytes + self.payload

    def __repr__(self):
        header_no_metadata = dataclasses.replace(self.header, metadata=[])
        return f"Frame(header={header_no_metadata}, payload={self.payload})"
